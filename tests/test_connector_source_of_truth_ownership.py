import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.connector_ownership import (
    classify_connector_escalation,
    classify_connector_ownership,
)


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_connector_ownership", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ConnectorSourceOfTruthOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def test_connector_ownership_examples_validate(self):
        self.validator.validate(
            example("connector.ownership.active.example.json"),
            "connector.ownership",
        )
        self.validator.validate(
            example("connector.ownership.stale-failed-closed.example.json"),
            "connector.ownership",
        )
        self.validator.validate(
            example("connector.ownership.sod-violation.example.json"),
            "connector.ownership",
        )

    def test_connector_escalation_examples_validate(self):
        self.validator.validate(
            example("connector.escalation.stale-owner-opened.example.json"),
            "connector.escalation",
        )
        self.validator.validate(
            example("connector.escalation.revocation-overdue-failed-closed.example.json"),
            "connector.escalation",
        )
        self.validator.validate(
            example("connector.escalation.resolved-placeholder.example.json"),
            "connector.escalation",
        )
        self.validator.validate(
            example("console.alert.connector-owner-stale.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.connector-ownership-degraded.example.json"),
            "supervisor.health",
        )

    def test_active_ownership_requires_owner_reviewer_evidence(self):
        payload = copy.deepcopy(example("connector.ownership.active.example.json"))
        payload["owner_refs"] = []
        result = classify_connector_ownership(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_owner_missing", result["reason_codes"])

    def test_stale_missing_conflicted_ownership_fails_closed(self):
        payload = copy.deepcopy(example("connector.ownership.stale-failed-closed.example.json"))
        result = classify_connector_ownership(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_owner_stale", result["reason_codes"])

        payload2 = copy.deepcopy(example("connector.ownership.active.example.json"))
        payload2["source_of_truth_status"] = "conflicted"
        result2 = classify_connector_ownership(payload2)
        self.assertTrue(result2["fail_closed"])
        self.assertIn("connector_source_of_truth_conflict", result2["reason_codes"])

    def test_sod_violation_fails_closed(self):
        payload = copy.deepcopy(example("connector.ownership.sod-violation.example.json"))
        result = classify_connector_ownership(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_sod_violation", result["reason_codes"])

    def test_revoked_transferred_require_reasons_and_evidence(self):
        payload = copy.deepcopy(example("connector.ownership.active.example.json"))
        payload["ownership_status"] = "transferred"
        payload["evidence_refs"] = []
        payload["reason_codes"] = []
        result = classify_connector_ownership(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_accountability_failed_closed", result["reason_codes"])

    def test_escalation_resolved_requires_evidence_and_resolved_at(self):
        payload = copy.deepcopy(example("connector.escalation.resolved-placeholder.example.json"))
        payload["resolved_at"] = None
        payload["evidence_refs"] = []
        result = classify_connector_escalation(payload)
        self.assertTrue(result["fail_closed"])
        self.assertEqual("failed_closed", result["escalation_status"])

    def test_revocation_overdue_escalation_fails_closed(self):
        payload = copy.deepcopy(
            example("connector.escalation.revocation-overdue-failed-closed.example.json")
        )
        result = classify_connector_escalation(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_escalation_overdue", result["reason_codes"])

    def test_revocation_overdue_missing_owner_ref_fails_closed(self):
        payload = copy.deepcopy(
            example("connector.escalation.revocation-overdue-failed-closed.example.json")
        )
        payload["escalation_owner_ref"] = ""
        result = classify_connector_escalation(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_revocation_owner_missing", result["reason_codes"])

    def test_source_of_truth_conflict_fails_closed(self):
        payload = copy.deepcopy(example("connector.escalation.stale-owner-opened.example.json"))
        payload["escalation_type"] = "source_of_truth_conflict"
        result = classify_connector_escalation(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_source_of_truth_conflict", result["reason_codes"])

    def test_helper_never_stores_reads_secrets_or_calls_external_apis(self):
        source = (ROOT / "lima_office" / "runtime" / "connector_ownership.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("requests.", "httpx.", "socket.", "urllib.", "subprocess.", "oauth.")
        for token in banned_tokens:
            self.assertNotIn(token, source)

    def test_helper_never_authorizes_real_connector_use(self):
        ownership = copy.deepcopy(example("connector.ownership.active.example.json"))
        escalation = copy.deepcopy(example("connector.escalation.stale-owner-opened.example.json"))
        self.assertFalse(classify_connector_ownership(ownership)["can_authorize"])
        self.assertFalse(classify_connector_escalation(escalation)["can_authorize"])

    def test_reason_code_gate_passes_new_ownership_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
