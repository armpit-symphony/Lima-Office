import copy
import unittest

from helpers import example, guardian_allow_decision, has_jsonschema, task_example, token_valid_example, validator
from lima_office.guardian import ApprovalBindingVerifier
from lima_office.runtime.errors import ContractValidationError, EvidenceRequiredError, PolicyDenyError
from lima_office.runtime.invariants import assert_approval_binding_authorizes_action, assert_tool_invocation_consistent
from lima_office.supervisor import TaskQueue, WorkerRegistry


REFERENCE_TIME = "2026-05-18T21:44:00Z"


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ApprovalTokenBindingTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.verifier = ApprovalBindingVerifier(self.validator, reference_time=REFERENCE_TIME)

    def binding(self):
        return copy.deepcopy(example("approval.binding.bound-valid.example.json"))

    def requested_action(self, **updates):
        binding = self.binding()
        action = {
            "tenant_id": binding["tenant_id"],
            "customer_context_id": binding["customer_context_id"],
            "task_id": binding["task_id"],
            "tool_invocation_id": binding["tool_invocation_id"],
            "worker_id": binding["worker_id"],
            "guardian_decision_id": binding["guardian_decision_id"],
            "approval_request_id": binding["approval_request_id"],
            "approval_result_id": binding["approval_result_id"],
            "approval_token_id": binding["approval_token_id"],
            "token_verification_id": binding["token_verification_id"],
            "binding_id": binding["binding_id"],
            "approval_chain_id": binding["approval_chain_id"],
            "policy_version": binding["policy_version"],
            "policy_snapshot_hash": binding["policy_snapshot_hash"],
            "approved_scope_hash": binding["approved_scope_hash"],
            "action_type": binding["action_type"],
            "tool_scope": copy.deepcopy(binding["tool_scope"]),
            "evidence_required": True,
            "evidence_refs": ["ev-token-verify-valid-001"],
        }
        action.update(updates)
        return action

    def test_valid_one_time_binding_passes_once(self):
        verified = self.verifier.verify_once(self.binding(), self.requested_action())
        self.assertEqual("bind-email-draft-001", verified["binding_id"])
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.binding(), self.requested_action())

    def test_replay_of_one_time_binding_fails(self):
        binding = self.binding()
        consumed_nonces = {binding["nonce_ref"]}
        with self.assertRaises(PolicyDenyError):
            assert_approval_binding_authorizes_action(
                binding,
                self.requested_action(),
                reference_time=REFERENCE_TIME,
                consumed_nonces=consumed_nonces,
                consume_nonce=True,
            )

    def test_expired_token_fails(self):
        binding = self.binding()
        binding["expires_at"] = "2026-05-18T21:00:00Z"
        with self.assertRaises((ContractValidationError, PolicyDenyError)):
            self.verifier.verify_once(binding, self.requested_action())

    def test_revoked_token_fails(self):
        binding = self.binding()
        binding["status"] = "revoked"
        binding["verification_result"] = "revoked"
        binding["revoked_at"] = "2026-05-18T21:43:30Z"
        with self.assertRaises((ContractValidationError, PolicyDenyError)):
            self.verifier.verify_once(binding, self.requested_action())

    def test_tenant_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.binding(), self.requested_action(tenant_id="tenant-other"))

    def test_task_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.binding(), self.requested_action(task_id="task-other"))

    def test_worker_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.binding(), self.requested_action(worker_id="arc-other"))

    def test_action_type_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.binding(), self.requested_action(action_type="file_review"))

    def test_tool_scope_widening_fails(self):
        widened_scope = copy.deepcopy(self.binding()["tool_scope"])
        widened_scope["resource_refs"].append("draft-message-ref-other-002")
        widened_scope["allowed_operations"].append("send_external_message")
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.binding(), self.requested_action(tool_scope=widened_scope))

    def test_denied_approval_result_cannot_produce_usable_token(self):
        binding = self.binding()
        binding.update(
            {
                "status": "denied",
                "verification_result": "denied",
                "approval_token_id": None,
                "token_verification_id": None,
                "consumed_at": None,
            }
        )
        with self.assertRaises(PolicyDenyError):
            self.verifier.check(binding, self.requested_action())

    def test_blocked_mvp_approval_result_cannot_produce_usable_token(self):
        binding = copy.deepcopy(example("approval.binding.blocked-mvp.example.json"))
        with self.assertRaises(PolicyDenyError):
            self.verifier.check(binding, self.requested_action(action_type="lima_it_remediation"))

    def test_tainted_input_chain_cannot_authorize_privileged_tool(self):
        binding = self.binding()
        binding["input_taint_status"] = "suspected"
        binding["taint_ref_ids"] = ["taint-email-injection-001"]
        with self.assertRaises((ContractValidationError, PolicyDenyError)):
            self.verifier.verify_once(binding, self.requested_action())

    def test_lima_it_remediation_remains_blocked(self):
        binding = copy.deepcopy(example("approval.binding.blocked-mvp.example.json"))
        with self.assertRaises(PolicyDenyError):
            self.verifier.check(binding, self.requested_action(action_type="lima_it_remediation"))

    def test_missing_evidence_ref_fails_when_evidence_required(self):
        with self.assertRaises(EvidenceRequiredError):
            self.verifier.verify_once(self.binding(), self.requested_action(evidence_refs=[]))

    def test_guardian_decision_mismatch_fails(self):
        with self.assertRaises(PolicyDenyError):
            self.verifier.verify_once(self.binding(), self.requested_action(guardian_decision_id="gd-other"))

    def test_helper_cannot_authorize_live_connector_external_send_or_remediation(self):
        for action_type in ("live_connector_access", "external_send", "remediation"):
            with self.subTest(action_type=action_type):
                with self.assertRaises(PolicyDenyError):
                    self.verifier.verify_once(self.binding(), self.requested_action(action_type=action_type))

    def test_tool_invocation_must_match_binding(self):
        binding = self.binding()
        tool = copy.deepcopy(example("tool.invocation.tainted-input-denied.example.json"))
        tool.update(
            {
                "tenant_id": binding["tenant_id"],
                "customer_context_id": binding["customer_context_id"],
                "environment": "dry_run",
                "correlation_id": binding["correlation_id"],
                "causation_id": binding["guardian_decision_id"],
                "idempotency_key": "idem-tool-email-draft-review-001",
                "tool_invocation_id": binding["tool_invocation_id"],
                "task_id": binding["task_id"],
                "actor": {"actor_type": "worker", "actor_id": binding["worker_id"]},
                "execution_mode": "mock_only",
                "side_effect_class": "approval_required_write",
                "sandbox_profile": "mock_connector",
                "capability_lease_id": "cap-lease-admin-001",
                "tool_scope": copy.deepcopy(binding["tool_scope"]),
                "risk_tier": "high",
                "policy_result": "allow_with_evidence",
                "guardian_decision_id": binding["guardian_decision_id"],
                "approval_required": True,
                "approval_chain_id": binding["approval_chain_id"],
                "binding_id": binding["binding_id"],
                "approval_token_id": binding["approval_token_id"],
                "approval_result_id": binding["approval_result_id"],
                "token_verification_id": binding["token_verification_id"],
                "bound_action_type": binding["action_type"],
                "bound_worker_id": binding["worker_id"],
                "evidence_artifact_ids": ["ev-token-verify-valid-001"],
                "input_taint_status": "none",
                "taint_ref_ids": [],
                "status": "approved_to_run",
                "denial_reason": None,
                "denial_code": None,
            }
        )
        task = task_example()
        task.update(
            {
                "tenant_id": binding["tenant_id"],
                "customer_context_id": binding["customer_context_id"],
                "task_id": binding["task_id"],
                "assigned_worker_id": binding["worker_id"],
            }
        )
        worker = type("Worker", (), {"worker_id": binding["worker_id"], "tenant_id": binding["tenant_id"]})()
        assert_tool_invocation_consistent(tool, task=task, worker=worker, approval_binding=binding)

        tool["tool_scope"]["allowed_operations"] = ["send_external_message"]
        with self.assertRaises(PolicyDenyError):
            assert_tool_invocation_consistent(tool, task=task, worker=worker, approval_binding=binding)

    def test_approval_required_task_requires_binding(self):
        registry = WorkerRegistry()
        registry.register_mock_worker(
            worker_id="arc-it-helper-01",
            tenant_id="tenant-lab-001",
            role="it_helper_arc_worker",
            capabilities=["it_diagnostics_read_only"],
        )
        queue = TaskQueue(registry, self.validator, reference_time="2026-05-18T21:44:00Z")
        task = task_example()
        token = token_valid_example()
        task.update(
            {
                "task_id": token["task_id"],
                "approval_required": True,
                "approval_request_id": token["approval_request_id"],
                "approval_token_id": token["approval_token_id"],
                "approval_result_id": "apres-email-draft-001",
                "token_verification_id": token["token_verification_id"],
                "guardian_decision_id": token["guardian_decision_id"],
                "assigned_worker_id": None,
                "evidence_artifact_ids": ["ev-token-verify-valid-001"],
            }
        )
        guardian = guardian_allow_decision()
        guardian["decision_id"] = task["guardian_decision_id"]
        guardian["guardian_decision_id"] = task["guardian_decision_id"]
        guardian["decision"] = "allow_with_evidence"
        guardian["approval_required"] = False
        guardian["approval_request_id"] = None
        guardian["approval_token_id"] = None
        guardian["subject"] = {"subject_type": "task", "subject_id": task["task_id"]}
        guardian["created_at"] = "2026-05-18T21:43:00Z"
        guardian["issued_at"] = "2026-05-18T21:43:00Z"
        guardian["effective_at"] = "2026-05-18T21:43:00Z"
        guardian["expires_at"] = "2026-05-18T21:50:00Z"
        guardian["evidence_artifact_id"] = "ev-token-verify-valid-001"
        guardian["evidence_artifact_ids"] = ["ev-token-verify-valid-001"]
        guardian["evidence_refs"] = ["ev-token-verify-valid-001"]
        with self.assertRaises(PolicyDenyError):
            queue.enqueue(task, guardian, token)

        accepted = queue.enqueue(task, guardian, token, self.binding())
        self.assertEqual(task["task_id"], accepted["task_id"])

if __name__ == "__main__":
    unittest.main()
