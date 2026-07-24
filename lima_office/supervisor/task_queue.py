"""In-memory mock task queue with fail-closed assignment checks."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.evidence.writer import EvidenceWriter
from lima_office.guardian.policy import GuardianPolicy
from lima_office.runtime.invariants import (
    DEFAULT_REFERENCE_TIME,
    assert_guardian_decision_authorizes_task,
    assert_task_completion_allowed,
    assert_token_verification_authorizes_task,
    assert_worker_can_receive_task,
)
from lima_office.runtime.errors import EvidenceRequiredError, PolicyDenyError, UnsafeRuntimeActionError

from .worker_registry import WorkerRegistry


BLOCKED_EXECUTION_MODES = {"approval_required_write", "blocked_mvp"}
SAFE_TERMINAL_STATUSES = {"completed_mock", "evidence_recorded", "blocked", "denied", "failed", "cancelled", "timed_out"}
BLOCKED_TASK_ACTIONS = {
    "delete_file",
    "external_send",
    "install_update_software",
    "live_connector_write",
    "modify_customer_record",
    "payment_or_regulated_system",
    "production_remediation",
    "run_remediation",
    "send_external_message",
    "touch_production_server",
    "unrestricted_browser",
    "unrestricted_filesystem",
    "unrestricted_network",
    "use_regulated_system",
}


class TaskQueue:
    """Synchronous in-memory task records only; no tool execution."""

    def __init__(
        self,
        registry: WorkerRegistry,
        validator: ContractValidator,
        policy: GuardianPolicy | None = None,
        evidence_writer: EvidenceWriter | None = None,
        reference_time: str | None = DEFAULT_REFERENCE_TIME,
    ) -> None:
        self.registry = registry
        self.validator = validator
        self.policy = policy or GuardianPolicy()
        self.evidence_writer = evidence_writer
        self.reference_time = reference_time
        self._tasks: dict[str, dict[str, Any]] = {}
        self._token_verifications: dict[str, dict[str, Any]] = {}
        self._guardian_decisions: dict[str, dict[str, Any]] = {}

    def enqueue(
        self,
        payload: dict[str, Any],
        guardian_decision: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = self.validator.validate(payload, "task.execution")
        if guardian_decision is None:
            raise PolicyDenyError("Guardian decision is required before task assignment")
        guardian_decision = self.validator.validate(guardian_decision, "guardian.decision")
        assert_guardian_decision_authorizes_task(task, guardian_decision, reference_time=self.reference_time)

        task_id = task["task_id"]
        assigned_worker_id = task.get("assigned_worker_id")
        if isinstance(assigned_worker_id, str):
            worker = self.registry.require_assignable(assigned_worker_id, task.get("tenant_id"))
            assert_worker_can_receive_task(worker, task)
        verified_token = self._validate_token_if_required(task, token_verification, approval_binding)
        self._assert_safe_task(task)
        self._tasks[task_id] = copy.deepcopy(task)
        self._guardian_decisions[task_id] = copy.deepcopy(guardian_decision)
        if verified_token is not None:
            self._token_verifications[task_id] = copy.deepcopy(verified_token)
        return copy.deepcopy(task)

    def complete_mock(self, task_id: str, evidence_artifact_ids: list[str] | None = None) -> dict[str, Any]:
        task = self.get(task_id)
        assert_task_completion_allowed(
            task,
            guardian_decision=copy.deepcopy(self._guardian_decisions.get(task_id)),
            token_verification=copy.deepcopy(self._token_verifications.get(task_id)),
            evidence_artifact_ids=evidence_artifact_ids,
            reference_time=self.reference_time,
        )
        if self.evidence_writer is None:
            raise EvidenceRequiredError("mock completion requires an evidence writer to validate evidence refs")
        self.evidence_writer.require_evidence(
            evidence_artifact_ids,
            tenant_id=task.get("tenant_id"),
            subject_id=task_id,
            guardian_decision_id=self._guardian_decisions[task_id].get("decision_id"),
        )
        task["status"] = "completed_mock"
        task["evidence_artifact_ids"] = evidence_artifact_ids
        task = self.validator.validate(task, "task.execution")
        self._tasks[task_id] = copy.deepcopy(task)
        return copy.deepcopy(task)

    def get(self, task_id: str) -> dict[str, Any]:
        try:
            return copy.deepcopy(self._tasks[task_id])
        except KeyError as exc:
            raise UnsafeRuntimeActionError(f"unknown task: {task_id}") from exc

    def summary(self) -> dict[str, int]:
        return {
            "queue_depth": len(self._tasks),
            "blocked_tasks": sum(1 for task in self._tasks.values() if task.get("status") in {"blocked", "denied"}),
            "failed_tasks": sum(1 for task in self._tasks.values() if task.get("status") == "failed"),
        }

    def _assert_safe_task(self, task: dict[str, Any]) -> None:
        if task.get("execution_mode") in BLOCKED_EXECUTION_MODES:
            raise UnsafeRuntimeActionError("task execution mode is not mock/read-only safe")
        scope = task.get("task_scope") if isinstance(task.get("task_scope"), dict) else {}
        if scope.get("external_effect") not in {"none", "draft_only"}:
            raise UnsafeRuntimeActionError("task has out-of-scope external effect")
        blocked_actions = set(scope.get("blocked_actions", []))
        allowed_actions = set(scope.get("allowed_actions", []))
        unsafe_allowed = sorted(allowed_actions & BLOCKED_TASK_ACTIONS)
        if unsafe_allowed:
            raise UnsafeRuntimeActionError(f"task would imply blocked actions: {', '.join(unsafe_allowed)}")
        if task.get("status") in SAFE_TERMINAL_STATUSES and not task.get("evidence_artifact_ids"):
            raise EvidenceRequiredError("terminal task state requires evidence refs")
        if "run_remediation" not in blocked_actions:
            raise UnsafeRuntimeActionError("mock task must explicitly block remediation")
        if "install_update_software" not in blocked_actions:
            raise UnsafeRuntimeActionError("mock task must explicitly block software install/update")
        if "touch_production_server" not in blocked_actions:
            raise UnsafeRuntimeActionError("mock task must explicitly block production touch")

    def _validate_token_if_required(
        self,
        task: dict[str, Any],
        token_verification: dict[str, Any] | None,
        approval_binding: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not task.get("approval_required"):
            return None
        if token_verification is None:
            raise PolicyDenyError("approval-required task requires token verification metadata")
        verified = self.validator.validate(token_verification, "token.verification")
        if approval_binding is None:
            raise PolicyDenyError("approval-required task requires approval binding metadata")
        binding = self.validator.validate(approval_binding, "approval.binding")
        assert_token_verification_authorizes_task(
            task,
            verified,
            binding,
            reference_time=self.reference_time,
        )
        return verified
