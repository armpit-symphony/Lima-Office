import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.access_matrix import AccessMatrixEvaluator


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class RbacIdpMfaDeviceTrustMatrixTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.evaluator = AccessMatrixEvaluator()

    def test_rbac_matrix_examples_validate(self):
        self.validator.validate(
            example("governance.rbac_matrix.approver-privileged.example.json"),
            "governance.rbac_matrix",
        )
        self.validator.validate(
            example("governance.rbac_matrix.auditor-readonly.example.json"),
            "governance.rbac_matrix",
        )
        self.validator.validate(
            example("governance.rbac_matrix.field-it-remediation-blocked.example.json"),
            "governance.rbac_matrix",
        )

    def test_session_policy_examples_validate(self):
        self.validator.validate(
            example("governance.session_policy.step-up-required.example.json"),
            "governance.session_policy",
        )
        self.validator.validate(
            example("governance.session_policy.revoked-on-role-change.example.json"),
            "governance.session_policy",
        )

    def test_device_trust_examples_validate(self):
        self.validator.validate(
            example("governance.device_trust.operator-managed.example.json"),
            "governance.device_trust",
        )
        self.validator.validate(
            example("governance.device_trust.worker-attestation-required.example.json"),
            "governance.device_trust",
        )
        self.validator.validate(
            example("governance.device_trust.untrusted-blocked.example.json"),
            "governance.device_trust",
        )

    def test_auditor_readonly_cannot_approve_or_mutate(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.auditor-readonly.example.json"))
        rbac["permissions"].append({"action": "approve_low_risk_task", "level": "approve"})
        result = self.evaluator.evaluate(rbac_matrix=rbac, action="approve_low_risk_task")
        self.assertTrue(result["fail_closed"])
        self.assertIn("role_not_permitted", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_untrusted_device_cannot_approve_privileged_action(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.approver-privileged.example.json"))
        session = copy.deepcopy(example("governance.session_policy.step-up-required.example.json"))
        device = copy.deepcopy(example("governance.device_trust.untrusted-blocked.example.json"))
        result = self.evaluator.evaluate(
            rbac_matrix=rbac,
            session_policy=session,
            device_trust=device,
            action="approve_privileged_task",
        )
        self.assertTrue(result["fail_closed"])
        self.assertIn("device_untrusted", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_missing_mfa_requirement_for_privileged_action_fails(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.approver-privileged.example.json"))
        session = copy.deepcopy(example("governance.session_policy.step-up-required.example.json"))
        device = copy.deepcopy(example("governance.device_trust.operator-managed.example.json"))
        rbac["mfa_requirement"] = "no_mfa_blocked"
        result = self.evaluator.evaluate(
            rbac_matrix=rbac,
            session_policy=session,
            device_trust=device,
            action="approve_privileged_task",
        )
        self.assertTrue(result["fail_closed"])
        self.assertIn("mfa_required", result["reason_codes"])

    def test_lima_it_remediation_is_blocked_or_sod_required(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.field-it-remediation-blocked.example.json"))
        session = copy.deepcopy(example("governance.session_policy.step-up-required.example.json"))
        device = copy.deepcopy(example("governance.device_trust.operator-managed.example.json"))
        result = self.evaluator.evaluate(
            rbac_matrix=rbac,
            session_policy=session,
            device_trust=device,
            action="approve_lima_it_remediation",
        )
        self.assertEqual("blocked_mvp", result["matrix_outcome"])
        self.assertIn("privileged_action_blocked", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_breakglass_remains_blocked_mvp(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.approver-privileged.example.json"))
        result = self.evaluator.evaluate(rbac_matrix=rbac, action="breakglass_request_review")
        self.assertEqual("blocked_mvp", result["matrix_outcome"])
        self.assertIn("breakglass_blocked_mvp", result["reason_codes"])

    def test_attestation_failed_worker_cannot_receive_privileged_task_metadata(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.approver-privileged.example.json"))
        rbac["permissions"].append(
            {
                "action": "receive_privileged_task_metadata",
                "level": "approve",
            }
        )
        session = copy.deepcopy(example("governance.session_policy.step-up-required.example.json"))
        device = copy.deepcopy(example("governance.device_trust.worker-attestation-required.example.json"))
        device["trust_status"] = "attestation_failed"
        device["reason_codes"] = ["attestation_failed"]
        result = self.evaluator.evaluate(
            rbac_matrix=rbac,
            session_policy=session,
            device_trust=device,
            action="receive_privileged_task_metadata",
        )
        self.assertTrue(result["fail_closed"])
        self.assertIn("attestation_failed", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_role_change_session_revocation_is_represented(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.approver-privileged.example.json"))
        session = copy.deepcopy(example("governance.session_policy.revoked-on-role-change.example.json"))
        device = copy.deepcopy(example("governance.device_trust.operator-managed.example.json"))
        result = self.evaluator.evaluate(
            rbac_matrix=rbac,
            session_policy=session,
            device_trust=device,
            action="approve_privileged_task",
        )
        self.assertTrue(result["fail_closed"])
        self.assertIn("session_revoked", result["reason_codes"])

    def test_helper_fails_closed_on_unknown_role_or_action(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.approver-privileged.example.json"))
        rbac["role"] = "unknown_role"
        result = self.evaluator.evaluate(rbac_matrix=rbac, action="unknown_action")
        self.assertTrue(result["fail_closed"])
        self.assertIn("role_not_permitted", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_helper_never_authorizes_or_creates_real_sessions(self):
        rbac = copy.deepcopy(example("governance.rbac_matrix.approver-privileged.example.json"))
        result = self.evaluator.evaluate(rbac_matrix=rbac, action="deny_task")
        self.assertFalse(result["can_authorize"])
        with tempfile.TemporaryDirectory() as tmp:
            before = set(Path(tmp).iterdir())
            _ = self.evaluator.evaluate(rbac_matrix=rbac, action="deny_task")
            after = set(Path(tmp).iterdir())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
