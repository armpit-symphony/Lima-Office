import unittest

from helpers import has_jsonschema, validator
from lima_office.guardian import GuardianPolicy
from lima_office.runtime.errors import PolicyDenyError


class GuardianPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = GuardianPolicy()

    def test_default_denies_unknown_action(self):
        decision = self.policy.decide("unknown_action")
        self.assertEqual("deny", decision["decision"])
        self.assertIsNone(decision["approval_token_id"])
        self.assertTrue(decision["evidence_artifact_ids"])

    def test_allows_only_mock_read_only_internal_action(self):
        decision = self.policy.decide(
            "read_only_diagnostic",
            {
                "tenant_id": "tenant-lab-001",
                "customer_context_id": "customer-context-main",
                "execution_mode": "mock_only",
                "external_effect": "none",
                "evidence_required": True,
                "evidence_artifact_ids": ["ev-task-it-health-001"],
            },
        )
        self.assertEqual("allow_with_evidence", decision["decision"])
        self.assertTrue(decision["evidence_required"])

    def test_mock_allow_requires_explicit_context(self):
        decision = self.policy.decide("read_only_diagnostic", {"execution_mode": "mock_only"})
        self.assertEqual("deny", decision["decision"])

    def test_external_send_denied(self):
        self.assertEqual("deny", self.policy.decide("external_send")["decision"])

    def test_remediation_denied(self):
        self.assertEqual("deny", self.policy.decide("remediation")["decision"])

    def test_tainted_privileged_action_denied(self):
        decision = self.policy.decide("read_only_diagnostic", {"tainted_input_privileged_action": True})
        self.assertEqual("deny", decision["decision"])

    def test_missing_approval_denied(self):
        decision = self.policy.decide("internal_note", {"approval_required": True})
        self.assertEqual("deny", decision["decision"])

    def test_expired_and_revoked_token_denied(self):
        for state in ("expired", "revoked"):
            with self.subTest(state=state):
                decision = self.policy.decide(
                    "internal_note",
                    {
                        "approval_required": True,
                        "token_verification": {
                            "verification_result": state,
                            "can_proceed": False,
                            "token_status_observed": state,
                        },
                    },
                )
                self.assertEqual("deny", decision["decision"])

    def test_require_allowed_raises_on_denial(self):
        with self.assertRaises(PolicyDenyError):
            self.policy.require_allowed("file_delete")

    @unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
    def test_generated_guardian_decisions_validate(self):
        runtime_validator = validator()
        for action in ("unknown_action", "read_only_diagnostic", "external_send", "remediation"):
            with self.subTest(action=action):
                context = {
                    "tenant_id": "tenant-lab-001",
                    "customer_context_id": "customer-context-main",
                    "execution_mode": "mock_only",
                    "external_effect": "none",
                    "evidence_required": True,
                    "evidence_artifact_ids": ["ev-task-it-health-001"],
                }
                runtime_validator.validate(self.policy.decide(action, context), "guardian.decision")


if __name__ == "__main__":
    unittest.main()
