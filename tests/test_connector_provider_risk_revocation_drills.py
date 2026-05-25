import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.connector_risk import classify_provider_profile, classify_revocation_drill
from lima_office.runtime.errors import PolicyDenyError


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_connector_risk", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ConnectorProviderRiskRevocationDrillsTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def test_provider_profile_examples_validate(self):
        self.validator.validate(
            example("connector.provider_profile.email-medium-risk.example.json"),
            "connector.provider_profile",
        )
        self.validator.validate(
            example("connector.provider_profile.browser-blocked-mvp.example.json"),
            "connector.provider_profile",
        )
        self.validator.validate(
            example("connector.provider_profile.rmm-it-critical-review-required.example.json"),
            "connector.provider_profile",
        )
        self.validator.validate(
            example("connector.provider_profile.revoked.example.json"),
            "connector.provider_profile",
        )

    def test_revocation_drill_examples_validate(self):
        self.validator.validate(
            example("connector.revocation_drill.revocation-passed.example.json"),
            "connector.revocation_drill",
        )
        self.validator.validate(
            example("connector.revocation_drill.disable-switch-failed-closed.example.json"),
            "connector.revocation_drill",
        )
        self.validator.validate(
            example("connector.revocation_drill.cross-tenant-blocked.example.json"),
            "connector.revocation_drill",
        )
        self.validator.validate(
            example("connector.revocation_drill.prompt-injection-blocked.example.json"),
            "connector.revocation_drill",
        )
        self.validator.validate(
            example("console.alert.connector-provider-risk-critical.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.connector-risk-degraded.example.json"),
            "supervisor.health",
        )

    def test_approved_for_lab_requires_revocation_disable_evidence(self):
        payload = copy.deepcopy(example("connector.provider_profile.email-medium-risk.example.json"))
        payload["provider_status"] = "approved_for_lab"
        payload["revocation_method_status"] = "missing"
        result = classify_provider_profile(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_revocation_unverified", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_critical_provider_risk_without_review_evidence_fails(self):
        payload = copy.deepcopy(
            example("connector.provider_profile.rmm-it-critical-review-required.example.json")
        )
        payload["provider_status"] = "profiled"
        payload["evidence_refs"] = []
        result = classify_provider_profile(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_provider_critical_risk", result["reason_codes"])

    def test_blocked_mvp_provider_cannot_be_approved(self):
        payload = copy.deepcopy(example("connector.provider_profile.browser-blocked-mvp.example.json"))
        payload["provider_status"] = "approved_for_lab"
        payload["risk_level"] = "blocked_mvp"
        result = classify_provider_profile(payload)
        self.assertTrue(result["blocked"])
        self.assertIn("connector_live_blocked_mvp", result["reason_codes"])

    def test_revoked_or_disabled_provider_requires_reason_and_evidence(self):
        payload = copy.deepcopy(example("connector.provider_profile.revoked.example.json"))
        payload["reason_codes"] = []
        payload["evidence_refs"] = []
        result = classify_provider_profile(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_revocation_unverified", result["reason_codes"])

    def test_disable_switch_missing_fails_closed(self):
        payload = copy.deepcopy(
            example("connector.provider_profile.rmm-it-critical-review-required.example.json")
        )
        payload["disable_switch_status"] = "missing"
        result = classify_provider_profile(payload)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_disable_switch_missing", result["reason_codes"])

    def test_revocation_drill_failed_closed_requires_evidence_and_reasons(self):
        drill = copy.deepcopy(
            example("connector.revocation_drill.disable-switch-failed-closed.example.json")
        )
        drill["reason_codes"] = []
        drill["evidence_refs"] = []
        result = classify_revocation_drill(drill)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_revocation_drill_failed", result["reason_codes"])

    def test_cross_tenant_drill_cannot_pass_as_usable(self):
        drill = copy.deepcopy(example("connector.revocation_drill.cross-tenant-blocked.example.json"))
        drill["drill_status"] = "passed"
        drill["actual_outcome"] = "connector_usable"
        result = classify_revocation_drill(drill)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_cross_tenant_blocked", result["reason_codes"])

    def test_prompt_injection_drill_blocks_outbound_connector_action(self):
        drill = copy.deepcopy(
            example("connector.revocation_drill.prompt-injection-blocked.example.json")
        )
        result = classify_revocation_drill(drill)
        self.assertTrue(result["blocked"])
        self.assertIn("connector_prompt_injection_blocked", result["reason_codes"])

    def test_helper_never_stores_reads_secrets_or_calls_external_apis(self):
        source = (ROOT / "lima_office" / "runtime" / "connector_risk.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("requests.", "httpx.", "socket.", "urllib.", "subprocess.", "oauth.")
        for token in banned_tokens:
            self.assertNotIn(token, source)

        payload = copy.deepcopy(example("connector.provider_profile.email-medium-risk.example.json"))
        payload["api_key"] = "never-allowed"
        with self.assertRaises(PolicyDenyError):
            classify_provider_profile(payload)

        result = classify_provider_profile(
            copy.deepcopy(example("connector.provider_profile.email-medium-risk.example.json"))
        )
        self.assertFalse(result["can_authorize"])

    def test_reason_code_gate_passes_new_connector_risk_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
