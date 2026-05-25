import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.connector_acceptance import (
    classify_acceptance_score,
    classify_reconciliation_slo,
)
from lima_office.runtime.errors import PolicyDenyError


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_connector_acceptance", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ConnectorProviderAcceptanceScoringTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def test_connector_acceptance_score_examples_validate(self):
        self.validator.validate(
            example("connector.acceptance_score.email-approved-for-lab.example.json"),
            "connector.acceptance_score",
        )
        self.validator.validate(
            example("connector.acceptance_score.provider-critical-review-required.example.json"),
            "connector.acceptance_score",
        )
        self.validator.validate(
            example("connector.acceptance_score.revoked.example.json"),
            "connector.acceptance_score",
        )
        self.validator.validate(
            example("connector.acceptance_score.failed-closed.example.json"),
            "connector.acceptance_score",
        )

    def test_reconciliation_slo_examples_validate(self):
        self.validator.validate(
            example("connector.reconciliation_slo.current.example.json"),
            "connector.reconciliation_slo",
        )
        self.validator.validate(
            example("connector.reconciliation_slo.revocation-pending.example.json"),
            "connector.reconciliation_slo",
        )
        self.validator.validate(
            example("connector.reconciliation_slo.missed-failed-closed.example.json"),
            "connector.reconciliation_slo",
        )
        self.validator.validate(
            example("console.alert.connector-score-degraded.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.connector-slo-missed.example.json"),
            "supervisor.health",
        )

    def test_approved_for_lab_requires_evidence_and_no_failed_dimensions(self):
        payload = copy.deepcopy(example("connector.acceptance_score.email-approved-for-lab.example.json"))
        payload["failed_dimensions"] = ["scope_least_privilege"]
        result = classify_acceptance_score(payload)
        self.assertTrue(result["fail_closed"])
        self.assertNotEqual("approved_for_lab", result["score_status"])
        self.assertFalse(result["can_authorize"])

    def test_critical_provider_risk_requires_review_and_evidence(self):
        payload = copy.deepcopy(
            example("connector.acceptance_score.provider-critical-review-required.example.json")
        )
        provider = copy.deepcopy(example("connector.provider_profile.rmm-it-critical-review-required.example.json"))
        provider["provider_status"] = "profiled"
        provider["evidence_refs"] = []
        result = classify_acceptance_score(payload, provider_profile=provider)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_provider_critical_risk", result["reason_codes"])

    def test_revoked_score_requires_reason_and_evidence(self):
        payload = copy.deepcopy(example("connector.acceptance_score.revoked.example.json"))
        payload["reason_codes"] = []
        payload["evidence_refs"] = []
        result = classify_acceptance_score(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_score_failed_closed", result["reason_codes"])

    def test_failed_closed_requires_failed_dimensions_reasons_evidence(self):
        payload = copy.deepcopy(example("connector.acceptance_score.failed-closed.example.json"))
        payload["failed_dimensions"] = []
        payload["reason_codes"] = []
        payload["evidence_refs"] = []
        result = classify_acceptance_score(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_score_failed_closed", result["reason_codes"])

    def test_pending_or_missed_revocation_blocks_approved_for_lab(self):
        payload = copy.deepcopy(example("connector.acceptance_score.email-approved-for-lab.example.json"))
        slo = copy.deepcopy(example("connector.reconciliation_slo.revocation-pending.example.json"))
        result = classify_acceptance_score(payload, reconciliation_slo=slo)
        self.assertTrue(result["fail_closed"])
        self.assertNotEqual("approved_for_lab", result["score_status"])
        self.assertIn("connector_revocation_propagation_pending", result["reason_codes"])

    def test_stale_or_missed_slo_requires_reason_and_evidence(self):
        slo = copy.deepcopy(example("connector.reconciliation_slo.missed-failed-closed.example.json"))
        slo["reason_codes"] = []
        slo["evidence_refs"] = []
        result = classify_reconciliation_slo(slo)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_source_of_truth_missing", result["reason_codes"])

    def test_score_cannot_authorize_real_connector_use(self):
        payload = copy.deepcopy(example("connector.acceptance_score.email-approved-for-lab.example.json"))
        result = classify_acceptance_score(payload)
        self.assertFalse(result["can_authorize"])

    def test_helper_never_stores_reads_secrets_or_calls_external_apis(self):
        source = (ROOT / "lima_office" / "runtime" / "connector_acceptance.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("requests.", "httpx.", "socket.", "urllib.", "subprocess.", "oauth.")
        for token in banned_tokens:
            self.assertNotIn(token, source)

    def test_reason_code_gate_passes_new_score_slo_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)

    def test_unknown_taxonomy_version_fails_closed(self):
        payload = copy.deepcopy(example("connector.acceptance_score.email-approved-for-lab.example.json"))
        payload["taxonomy_version"] = "taxonomy-reason-v999"
        with self.assertRaises(PolicyDenyError):
            classify_acceptance_score(payload)


if __name__ == "__main__":
    unittest.main()
