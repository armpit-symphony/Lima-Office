import copy
import socket
import unittest
from unittest.mock import patch

from helpers import example, has_jsonschema, validator
from lima_office.runtime.errors import (
    TaskLifecycleTransitionError,
    TaskLifecycleValidationError,
    UnsafeRuntimeActionError,
)
from lima_office.supervisor import TaskLifecycleSimulator


def worker_payload(state: str = "active") -> dict:
    payload = copy.deepcopy(example("worker.deployment.lightweight.example.json"))
    payload["worker_id"] = "arc-it-helper-01"
    payload["tenant_id"] = "tenant-lab-001"
    payload["lifecycle_state"] = state
    payload["environment"] = "phase0_lab"
    payload["reason_codes"] = []
    payload["attestation_status"] = "not_required_phase0"
    payload["trust_root_status"] = "software_only_placeholder"
    payload["blocked_reason"] = None
    payload["security_reviewer_ref"] = None
    payload["attestation_result_ref"] = None
    payload["privileged_task_metadata_allowed"] = False
    payload["risk_tier"] = "low"
    if state == "active":
        payload["install_state"] = "enrolled_mock"
    elif state == "enrolled":
        payload["install_state"] = "enrolled_mock"
    elif state == "quarantined":
        payload["install_state"] = "quarantined"
        payload["blocked_reason"] = "quarantine_triggered"
        payload["security_reviewer_ref"] = "security-reviewer-001"
        payload["risk_tier"] = "high"
    elif state == "revoked":
        payload["install_state"] = "blocked"
        payload["blocked_reason"] = "revoked"
        payload["risk_tier"] = "blocked"
    return payload


def guardian_allow(
    task_id: str,
    worker_id: str | None = "arc-it-helper-01",
    *,
    approval_bound: bool = False,
) -> dict:
    payload = copy.deepcopy(example("guardian.decision.allowed-one-time.example.json"))
    payload["decision_id"] = f"gd-{task_id}"
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["request_id"] = f"req-{task_id}"
    payload["valid_for_action_ref"] = f"scope-{task_id}"
    payload["decision_scope_hash"] = f"scope-{task_id}"
    payload["tenant_id"] = "tenant-lab-001"
    payload["customer_context_id"] = "customer-context-main"
    payload["subject"] = {"subject_type": "task", "subject_id": task_id}
    payload["bound_tenant_id"] = "tenant-lab-001"
    payload["bound_task_id"] = task_id
    payload["bound_worker_id"] = worker_id
    payload["bound_action_type"] = "form_preparation_review"
    payload["action_class"] = "tool_invocation"
    payload["approval_binding_id"] = f"bind-{task_id}" if approval_bound else None
    payload["binding_id"] = f"bind-{task_id}" if approval_bound else None
    payload["approval_chain_id"] = f"chain-{task_id}" if approval_bound else None
    payload["token_verification_id"] = f"tv-{task_id}" if approval_bound else None
    payload["evidence_artifact_id"] = f"ev-{task_id}-guardian"
    payload["evidence_artifact_ids"] = [f"ev-{task_id}-guardian", f"ev-{task_id}-task"]
    payload["evidence_refs"] = [f"ev-{task_id}-guardian", f"ev-{task_id}-task"]
    payload["post_action_evidence_refs"] = [f"ev-{task_id}-guardian"]
    payload["created_at"] = "2026-05-20T00:00:10Z"
    payload["issued_at"] = "2026-05-20T00:00:10Z"
    payload["effective_at"] = "2026-05-20T00:00:10Z"
    payload["expires_at"] = "2026-05-20T00:05:10Z"
    payload["decision_nonce"] = f"nonce-{task_id}"
    payload["replay_status"] = "unused"
    payload["replay_policy"] = "one_time"
    return payload


def token_valid(task_id: str) -> dict:
    payload = copy.deepcopy(example("token.verification.valid.example.json"))
    payload["token_verification_id"] = f"tv-{task_id}"
    payload["approval_token_id"] = f"apt-{task_id}"
    payload["approval_request_id"] = f"apr-{task_id}"
    payload["task_id"] = task_id
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["evidence_artifact_ids"] = [f"ev-{task_id}-token-verify"]
    return payload


def binding_valid(task_id: str) -> dict:
    payload = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
    payload["approval_chain_id"] = f"chain-{task_id}"
    payload["binding_id"] = f"bind-{task_id}"
    payload["approval_request_id"] = f"apr-{task_id}"
    payload["approval_result_id"] = f"apres-{task_id}"
    payload["approval_token_id"] = f"apt-{task_id}"
    payload["token_verification_id"] = f"tv-{task_id}"
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["task_id"] = task_id
    payload["tool_invocation_id"] = f"tool-{task_id}"
    payload["worker_id"] = "arc-it-helper-01"
    payload["evidence_refs"] = [f"ev-{task_id}-approval", f"ev-{task_id}-task"]
    payload["created_at"] = "2026-05-18T21:43:10Z"
    payload["checked_at"] = "2026-05-18T21:43:10Z"
    payload["expires_at"] = "2026-05-20T00:10:00Z"
    return payload


def task_payload(
    status: str,
    *,
    task_id: str = "task-it-health-001",
    approval_required: bool = False,
    task_class: str = "it_health_check",
    execution_mode: str = "mock_only",
    risk_tier: str = "medium",
    assigned_worker_id: str | None = None,
    evidence_refs: list[str] | None = None,
) -> dict:
    payload = copy.deepcopy(example("task.execution.example.json"))
    payload["task_id"] = task_id
    payload["status"] = status
    payload["task_class"] = task_class
    payload["execution_mode"] = execution_mode
    payload["risk_tier"] = risk_tier
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["approval_chain_id"] = f"chain-{task_id}"
    payload["binding_id"] = f"bind-{task_id}"
    payload["approval_request_id"] = f"apr-{task_id}" if approval_required else None
    payload["approval_result_id"] = f"apres-{task_id}" if approval_required else None
    payload["approval_token_id"] = f"apt-{task_id}" if approval_required else None
    payload["token_verification_id"] = f"tv-{task_id}" if approval_required else None
    payload["approval_required"] = approval_required
    payload["assigned_worker_id"] = assigned_worker_id
    payload["evidence_artifact_ids"] = evidence_refs if evidence_refs is not None else [f"ev-{task_id}-task"]
    payload["task_scope"]["external_effect"] = "none"
    payload["task_scope"]["allowed_actions"] = ["read_health_status", "summarize_diagnostics"]
    payload["task_scope"]["blocked_actions"] = [
        "run_remediation",
        "install_update_software",
        "touch_production_server",
    ]
    payload["failure_reason"] = None
    payload["operator_visible"] = False
    payload["blocked_reason_code"] = None
    payload["failure_code"] = None
    payload["evidence_failure_id"] = None
    payload["blocked_at"] = None
    payload["runbook_ref"] = None
    payload["incident_id"] = None

    if status == "needs_approval":
        payload["approval_required"] = True
        payload["approval_request_id"] = f"apr-{task_id}"
        payload["approval_result_id"] = None
        payload["approval_token_id"] = None
        payload["token_verification_id"] = None

    if status in {"assigned_to_worker", "accepted", "in_progress", "draft_ready", "completed_mock", "evidence_recorded"}:
        if payload["assigned_worker_id"] is None:
            payload["assigned_worker_id"] = "arc-it-helper-01"
    if status in {"blocked", "denied", "failed", "blocked_evidence_unavailable", "cancelled", "timed_out"}:
        payload["failure_reason"] = f"{status} in simulator"
        payload["operator_visible"] = True
    if status == "blocked_evidence_unavailable":
        payload["execution_mode"] = "approval_required_write"
        payload["approval_required"] = True
        payload["approval_request_id"] = f"apr-{task_id}"
        payload["approval_token_id"] = None
        payload["blocked_reason_code"] = "evidence_writer_unavailable"
        payload["failure_code"] = "evidence_failure"
        payload["evidence_failure_id"] = f"ef-{task_id}"
        payload["blocked_at"] = "2026-05-18T21:39:00Z"
        payload["runbook_ref"] = "docs/runbooks/evidence-writer-failure.md"
    if task_class == "blocked_mvp_action" or execution_mode == "blocked_mvp" or risk_tier == "blocked":
        payload["blocked_reason_code"] = "blocked_mvp"
    if status in {"completed_mock", "evidence_recorded"} and payload["approval_required"]:
        payload["approval_result_id"] = f"apres-{task_id}"
        payload["approval_token_id"] = f"apt-{task_id}"
        payload["token_verification_id"] = f"tv-{task_id}"

    return payload


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class TaskLifecycleSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.simulator = TaskLifecycleSimulator(self.validator)
        self.worker = worker_payload("active")

    def test_valid_task_examples_validate(self):
        self.validator.validate(example("task.execution.example.json"), "task.execution")
        self.validator.validate(example("task.execution.evidence-required-blocked.example.json"), "task.execution")

    def test_safe_lifecycle_path_passes(self):
        task_id = "task-safe-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        self.simulator.transition(task_payload("classified", task_id=task_id))
        self.simulator.transition(task_payload("needs_approval", task_id=task_id, approval_required=True))
        self.simulator.transition(
            task_payload("assigned_to_worker", task_id=task_id, approval_required=True),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id, approval_bound=True),
            approval_binding=binding_valid(task_id),
            token_verification=token_valid(task_id),
        )
        self.simulator.transition(
            task_payload("accepted", task_id=task_id, approval_required=True),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id, approval_bound=True),
            approval_binding=binding_valid(task_id),
            token_verification=token_valid(task_id),
        )
        self.simulator.transition(
            task_payload("in_progress", task_id=task_id, approval_required=True),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id, approval_bound=True),
            approval_binding=binding_valid(task_id),
            token_verification=token_valid(task_id),
        )
        result = self.simulator.transition(
            task_payload("completed_mock", task_id=task_id, approval_required=True),
            guardian_decision=guardian_allow(task_id, approval_bound=True),
            approval_binding=binding_valid(task_id),
            token_verification=token_valid(task_id),
        )
        self.assertEqual("completed_mock", result["status"])
        self.assertFalse(result["authorization_allowed"])
        self.assertFalse(result["execution_allowed"])

    def test_pending_guardian_to_denied_passes(self):
        task_id = "task-deny-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        self.simulator.transition(task_payload("classified", task_id=task_id))
        denied = self.simulator.transition(task_payload("denied", task_id=task_id))
        self.assertEqual("denied", denied["status"])

    def test_pending_approval_to_denied_passes(self):
        task_id = "task-deny-002"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        self.simulator.transition(task_payload("classified", task_id=task_id))
        self.simulator.transition(task_payload("needs_approval", task_id=task_id, approval_required=True))
        denied = self.simulator.transition(task_payload("denied", task_id=task_id, approval_required=True))
        self.assertEqual("denied", denied["status"])

    def test_in_progress_to_blocked_passes(self):
        task_id = "task-block-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        self.simulator.transition(task_payload("classified", task_id=task_id))
        self.simulator.transition(
            task_payload("assigned_to_worker", task_id=task_id),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id),
        )
        self.simulator.transition(
            task_payload("accepted", task_id=task_id),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id),
        )
        self.simulator.transition(
            task_payload("in_progress", task_id=task_id),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id),
        )
        blocked = self.simulator.transition(task_payload("blocked", task_id=task_id))
        self.assertEqual("blocked", blocked["status"])

    def test_in_progress_to_failed_passes(self):
        task_id = "task-fail-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        self.simulator.transition(task_payload("classified", task_id=task_id))
        self.simulator.transition(
            task_payload("assigned_to_worker", task_id=task_id),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id),
        )
        self.simulator.transition(
            task_payload("accepted", task_id=task_id),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id),
        )
        self.simulator.transition(
            task_payload("in_progress", task_id=task_id),
            worker_metadata=self.worker,
            guardian_decision=guardian_allow(task_id),
        )
        failed = self.simulator.transition(task_payload("failed", task_id=task_id))
        self.assertEqual("failed", failed["status"])

    def test_failed_to_cancelled_passes_schema_terminal(self):
        task_id = "task-fail-002"
        self.simulator.register(task_payload("failed", task_id=task_id))
        cancelled = self.simulator.transition(task_payload("cancelled", task_id=task_id))
        self.assertEqual("cancelled", cancelled["status"])

    def test_requested_to_completed_fails(self):
        task_id = "task-bad-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(task_payload("completed_mock", task_id=task_id))

    def test_denied_to_completed_fails(self):
        task_id = "task-bad-002"
        self.simulator.register(task_payload("denied", task_id=task_id))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(task_payload("completed_mock", task_id=task_id))

    def test_failed_to_completed_fails(self):
        task_id = "task-bad-003"
        self.simulator.register(task_payload("failed", task_id=task_id))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(task_payload("completed_mock", task_id=task_id))

    def test_blocked_mvp_to_assigned_or_completed_fails(self):
        task_id = "task-blocked-mvp-001"
        self.simulator.register(
            task_payload("blocked", task_id=task_id, task_class="blocked_mvp_action", execution_mode="blocked_mvp", risk_tier="blocked")
        )
        with self.assertRaises(TaskLifecycleValidationError):
            self.simulator.transition(
                task_payload(
                    "assigned_to_worker",
                    task_id=task_id,
                    task_class="blocked_mvp_action",
                    execution_mode="blocked_mvp",
                    risk_tier="blocked",
                )
            )
        with self.assertRaises(TaskLifecycleValidationError):
            self.simulator.transition(
                task_payload(
                    "completed_mock",
                    task_id=task_id,
                    task_class="blocked_mvp_action",
                    execution_mode="blocked_mvp",
                    risk_tier="blocked",
                )
            )

    def test_assignment_without_worker_ref_fails(self):
        task_id = "task-worker-ref-001"
        self.simulator.register(task_payload("needs_approval", task_id=task_id, approval_required=True))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(
                task_payload("assigned_to_worker", task_id=task_id, approval_required=True, assigned_worker_id=None),
                guardian_decision=guardian_allow(task_id, worker_id=None, approval_bound=True),
                approval_binding=binding_valid(task_id),
                token_verification=token_valid(task_id),
            )

    def test_tenant_mismatch_fails(self):
        task_id = "task-tenant-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        mismatched = task_payload("classified", task_id=task_id)
        mismatched["tenant_id"] = "tenant-other"
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(mismatched)

    def test_approval_required_without_binding_or_token_fails(self):
        task_id = "task-approval-001"
        self.simulator.register(task_payload("needs_approval", task_id=task_id, approval_required=True))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(
                task_payload("assigned_to_worker", task_id=task_id, approval_required=True),
                worker_metadata=self.worker,
                guardian_decision=guardian_allow(task_id, approval_bound=True),
            )

    def test_evidence_required_completion_without_evidence_refs_fails(self):
        task_id = "task-evidence-001"
        with self.assertRaises(TaskLifecycleValidationError):
            self.simulator.register(task_payload("completed_mock", task_id=task_id, evidence_refs=[]))

    def test_guardian_denied_blocks_assignment_and_completion(self):
        task_id = "task-guardian-denied-001"
        denied_decision = copy.deepcopy(example("guardian.decision.blocked-mvp.example.json"))
        denied_decision["tenant_id"] = "tenant-lab-001"
        denied_decision["customer_context_id"] = "customer-context-main"
        denied_decision["decision_id"] = f"gd-{task_id}"
        denied_decision["guardian_decision_id"] = f"gd-{task_id}"
        denied_decision["subject"] = {"subject_type": "task", "subject_id": task_id}

        self.simulator.register(task_payload("needs_approval", task_id=task_id, approval_required=True))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(
                task_payload("assigned_to_worker", task_id=task_id, approval_required=True),
                worker_metadata=self.worker,
                guardian_decision=denied_decision,
                approval_binding=binding_valid(task_id),
                token_verification=token_valid(task_id),
            )

    def test_stale_or_expired_guardian_blocks_assignment_or_completion(self):
        task_id = "task-stale-001"
        expired_guardian = guardian_allow(task_id, approval_bound=True)
        expired_guardian["expires_at"] = "2026-05-18T21:44:00Z"
        self.simulator.register(task_payload("needs_approval", task_id=task_id, approval_required=True))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(
                task_payload("assigned_to_worker", task_id=task_id, approval_required=True),
                worker_metadata=self.worker,
                guardian_decision=expired_guardian,
                approval_binding=binding_valid(task_id),
                token_verification=token_valid(task_id),
            )

    def test_external_send_live_connector_remediation_cannot_become_executable(self):
        for task_class, task_id in (
            ("external_message_send", "task-xsend-001"),
            ("remediation", "task-remed-001"),
        ):
            self.simulator.register(task_payload("classified", task_id=task_id, task_class=task_class))
            with self.assertRaises(TaskLifecycleTransitionError):
                self.simulator.transition(
                    task_payload("assigned_to_worker", task_id=task_id, task_class=task_class),
                    worker_metadata=self.worker,
                    guardian_decision=guardian_allow(task_id),
                )

        task_id = "task-live-connector-001"
        payload = task_payload("classified", task_id=task_id)
        payload["task_scope"]["allowed_actions"] = ["live_connector_write"]
        self.simulator.register(payload)
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(
                task_payload("assigned_to_worker", task_id=task_id),
                worker_metadata=self.worker,
                guardian_decision=guardian_allow(task_id, approval_bound=True),
            )

    def test_approval_required_write_execution_mode_cannot_become_executable(self):
        task_id = "task-write-mode-001"
        self.simulator.register(
            task_payload("classified", task_id=task_id, approval_required=True, execution_mode="approval_required_write")
        )
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(
                task_payload("assigned_to_worker", task_id=task_id, approval_required=True, execution_mode="approval_required_write"),
                worker_metadata=self.worker,
                guardian_decision=guardian_allow(task_id, approval_bound=True),
                approval_binding=binding_valid(task_id),
                token_verification=token_valid(task_id),
            )

    def test_unavailable_quarantined_or_revoked_worker_fails(self):
        task_id = "task-worker-state-001"
        self.simulator.register(task_payload("needs_approval", task_id=task_id, approval_required=True))
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(
                task_payload("assigned_to_worker", task_id=task_id, approval_required=True),
                worker_metadata=worker_payload("quarantined"),
                guardian_decision=guardian_allow(task_id, approval_bound=True),
                approval_binding=binding_valid(task_id),
                token_verification=token_valid(task_id),
            )

    def test_unknown_task_fails(self):
        with self.assertRaises(TaskLifecycleTransitionError):
            self.simulator.transition(task_payload("classified", task_id="task-unknown-001"))

    def test_history_is_in_memory_only(self):
        task_id = "task-history-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        self.simulator.transition(task_payload("classified", task_id=task_id))
        history = self.simulator.history(task_id)
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual("task_created", history[0]["to_state"])
        self.assertEqual("classified", history[-1]["to_state"])

    def test_simulator_never_writes_files(self):
        task_id = "task-file-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        with patch("pathlib.Path.write_text", side_effect=AssertionError("unexpected file write")):
            with patch("pathlib.Path.write_bytes", side_effect=AssertionError("unexpected file write")):
                self.simulator.transition(task_payload("classified", task_id=task_id))

    def test_simulator_never_calls_network(self):
        task_id = "task-net-001"
        self.simulator.register(task_payload("task_created", task_id=task_id))
        with patch.object(socket, "create_connection", side_effect=AssertionError("unexpected network call")):
            self.simulator.transition(task_payload("classified", task_id=task_id))

    def test_simulator_never_executes_tools(self):
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.execute_tools("task-001")

    def test_simulator_never_authorizes_real_actions(self):
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.authorize_real_action("task-001")


if __name__ == "__main__":
    unittest.main()
