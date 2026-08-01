import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.connector_readiness import classify_connector_readiness
from lima_office.runtime.errors import PolicyDenyError


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_connectors", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class LiveConnectorCriteriaDesignTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def test_connector_readiness_examples_validate(self):
        self.validator.validate(
            example("connector.readiness.email-approved-for-lab.example.json"),
            "connector.readiness",
        )
        self.validator.validate(
            example("connector.readiness.browser-blocked-mvp.example.json"),
            "connector.readiness",
        )
        self.validator.validate(
            example("connector.readiness.rmm-it-approval-required.example.json"),
            "connector.readiness",
        )
        self.validator.validate(
            example("connector.readiness.revoked.example.json"),
            "connector.readiness",
        )

    def test_connector_scope_review_examples_validate(self):
        self.validator.validate(
            example("connector.scope_review.least-privilege-satisfied.example.json"),
            "connector.scope_review",
        )
        self.validator.validate(
            example("connector.scope_review.overbroad-denied.example.json"),
            "connector.scope_review",
        )
        self.validator.validate(
            example("connector.scope_review.object-auth-missing-failed-closed.example.json"),
            "connector.scope_review",
        )
        self.validator.validate(
            example("console.alert.connector-revoked.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("console.alert.connector-scope-overbroad.example.json"),
            "console.alert",
        )

    def test_email_approved_requires_consent_scope_evidence_owner(self):
        payload = copy.deepcopy(example("connector.readiness.email-approved-for-lab.example.json"))
        result = classify_connector_readiness(payload)
        self.assertEqual("approved_for_lab", result["readiness_status"])
        self.assertFalse(result["blocked"])
        self.assertFalse(result["can_authorize"])

    def test_browser_blocked_mvp_cannot_be_usable(self):
        payload = copy.deepcopy(example("connector.readiness.browser-blocked-mvp.example.json"))
        result = classify_connector_readiness(payload)
        self.assertTrue(result["blocked"])
        self.assertIn("connector_live_blocked_mvp", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_rmm_it_requires_approval_or_blocked_mvp(self):
        payload = copy.deepcopy(example("connector.readiness.rmm-it-approval-required.example.json"))
        result = classify_connector_readiness(payload)
        self.assertTrue(result["blocked"])
        self.assertIn(result["readiness_status"], {"review_required", "blocked_mvp", "failed_closed"})
        self.assertFalse(result["can_authorize"])

    def test_revoked_connector_requires_evidence_reason_revocation_refs(self):
        payload = copy.deepcopy(example("connector.readiness.revoked.example.json"))
        result = classify_connector_readiness(payload)
        self.assertIn("connector_revoked", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_overbroad_scope_fails_closed(self):
        readiness = copy.deepcopy(example("connector.readiness.email-approved-for-lab.example.json"))
        scope = copy.deepcopy(example("connector.scope_review.overbroad-denied.example.json"))
        result = classify_connector_readiness(readiness, scope_review=scope)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_scope_overbroad", result["reason_codes"])

    def test_missing_object_property_authorization_fails_closed(self):
        readiness = copy.deepcopy(example("connector.readiness.email-approved-for-lab.example.json"))
        scope = copy.deepcopy(example("connector.scope_review.object-auth-missing-failed-closed.example.json"))
        result = classify_connector_readiness(readiness, scope_review=scope)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_object_auth_missing", result["reason_codes"])
        self.assertIn("connector_property_auth_missing", result["reason_codes"])

    def test_outbound_action_missing_approval_policy_fails_closed(self):
        readiness = copy.deepcopy(example("connector.readiness.email-approved-for-lab.example.json"))
        readiness["approval_policy_refs"] = []
        result = classify_connector_readiness(readiness)
        self.assertTrue(result["fail_closed"])
        self.assertIn("connector_outbound_action_blocked", result["reason_codes"])

    def test_secret_value_api_key_token_fields_fail_if_present(self):
        readiness = copy.deepcopy(example("connector.readiness.email-approved-for-lab.example.json"))
        readiness["api_key"] = "should-not-exist"
        with self.assertRaises(PolicyDenyError):
            classify_connector_readiness(readiness)

    def test_helper_never_calls_external_apis_or_authorizes_real_connector_use(self):
        source = (ROOT / "lima_office" / "runtime" / "connector_readiness.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("requests.", "httpx.", "socket.", "urllib.", "subprocess.", "oauth.")
        for token in banned_tokens:
            self.assertNotIn(token, source)
        result = classify_connector_readiness(
            copy.deepcopy(example("connector.readiness.email-approved-for-lab.example.json"))
        )
        self.assertFalse(result["can_authorize"])

    def test_reason_code_gate_passes_new_connector_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
