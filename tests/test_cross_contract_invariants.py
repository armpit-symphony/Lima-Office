import copy
import unittest

from helpers import (
    example,
    guardian_allow_decision,
    has_jsonschema,
    heartbeat_example,
    task_example,
    token_expired_example,
    token_valid_example,
    validator,
)
from lima_office.evidence import EvidenceWriter
from lima_office.guardian import GuardianPolicy
from lima_office.runtime.errors import (
    CrossContractInvariantError,
    EvidenceRequiredError,
    PolicyDenyError,
    WorkerStateError,
)
from lima_office.runtime.invariants import (
    assert_helper_scope_allows_task,
    assert_lima_it_handoff_consistent,
    assert_memory_access_consistent,
    assert_task_completion_allowed,
    assert_tool_invocation_consistent,
)
from lima_office.supervisor import HeartbeatService, TaskQueue, WorkerRegistry


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class CrossContractInvariantTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.registry = WorkerRegistry()
        self.worker = self.registry.register_mock_worker(
            worker_id="arc-it-helper-01",
            tenant_id="tenant-lab-001",
            role="it_helper_arc_worker",
            capabilities=["it_diagnostics_read_only"],
        )
        self.writer = EvidenceWriter(self.validator)
        self.queue = TaskQueue(self.registry, self.validator, evidence_writer=self.writer)

    def bound_decision(self, task):
        decision = guardian_allow_decision()
        decision["decision_id"] = task["guardian_decision_id"]
        decision["tenant_id"] = task["tenant_id"]
        decision["customer_context_id"] = task["customer_context_id"]
        decision["subject"] = {"subject_type": "task", "subject_id": task["task_id"]}
        return decision

    def in_progress_task(self):
        task = task_example()
        task["status"] = "in_progress"
        task["evidence_artifact_ids"] = ["ev-task-it-health-001"]
        return task

    def test_valid_safe_flow_passes(self):
        task = self.in_progress_task()
        decision = self.bound_decision(task)
        accepted = self.queue.enqueue(task, decision)
        artifact = self.writer.write_artifact(
            artifact_type="task_transition",
            subject_id=accepted["task_id"],
            action="read_only_diagnostic",
            guardian_decision_id=decision["decision_id"],
        )
        completed = self.queue.complete_mock(task["task_id"], [artifact["artifact_id"]])
        self.assertEqual("completed_mock", completed["status"])

    def test_evidence_required_completion_without_evidence_fails(self):
        task = self.in_progress_task()
        self.queue.enqueue(task, self.bound_decision(task))
        with self.assertRaises(EvidenceRequiredError):
            self.queue.complete_mock(task["task_id"], [])

    def test_guardian_denied_decision_blocks_completion(self):
        task = self.in_progress_task()
        denied = GuardianPolicy().decide("external_send")
        denied["decision_id"] = task["guardian_decision_id"]
        denied["tenant_id"] = task["tenant_id"]
        denied["customer_context_id"] = task["customer_context_id"]
        denied["subject"] = {"subject_type": "task", "subject_id": task["task_id"]}
        with self.assertRaises(PolicyDenyError):
            assert_task_completion_allowed(
                task,
                guardian_decision=denied,
                token_verification=None,
                evidence_artifact_ids=["ev-task-it-health-001"],
            )

    def test_expired_token_blocks_approval_required_task(self):
        task = self._approval_task(
            task_id="task-email-draft-002",
            approval_request_id="apr-email-expired-001",
            approval_token_id="apt-email-expired-001",
            token_verification_id="tv-email-expired-001",
        )
        token = token_expired_example()
        task["guardian_decision_id"] = token["guardian_decision_id"]
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, self.bound_decision(task), token)

    def test_revoked_token_blocks_approval_required_task(self):
        task = self._approval_task(
            task_id="task-email-draft-003",
            approval_request_id="apr-email-revoked-001",
            approval_token_id="apt-email-revoked-001",
            token_verification_id="tv-email-revoked-001",
        )
        token = example("token.verification.revoked.example.json")
        task["guardian_decision_id"] = token["guardian_decision_id"]
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, self.bound_decision(task), token)

    def test_mismatched_token_scope_blocks_task(self):
        task = self._approval_task()
        token = token_valid_example()
        token["verification_result"] = "wrong_scope"
        token["scope_match_result"] = "mismatch"
        token["token_status_observed"] = "active"
        token["fail_closed"] = True
        token["can_proceed"] = False
        token["denial_reason"] = "Approved scope did not match presented scope."
        task["guardian_decision_id"] = token["guardian_decision_id"]
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, self.bound_decision(task), token)

    def test_stale_or_expired_guardian_decision_blocks_task(self):
        task = self.in_progress_task()
        decision = self.bound_decision(task)
        decision["expires_at"] = "2026-05-19T00:00:00Z"
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, decision)

        fresh_expiry = self.bound_decision(task)
        fresh_expiry["created_at"] = "2026-05-19T23:00:00Z"
        fresh_expiry["expires_at"] = "2026-05-20T00:10:00Z"
        with self.assertRaises(PolicyDenyError):
            self.queue.enqueue(task, fresh_expiry)

    def test_tainted_privileged_tool_invocation_denied(self):
        task = self.in_progress_task()
        tool = example("tool.invocation.tainted-input-denied.example.json")
        tool["tenant_id"] = task["tenant_id"]
        tool["customer_context_id"] = task["customer_context_id"]
        tool["task_id"] = task["task_id"]
        tool["actor"] = {"actor_type": "worker", "actor_id": self.worker.worker_id}
        tool["policy_result"] = "allow_with_evidence"
        tool["status"] = "approved_to_run"
        with self.assertRaises(PolicyDenyError):
            assert_tool_invocation_consistent(tool, task=task, worker=self.worker)

    def test_tainted_durable_memory_write_denied(self):
        task = self.in_progress_task()
        memory_access = example("memory.access.example.json")
        memory_access["task_id"] = task["task_id"]
        memory_access["access_type"] = "write_summary"
        memory_access["operation"] = "write_summary"
        memory_access["prompt_injection_scan_status"] = "suspected"
        memory_access["taint_ref_ids"] = ["taint-email-injection-001"]
        memory_access["policy_result"] = "allow_with_evidence"
        memory_access["status"] = "completed"
        with self.assertRaises(PolicyDenyError):
            assert_memory_access_consistent(memory_access, task=task)

    def test_lima_it_remediation_denied_in_mvp(self):
        remediation = example("lima_it.handoff.remediation-denied-mvp.example.json")
        assert_lima_it_handoff_consistent(remediation)
        unsafe = copy.deepcopy(remediation)
        unsafe["remediation_authorized"] = True
        with self.assertRaises(PolicyDenyError):
            assert_lima_it_handoff_consistent(unsafe)

    def test_lima_it_read_only_diagnostic_can_be_represented_safely(self):
        handoff = example("lima_it.handoff.example.json")
        assert_lima_it_handoff_consistent(handoff)

    def test_quarantined_worker_cannot_receive_task(self):
        self.registry.quarantine("arc-it-helper-01", "test")
        task = self.in_progress_task()
        with self.assertRaises(WorkerStateError):
            self.queue.enqueue(task, self.bound_decision(task))

    def test_revoked_worker_cannot_receive_task(self):
        self.registry.revoke("arc-it-helper-01", "test")
        task = self.in_progress_task()
        with self.assertRaises(WorkerStateError):
            self.queue.enqueue(task, self.bound_decision(task))

    def test_wrong_tenant_heartbeat_denied(self):
        heartbeat_service = HeartbeatService(self.registry, self.validator)
        heartbeat = heartbeat_example()
        heartbeat["worker_id"] = "arc-it-helper-01"
        heartbeat["tenant_id"] = "tenant-other"
        with self.assertRaises(WorkerStateError):
            heartbeat_service.accept(heartbeat)

    def test_worker_capability_mismatch_blocks_routing(self):
        registry = WorkerRegistry()
        registry.register_mock_worker(
            worker_id="arc-file-clerk-01",
            tenant_id="tenant-lab-001",
            role="file_clerk_arc_worker",
            capabilities=["document_read", "file_organize"],
        )
        queue = TaskQueue(registry, self.validator)
        task = self.in_progress_task()
        task["assigned_worker_id"] = "arc-file-clerk-01"
        with self.assertRaises(CrossContractInvariantError):
            queue.enqueue(task, self.bound_decision(task))

    def test_helper_scope_overreach_denied(self):
        helper_scope = example("helper.scope.it-helper-readonly.example.json")
        task = self.in_progress_task()
        task["required_tool_packs"] = ["draft_workspace"]
        with self.assertRaises(PolicyDenyError):
            assert_helper_scope_allows_task(helper_scope, task)

    def test_blocked_mvp_approval_result_cannot_authorize_tool_invocation(self):
        task = self.in_progress_task()
        tool = example("tool.invocation.tainted-input-denied.example.json")
        tool["tenant_id"] = task["tenant_id"]
        tool["customer_context_id"] = task["customer_context_id"]
        tool["task_id"] = task["task_id"]
        tool["actor"] = {"actor_type": "worker", "actor_id": self.worker.worker_id}
        tool["policy_result"] = "allow_with_evidence"
        tool["status"] = "approved_to_run"
        tool["approval_token_id"] = "apt-blocked-001"
        approval_result = example("approval.result.denied-blocked-mvp.example.json")
        with self.assertRaises(PolicyDenyError):
            assert_tool_invocation_consistent(tool, task=task, worker=self.worker, approval_result=approval_result)

    def _approval_task(
        self,
        *,
        task_id="task-email-draft-001",
        approval_request_id="apr-email-draft-001",
        approval_token_id="apt-email-draft-001",
        token_verification_id="tv-email-valid-001",
    ):
        task = self.in_progress_task()
        task.update(
            {
                "approval_required": True,
                "approval_request_id": approval_request_id,
                "approval_token_id": approval_token_id,
                "approval_result_id": "ar-phase1a-001",
                "token_verification_id": token_verification_id,
                "task_id": task_id,
            }
        )
        token = token_valid_example()
        if task_id == token["task_id"]:
            task["guardian_decision_id"] = token["guardian_decision_id"]
        return task


if __name__ == "__main__":
    unittest.main()
