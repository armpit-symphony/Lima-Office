"""In-memory mock task queue with fail-closed assignment checks."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.evidence.writer import EvidenceWriter
from lima_office.guardian.policy import GuardianPolicy
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
    ) -> None:
        self.registry = registry
        self.validator = validator
        self.policy = policy or GuardianPolicy()
        self.evidence_writer = evidence_writer
        self._tasks: dict[str, dict[str, Any]] = {}
        self._token_verifications: dict[str, dict[str, Any]] = {}

    def enqueue(
        self,
        payload: dict[str, Any],
        guardian_decision: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = self.validator.validate(payload, "task.execution")
        if guardian_decision is None:
            raise PolicyDenyError("Guardian decision is required before task assignment")
        guardian_decision = self.validator.validate(guardian_decision, "guardian.decision")
        if guardian_decision.get("decision") not in {"allow", "allow_with_evidence"}:
            raise PolicyDenyError(guardian_decision.get("denial_reason") or "Guardian denied task assignment")
        if guardian_decision.get("tenant_id") != task.get("tenant_id"):
            raise PolicyDenyError("Guardian decision tenant mismatch")
        if guardian_decision.get("decision_id") != task.get("guardian_decision_id"):
            raise PolicyDenyError("Guardian decision is not bound to task guardian_decision_id")

        task_id = task["task_id"]
        assigned_worker_id = task.get("assigned_worker_id")
        if isinstance(assigned_worker_id, str):
            self.registry.require_assignable(assigned_worker_id, task.get("tenant_id"))
        verified_token = self._validate_token_if_required(task, token_verification)
        self._assert_safe_task(task)
        self._tasks[task_id] = copy.deepcopy(task)
        if verified_token is not None:
            self._token_verifications[task_id] = copy.deepcopy(verified_token)
        return copy.deepcopy(task)

    def complete_mock(self, task_id: str, evidence_artifact_ids: list[str] | None = None) -> dict[str, Any]:
        task = self.get(task_id)
        if task.get("approval_required") and task_id not in self._token_verifications:
            raise PolicyDenyError("approval-required task cannot complete without approved token metadata")
        if not evidence_artifact_ids:
            raise EvidenceRequiredError("mock completion requires evidence artifact refs")
        if self.evidence_writer is not None:
            self.evidence_writer.require_evidence(evidence_artifact_ids)
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
    ) -> dict[str, Any] | None:
        if not task.get("approval_required"):
            return None
        if token_verification is None:
            raise PolicyDenyError("approval-required task requires token verification metadata")
        verified = self.validator.validate(token_verification, "token.verification")
        if verified.get("tenant_id") != task.get("tenant_id"):
            raise PolicyDenyError("token verification tenant mismatch")
        if verified.get("task_id") != task.get("task_id"):
            raise PolicyDenyError("token verification task mismatch")
        if verified.get("approval_token_id") != task.get("approval_token_id"):
            raise PolicyDenyError("token verification approval token mismatch")
        if verified.get("verification_result") != "valid" or verified.get("can_proceed") is not True:
            raise PolicyDenyError(verified.get("denial_reason") or "token verification failed closed")
        return verified
