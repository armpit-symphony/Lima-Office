"""In-memory task lifecycle simulator for the narrow Phase 1B slice."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import (
    PolicyDenyError,
    TaskLifecycleTransitionError,
    TaskLifecycleValidationError,
    UnsafeRuntimeActionError,
)
from lima_office.runtime.invariants import (
    DEFAULT_REFERENCE_TIME,
    assert_guardian_decision_replay_safe,
    assert_token_verification_authorizes_task,
)


TASK_STATES = frozenset(
    {
        "task_created",
        "classified",
        "assigned_to_worker",
        "accepted",
        "rejected",
        "in_progress",
        "needs_approval",
        "draft_ready",
        "blocked",
        "denied",
        "failed",
        "blocked_evidence_unavailable",
        "completed_mock",
        "evidence_recorded",
        "cancelled",
        "timed_out",
    }
)

ALLOWED_TRANSITIONS = {
    "task_created": frozenset({"classified", "blocked", "denied", "cancelled"}),
    "classified": frozenset({"needs_approval", "assigned_to_worker", "blocked", "denied", "cancelled"}),
    "needs_approval": frozenset({"assigned_to_worker", "denied", "timed_out", "cancelled"}),
    "assigned_to_worker": frozenset({"accepted", "rejected", "blocked", "denied", "cancelled"}),
    "accepted": frozenset({"in_progress", "blocked", "denied", "cancelled"}),
    "rejected": frozenset({"assigned_to_worker", "denied", "cancelled"}),
    "in_progress": frozenset({"draft_ready", "completed_mock", "blocked", "failed", "blocked_evidence_unavailable"}),
    "draft_ready": frozenset({"completed_mock", "blocked", "failed", "denied"}),
    "completed_mock": frozenset({"evidence_recorded"}),
    "blocked_evidence_unavailable": frozenset({"blocked", "denied", "cancelled"}),
    "blocked": frozenset({"needs_approval", "denied", "cancelled"}),
    "failed": frozenset({"cancelled"}),
    "timed_out": frozenset({"cancelled"}),
    "denied": frozenset(),
    "evidence_recorded": frozenset(),
    "cancelled": frozenset(),
}

EXECUTABLE_STATES = frozenset(
    {
        "assigned_to_worker",
        "accepted",
        "in_progress",
        "draft_ready",
        "completed_mock",
        "evidence_recorded",
    }
)

COMPLETION_STATES = frozenset({"completed_mock", "evidence_recorded"})
WORKER_REQUIRED_STATES = frozenset({"assigned_to_worker", "accepted", "in_progress", "draft_ready"})
WORKER_BLOCKED_STATES = frozenset({"quarantined", "revoked", "retired", "degraded"})

BLOCKED_MVP_TASK_CLASSES = frozenset({"blocked_mvp_action"})
BLOCKED_EXECUTION_TASK_CLASSES = frozenset({"external_message_send", "remediation"})
BLOCKED_EXECUTION_ACTIONS = frozenset(
    {"external_send", "send_external_message", "live_connector_write", "run_remediation"}
)
BLOCKED_EXECUTION_MODES = frozenset({"approval_required_write"})


@dataclass(frozen=True)
class TaskTransition:
    task_id: str
    tenant_id: str
    from_state: str | None
    to_state: str
    updated_at: str


class TaskLifecycleSimulator:
    """Validates task metadata and simulates lifecycle transitions in memory only."""

    def __init__(self, validator: ContractValidator, *, reference_time: str | None = DEFAULT_REFERENCE_TIME) -> None:
        self.validator = validator
        self.reference_time = reference_time
        self._current: dict[str, dict[str, Any]] = {}
        self._history: dict[str, list[TaskTransition]] = {}

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        task = self._validate_payload(payload)
        task_id, tenant_id = self._required_identity(task)
        if task_id in self._current:
            raise TaskLifecycleTransitionError(f"task already registered in simulator: {task_id}")
        state = task["status"]
        self._ensure_known_state(state)
        self._enforce_state_safety(task, state=state)
        self._current[task_id] = copy.deepcopy(task)
        self._history[task_id] = [
            TaskTransition(
                task_id=task_id,
                tenant_id=tenant_id,
                from_state=None,
                to_state=state,
                updated_at=task["updated_at"],
            )
        ]
        return self.snapshot(task_id)

    def transition(
        self,
        payload: dict[str, Any],
        *,
        worker_metadata: dict[str, Any] | None = None,
        guardian_decision: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = self._validate_payload(payload)
        task_id, tenant_id = self._required_identity(task)
        current = self._current.get(task_id)
        if current is None:
            raise TaskLifecycleTransitionError(f"unknown task: {task_id}")
        if current.get("tenant_id") != tenant_id:
            raise TaskLifecycleTransitionError("task tenant mismatch")

        from_state = current["status"]
        to_state = task["status"]
        self._ensure_known_state(from_state)
        self._ensure_known_state(to_state)

        if from_state != to_state:
            allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
            if to_state not in allowed:
                raise TaskLifecycleTransitionError(f"invalid task transition: {from_state} -> {to_state}")

        self._enforce_state_safety(
            task,
            state=to_state,
            worker_metadata=worker_metadata,
            guardian_decision=guardian_decision,
            approval_binding=approval_binding,
            token_verification=token_verification,
        )

        self._current[task_id] = copy.deepcopy(task)
        self._record_transition(task_id, tenant_id, from_state=from_state, to_state=to_state, updated_at=task["updated_at"])
        return self.snapshot(task_id)

    def snapshot(self, task_id: str) -> dict[str, Any]:
        current = self._current.get(task_id)
        if current is None:
            raise TaskLifecycleTransitionError(f"unknown task: {task_id}")
        result = copy.deepcopy(current)
        result["authorization_allowed"] = False
        result["execution_allowed"] = False
        return result

    def history(self, task_id: str) -> list[dict[str, Any]]:
        transitions = self._history.get(task_id)
        if transitions is None:
            raise TaskLifecycleTransitionError(f"unknown task: {task_id}")
        return [
            {
                "task_id": entry.task_id,
                "tenant_id": entry.tenant_id,
                "from_state": entry.from_state,
                "to_state": entry.to_state,
                "updated_at": entry.updated_at,
            }
            for entry in transitions
        ]

    def execute_tools(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("task lifecycle simulator never executes tools")

    def authorize_real_action(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("task lifecycle simulator never authorizes real actions")

    def _enforce_state_safety(
        self,
        task: dict[str, Any],
        *,
        state: str,
        worker_metadata: dict[str, Any] | None = None,
        guardian_decision: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
    ) -> None:
        if self._is_blocked_mvp_posture(task) and state in EXECUTABLE_STATES:
            raise TaskLifecycleTransitionError("blocked_mvp posture cannot enter executable task states")

        if self._is_prohibited_action_class(task) and state in EXECUTABLE_STATES:
            raise TaskLifecycleTransitionError("external_send/live_connector/remediation task class is blocked in MVP")

        if state in EXECUTABLE_STATES and task.get("execution_mode") in BLOCKED_EXECUTION_MODES:
            raise TaskLifecycleTransitionError("approval-required write execution mode is blocked in MVP simulator")

        if state in EXECUTABLE_STATES and self._has_prohibited_allowed_actions(task):
            raise TaskLifecycleTransitionError("task scope allowed_actions contains blocked MVP execution actions")

        if state in WORKER_REQUIRED_STATES:
            self._ensure_worker_ready(task, worker_metadata)

        if state in EXECUTABLE_STATES:
            self._ensure_guardian_allows(task, guardian_decision)

        if state in EXECUTABLE_STATES and task.get("approval_required"):
            self._ensure_approval_chain(task, approval_binding=approval_binding, token_verification=token_verification)

        if state in COMPLETION_STATES and not task.get("evidence_artifact_ids"):
            raise TaskLifecycleTransitionError("completion requires evidence_artifact_ids")

    def _ensure_guardian_allows(self, task: dict[str, Any], guardian_decision: dict[str, Any] | None) -> None:
        if guardian_decision is None:
            raise TaskLifecycleTransitionError("executable task transition requires guardian decision metadata")
        decision = self._validate_contract(guardian_decision, "guardian.decision")
        requested_action = {
            "tenant_id": task.get("tenant_id"),
            "customer_context_id": task.get("customer_context_id"),
            "task_id": task.get("task_id"),
            "worker_id": task.get("assigned_worker_id"),
            "guardian_decision_id": task.get("guardian_decision_id"),
            "binding_id": task.get("binding_id"),
            "approval_binding_id": task.get("binding_id"),
            "approval_chain_id": task.get("approval_chain_id"),
            "approval_request_id": task.get("approval_request_id"),
            "approval_result_id": task.get("approval_result_id"),
            "approval_token_id": task.get("approval_token_id"),
            "token_verification_id": task.get("token_verification_id"),
            "action_type": task.get("bound_action_type") or decision.get("bound_action_type") or "form_preparation_review",
            "tool_scope": task.get("bound_tool_scope") or decision.get("bound_tool_scope"),
            "decision_scope_hash": decision.get("decision_scope_hash"),
            "evidence_required": True,
            "evidence_refs": task.get("evidence_artifact_ids"),
        }
        try:
            assert_guardian_decision_replay_safe(
                decision,
                requested_action,
                reference_time=self.reference_time,
                consume_nonce=False,
            )
        except PolicyDenyError as exc:
            raise TaskLifecycleTransitionError(str(exc)) from exc

    def _ensure_approval_chain(
        self,
        task: dict[str, Any],
        *,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
    ) -> None:
        if approval_binding is None or token_verification is None:
            raise TaskLifecycleTransitionError("approval-required task transition requires approval binding and token verification")
        binding = self._validate_contract(approval_binding, "approval.binding")
        token = self._validate_contract(token_verification, "token.verification")
        try:
            assert_token_verification_authorizes_task(task, token, binding, reference_time=self.reference_time)
        except PolicyDenyError as exc:
            raise TaskLifecycleTransitionError(str(exc)) from exc

    def _ensure_worker_ready(self, task: dict[str, Any], worker_metadata: dict[str, Any] | None) -> None:
        worker_id = task.get("assigned_worker_id")
        if not isinstance(worker_id, str) or not worker_id:
            raise TaskLifecycleTransitionError("assigned_worker_id is required for executable task states")
        if worker_metadata is None:
            raise TaskLifecycleTransitionError("worker metadata is required before assignment/execution transitions")
        worker = self._validate_contract(worker_metadata, "worker.deployment")
        if worker.get("tenant_id") != task.get("tenant_id"):
            raise TaskLifecycleTransitionError("worker metadata tenant mismatch")
        if worker.get("worker_id") != worker_id:
            raise TaskLifecycleTransitionError("worker metadata does not match assigned_worker_id")
        lifecycle_state = worker.get("lifecycle_state")
        if lifecycle_state in WORKER_BLOCKED_STATES:
            raise TaskLifecycleTransitionError(f"worker lifecycle blocks assignment: {lifecycle_state}")
        if lifecycle_state not in {"active", "enrolled"}:
            raise TaskLifecycleTransitionError(f"worker lifecycle is not assignable: {lifecycle_state}")

    def _validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._validate_contract(payload, "task.execution")

    def _validate_contract(self, payload: dict[str, Any], schema_ref: str) -> dict[str, Any]:
        try:
            return self.validator.validate(payload, schema_ref)
        except Exception as exc:  # pragma: no cover - explicit fail-closed mapping
            raise TaskLifecycleValidationError(str(exc)) from exc

    @staticmethod
    def _required_identity(payload: dict[str, Any]) -> tuple[str, str]:
        task_id = payload.get("task_id")
        tenant_id = payload.get("tenant_id")
        if not isinstance(task_id, str) or not task_id:
            raise TaskLifecycleValidationError("task_id is required")
        if not isinstance(tenant_id, str) or not tenant_id:
            raise TaskLifecycleValidationError("tenant_id is required")
        return task_id, tenant_id

    @staticmethod
    def _ensure_known_state(state: str) -> None:
        if state not in TASK_STATES:
            raise TaskLifecycleTransitionError(f"unknown task state: {state}")

    @staticmethod
    def _is_blocked_mvp_posture(task: dict[str, Any]) -> bool:
        return (
            task.get("task_class") in BLOCKED_MVP_TASK_CLASSES
            or task.get("execution_mode") == "blocked_mvp"
            or task.get("risk_tier") == "blocked"
            or task.get("environment") == "blocked_mvp"
        )

    @staticmethod
    def _is_prohibited_action_class(task: dict[str, Any]) -> bool:
        return task.get("task_class") in BLOCKED_EXECUTION_TASK_CLASSES

    @staticmethod
    def _has_prohibited_allowed_actions(task: dict[str, Any]) -> bool:
        scope = task.get("task_scope")
        if not isinstance(scope, dict):
            return False
        allowed_actions = scope.get("allowed_actions", [])
        if not isinstance(allowed_actions, list):
            return False
        return bool(set(allowed_actions) & BLOCKED_EXECUTION_ACTIONS)

    def _record_transition(self, task_id: str, tenant_id: str, *, from_state: str | None, to_state: str, updated_at: str) -> None:
        self._history.setdefault(task_id, []).append(
            TaskTransition(
                task_id=task_id,
                tenant_id=tenant_id,
                from_state=from_state,
                to_state=to_state,
                updated_at=updated_at,
            )
        )
