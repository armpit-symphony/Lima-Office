import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.connector_defaults import (
    classify_connector_defaults,
    classify_connector_defaults_bundle,
    classify_connector_score_threshold,
    classify_connector_slo_target,
)
from lima_office.runtime.errors import PolicyDenyError


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_connector_defaults", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ConnectorSourceOfTruthValuesSloTargetsTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def test_connector_defaults_examples_validate(self):
        self.validator.validate(
            example("connector.defaults.email-defaults.example.json"),
            "connector.defaults",
        )
        self.validator.validate(
            example("connector.defaults.browser-blocked-mvp.example.json"),
            "connector.defaults",
        )
        self.validator.validate(
            example("connector.defaults.rmm-it-approval-required.example.json"),
            "connector.defaults",
        )
        self.validator.validate(
            example("connector.defaults.tenant-override-review-required.example.json"),
            "connector.defaults",
        )

    def test_slo_target_examples_validate(self):
        self.validator.validate(
            example("connector.slo_target.email-placeholder.example.json"),
            "connector.slo_target",
        )
        self.validator.validate(
            example("connector.slo_target.revocation-missed-failed-closed.example.json"),
            "connector.slo_target",
        )

    def test_score_threshold_examples_validate(self):
        self.validator.validate(
            example("connector.score_threshold.default-lab-thresholds.example.json"),
            "connector.score_threshold",
        )
        self.validator.validate(
            example("connector.score_threshold.blocked-mvp-categories.example.json"),
            "connector.score_threshold",
        )

    def test_console_and_supervisor_examples_validate(self):
        self.validator.validate(
            example("console.alert.connector-slo-target-missed.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.connector-defaults-missing.example.json"),
            "supervisor.health",
        )

    def test_browser_blocked_mvp_defaults_cannot_include_live_allowed_actions(self):
        payload = copy.deepcopy(example("connector.defaults.browser-blocked-mvp.example.json"))
        payload["default_allowed_actions"] = ["metadata_read"]
        result = classify_connector_defaults(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_default_outbound_blocked", result["reason_codes"])

    def test_high_critical_defaults_require_reviewer_approver_revocation_disable(self):
        payload = copy.deepcopy(example("connector.defaults.rmm-it-approval-required.example.json"))
        payload["default_approver_required"] = False
        result = classify_connector_defaults(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_defaults_missing", result["reason_codes"])

    def test_tenant_override_requires_evidence_and_review(self):
        payload = copy.deepcopy(example("connector.defaults.email-defaults.example.json"))
        payload["tenant_override_status"] = "approved_placeholder"
        payload["evidence_refs"] = []
        payload["reason_codes"] = []
        result = classify_connector_defaults(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_defaults_override_review_required", result["reason_codes"])

    def test_missing_slo_target_fails_closed(self):
        defaults = copy.deepcopy(example("connector.defaults.email-defaults.example.json"))
        threshold = copy.deepcopy(example("connector.score_threshold.default-lab-thresholds.example.json"))
        result = classify_connector_defaults_bundle(
            defaults=defaults,
            slo_target=None,
            score_threshold=threshold,
        )
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_slo_target_missing", result["reason_codes"])

    def test_missed_slo_target_requires_evidence_and_reasons(self):
        payload = copy.deepcopy(example("connector.slo_target.revocation-missed-failed-closed.example.json"))
        payload["reason_codes"] = []
        payload["evidence_refs"] = []
        result = classify_connector_slo_target(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_slo_target_missing", result["reason_codes"])

    def test_active_placeholder_slo_requires_owner_reviewer_evidence(self):
        payload = copy.deepcopy(example("connector.slo_target.email-placeholder.example.json"))
        payload["owner_ref"] = None
        payload["reviewer_ref"] = None
        payload["evidence_refs"] = []
        result = classify_connector_slo_target(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_slo_target_missing", result["reason_codes"])

    def test_active_threshold_requires_evidence(self):
        payload = copy.deepcopy(example("connector.score_threshold.default-lab-thresholds.example.json"))
        payload["evidence_refs"] = []
        result = classify_connector_score_threshold(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_score_threshold_missing", result["reason_codes"])

    def test_required_dimensions_cannot_be_empty(self):
        payload = copy.deepcopy(example("connector.score_threshold.default-lab-thresholds.example.json"))
        payload["required_dimensions"] = []
        result = classify_connector_score_threshold(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_score_threshold_missing", result["reason_codes"])

    def test_helper_never_stores_reads_secrets(self):
        payload = copy.deepcopy(example("connector.defaults.email-defaults.example.json"))
        payload["api_key"] = "forbidden"
        with self.assertRaises(PolicyDenyError):
            classify_connector_defaults(payload)

    def test_helper_never_calls_external_apis(self):
        source = (ROOT / "lima_office" / "runtime" / "connector_defaults.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("requests.", "httpx.", "socket.", "urllib.", "subprocess.", "oauth.")
        for token in banned_tokens:
            self.assertNotIn(token, source)

    def test_helper_never_authorizes_real_connector_use(self):
        defaults = classify_connector_defaults(
            copy.deepcopy(example("connector.defaults.email-defaults.example.json"))
        )
        slo = classify_connector_slo_target(
            copy.deepcopy(example("connector.slo_target.email-placeholder.example.json"))
        )
        threshold = classify_connector_score_threshold(
            copy.deepcopy(example("connector.score_threshold.default-lab-thresholds.example.json"))
        )
        bundle = classify_connector_defaults_bundle(
            defaults=copy.deepcopy(example("connector.defaults.email-defaults.example.json")),
            slo_target=copy.deepcopy(example("connector.slo_target.email-placeholder.example.json")),
            score_threshold=copy.deepcopy(
                example("connector.score_threshold.default-lab-thresholds.example.json")
            ),
        )
        self.assertFalse(defaults["can_authorize"])
        self.assertFalse(slo["can_authorize"])
        self.assertFalse(threshold["can_authorize"])
        self.assertFalse(bundle["can_authorize"])

    def test_reason_code_gate_passes_new_defaults_slo_threshold_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
