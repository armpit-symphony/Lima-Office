import copy
import unittest

from helpers import example, guardian_allow_decision, has_jsonschema, task_example, token_expired_example, token_valid_example, validator
from lima_office.runtime.errors import ContractValidationError
from lima_office.runtime.errors import EvidenceRequiredError, PolicyDenyError, UnsafeRuntimeActionError, WorkerStateError
from lima_office.supervisor import TaskQueue, WorkerRegistry


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class TaskQueueTests(unittest.TestCase):
    def setUp(self):
        self.registry = WorkerRegistry()
        self.registry.register_mock_worker(
            worker_id="arc-it-helper-01",
            tenant_id="tenant-lab-001",
            role="it_helper_arc_worker",
            capabilities=["it_diagnostics_read_only"],
        )
        self.validator = validator()
        self.queue = TaskQueue(self.registry, self.validator)

    def bound_decision(self, task):
        decision = guardian_allow_decision()
        decision["decision_id"] = task["guardian_decision_id"]
        decision["guardian_decision_id"] = task["guardian_decision_id"]
        decision["tenant_id"] = task["tenant_id"]
        decision["subject"] = {"subject_type": "task", "subject_id": task["task_id"]}
        decision["evidence_artifact_id"] = task["evidence_artifact_ids"][0]
        decision["evidence_artifact_ids"] = list(task["evidence_artifact_ids"])
        decision["evidence_refs"] = list(task["evidence_artifact_ids"])
        return decision

    def test_enqueue_requires_guardian_decision(self):
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task_example())

    def test_enqueue_accepts_valid_mock_task(self):
        task = task_example()
        accepted = self.queue.enqueue(task, self.bound_decision(task))
        self.assertEqual(task["task_id"], accepted["task_id"])

    def test_rejects_unbound_guardian_decision(self):
        task = task_example()
        decision = self.bound_decision(task)
        decision["decision_id"] = "gd-other"
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, decision)

    def test_rejects_forged_minimal_allow_decision(self):
        with self.assertRaises(ContractValidationError):
            self.queue.enqueue(task_example(), {"decision": "allow"})

    def test_quarantined_worker_cannot_receive_task(self):
        self.registry.quarantine("arc-it-helper-01", "test")
        task = task_example()
        with self.assertRaises(WorkerStateError):
            self.queue.enqueue(task, self.bound_decision(task))

    def test_revoked_worker_cannot_receive_task(self):
        self.registry.revoke("arc-it-helper-01", "test")
        task = task_example()
        with self.assertRaises(WorkerStateError):
            self.queue.enqueue(task, self.bound_decision(task))

    def test_evidence_required_completion_without_evidence_denied(self):
        task = task_example()
        task["status"] = "in_progress"
        self.queue.enqueue(task, self.bound_decision(task))
        with self.assertRaises(EvidenceRequiredError):
            self.queue.complete_mock(task["task_id"], [])

    def test_approval_required_task_requires_valid_token_verification(self):
        task = task_example()
        task.update(
            {
                "approval_required": True,
                "approval_request_id": "apr-phase1a-001",
                "approval_token_id": "apt-phase1a-001",
                "approval_result_id": "ar-phase1a-001",
                "token_verification_id": "tv-phase1a-001",
            }
        )
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, self.bound_decision(task))

    def test_expired_token_verification_denied(self):
        task = task_example()
        task.update(
            {
                "approval_required": True,
                "approval_request_id": "apr-email-expired-001",
                "approval_token_id": "apt-email-expired-001",
                "approval_result_id": "ar-phase1a-001",
                "token_verification_id": "tv-email-expired-001",
                "task_id": "task-email-draft-002",
            }
        )
        token = token_expired_example()
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, self.bound_decision(task), token)

    def test_valid_token_verification_can_enqueue_mock_only_metadata(self):
        task = task_example()
        task.update(
            {
                "approval_required": True,
                "approval_request_id": "apr-email-draft-001",
                "approval_token_id": "apt-email-draft-001",
                "approval_result_id": "apres-email-draft-001",
                "token_verification_id": "tv-email-valid-001",
                "task_id": "task-email-draft-001",
                "assigned_worker_id": None,
            }
        )
        token = token_valid_example()
        task["guardian_decision_id"] = token["guardian_decision_id"]
        binding = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
        task["evidence_artifact_ids"] = ["ev-token-verify-valid-001"]
        accepted = self.queue.enqueue(task, self.bound_decision(task), token, binding)
        self.assertEqual("task-email-draft-001", accepted["task_id"])

    def test_expired_approval_binding_denied(self):
        task = task_example()
        task.update(
            {
                "approval_required": True,
                "approval_request_id": "apr-email-draft-001",
                "approval_token_id": "apt-email-draft-001",
                "approval_result_id": "apres-email-draft-001",
                "token_verification_id": "tv-email-valid-001",
                "task_id": "task-email-draft-001",
                "assigned_worker_id": None,
            }
        )
        token = token_valid_example()
        task["guardian_decision_id"] = token["guardian_decision_id"]
        task["evidence_artifact_ids"] = ["ev-token-verify-valid-001"]
        binding = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
        binding["expires_at"] = "2026-05-19T23:59:00Z"
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, self.bound_decision(task), token, binding)

    def test_task_with_external_effect_denied(self):
        task = task_example()
        task["task_scope"]["external_effect"] = "approval_required"
        with self.assertRaises(UnsafeRuntimeActionError):
            self.queue.enqueue(task, self.bound_decision(task))


if __name__ == "__main__":
    unittest.main()
