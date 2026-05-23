import copy
import unittest

from helpers import example, has_jsonschema, validator
from lima_office.guardian import GuardianDecisionReplayVerifier
from lima_office.runtime.errors import ContractValidationError, EvidenceRequiredError, PolicyDenyError
from lima_office.runtime.invariants import assert_guardian_decision_replay_safe


REFERENCE_TIME = "2026-05-18T21:44:00Z"


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class GuardianExpiryReplayTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.verifier = GuardianDecisionReplayVerifier(self.validator, reference_time=REFERENCE_TIME)

    def decision(self):
        return copy.deepcopy(example("guardian.decision.allowed-one-time.example.json"))

    def binding(self):
        return copy.deepcopy(example("approval.binding.bound-valid.example.json"))

    def requested_action(self, **updates):
        decision = self.decision()
        action = {
            "tenant_id": decision["tenant_id"],
            "customer_context_id": decision["customer_context_id"],
            "task_id": decision["bound_task_id"],
            "worker_id": decision["bound_worker_id"],
            "guardian_decision_id": decision["decision_id"],
            "approval_binding_id": decision["approval_binding_id"],
            "binding_id": decision["binding_id"],
            "approval_chain_id": decision["approval_chain_id"],
            "token_verification_id": decision["token_verification_id"],
            "action_type": decision["bound_action_type"],
            "tool_scope": copy.deepcopy(decision["bound_tool_scope"]),
            "decision_scope_hash": decision["decision_scope_hash"],
            "evidence_required": True,
            "evidence_refs": ["ev-guardian-email-draft-001"],
            "approval_binding": self.binding(),
        }
        action.update(updates)
        return action

    def test_valid_one_time_guardian_decision_passes_once(self):
        replay = self.verifier.verify_once(self.decision(), self.requested_action())
        self.assertEqual("valid_first_use", replay["replay_check_result"])
        self.assertIn("decision-nonce-email-draft-001", self.verifier.consumed_nonces)
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action())

    def test_replayed_guardian_decision_fails(self):
        decision = self.decision()
        with self.assertRaises(PolicyDenyError):
            assert_guardian_decision_replay_safe(
                decision,
                self.requested_action(),
                reference_time=REFERENCE_TIME,
                consumed_nonces={decision["decision_nonce"]},
                consume_nonce=True,
            )

    def test_expired_guardian_decision_fails(self):
        decision = self.decision()
        decision["expires_at"] = "2026-05-18T21:43:30Z"
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(decision, self.requested_action())

    def test_stale_guardian_decision_fails(self):
        decision = self.decision()
        decision["issued_at"] = "2026-05-18T21:30:00Z"
        decision["effective_at"] = "2026-05-18T21:30:00Z"
        decision["created_at"] = "2026-05-18T21:30:00Z"
        decision["expires_at"] = "2026-05-18T21:50:00Z"
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(decision, self.requested_action())

    def test_missing_expires_at_fails_for_allowed_decision(self):
        decision = self.decision()
        decision["expires_at"] = None
        with self.assertRaises((ContractValidationError, PolicyDenyError)):
            self.verifier.verify_once(decision, self.requested_action())

    def test_effective_at_in_future_beyond_skew_fails(self):
        decision = self.decision()
        decision["effective_at"] = "2026-05-18T21:45:00Z"
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(decision, self.requested_action())

    def test_clock_skew_within_allowance_passes_when_otherwise_safe(self):
        decision = self.decision()
        decision["decision_nonce"] = "decision-nonce-email-draft-skew-001"
        decision["effective_at"] = "2026-05-18T21:44:20Z"
        decision["clock_skew_allowance_seconds"] = 30
        replay = self.verifier.verify_once(decision, self.requested_action())
        self.assertEqual("valid_first_use", replay["replay_check_result"])

    def test_tenant_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action(tenant_id="tenant-other"))

    def test_task_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action(task_id="task-other"))

    def test_worker_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action(worker_id="arc-other"))

    def test_action_type_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action(action_type="file_review"))

    def test_tool_scope_mismatch_fails(self):
        scope = copy.deepcopy(self.decision()["bound_tool_scope"])
        scope["resource_refs"] = ["draft-message-ref-other-002"]
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action(tool_scope=scope))

    def test_decision_scope_hash_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action(decision_scope_hash="hash-other"))

    def test_blocked_mvp_decision_fails(self):
        decision = copy.deepcopy(example("guardian.decision.blocked-mvp.example.json"))
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(decision, self.requested_action(action_type="live_connector_access"))

    def test_lima_it_remediation_decision_fails_in_mvp(self):
        decision = copy.deepcopy(example("guardian.decision.lima-it-remediation-denied.example.json"))
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(decision, self.requested_action(action_type="lima_it_remediation"))

    def test_external_send_and_live_connector_fail_in_mvp(self):
        for action_type in ("external_send", "live_connector_access"):
            with self.subTest(action_type=action_type):
                decision = self.decision()
                decision["decision_nonce"] = f"decision-nonce-{action_type}-001"
                decision["bound_action_type"] = action_type
                with self.assertRaises(PolicyDenyError):
                    self.verifier.verify_once(decision, self.requested_action(action_type=action_type))

    def test_guardian_decision_mismatch_with_approval_binding_fails(self):
        binding = self.binding()
        binding["guardian_decision_id"] = "gd-other"
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.decision(), self.requested_action(approval_binding=binding))

    def test_ambiguous_timestamp_fails_closed(self):
        decision = self.decision()
        decision["issued_at"] = "2026-05-18T21:43:20"
        with self.assertRaises(PolicyDenyError):
            assert_guardian_decision_replay_safe(decision, self.requested_action(), reference_time=REFERENCE_TIME)

    def test_missing_evidence_ref_fails_when_evidence_required(self):
        with self.assertRaises(EvidenceRequiredError):
            self.verifier.verify_once(self.decision(), self.requested_action(evidence_refs=[]))

    def test_helper_cannot_authorize_real_external_action(self):
        for action_type in ("external_send", "live_connector_access", "lima_it_remediation"):
            with self.subTest(action_type=action_type):
                decision = self.decision()
                decision["decision_nonce"] = f"decision-nonce-real-action-{action_type}"
                decision["bound_action_type"] = action_type
                with self.assertRaises(PolicyDenyError):
                    self.verifier.verify_once(decision, self.requested_action(action_type=action_type))


if __name__ == "__main__":
    unittest.main()
