"""In-memory worker lifecycle simulator for the narrow Phase 1B slice."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import (
    UnsafeRuntimeActionError,
    WorkerLifecycleTransitionError,
    WorkerLifecycleValidationError,
)


LIFECYCLE_STATES = frozenset(
    {
        "provisioned",
        "enrolled",
        "active",
        "degraded",
        "quarantined",
        "revoked",
        "reenrollment_pending",
        "retired",
    }
)

ALLOWED_TRANSITIONS = {
    "provisioned": frozenset({"enrolled"}),
    "enrolled": frozenset({"active", "retired"}),
    "active": frozenset({"degraded", "quarantined", "revoked", "retired"}),
    "degraded": frozenset({"active", "quarantined", "revoked", "retired"}),
    "quarantined": frozenset({"reenrollment_pending", "revoked", "retired"}),
    "reenrollment_pending": frozenset({"enrolled", "revoked", "retired"}),
    "revoked": frozenset({"retired"}),
    "retired": frozenset(),
}

ACTIVE_BLOCKED_ATTESTATION = frozenset({"failed", "expired", "revoked", "blocked_mvp"})
ACTIVE_BLOCKED_TRUST = frozenset({"failed", "blocked_mvp"})


@dataclass(frozen=True)
class LifecycleTransition:
    worker_id: str
    tenant_id: str
    from_state: str | None
    to_state: str
    updated_at: str
    reason_codes: tuple[str, ...]


class WorkerLifecycleSimulator:
    """Validates worker deployment lifecycle metadata and simulates transitions."""

    def __init__(self, validator: ContractValidator) -> None:
        self.validator = validator
        self._current: dict[str, dict[str, Any]] = {}
        self._history: dict[str, list[LifecycleTransition]] = {}

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        deployment = self._validate_payload(payload)
        worker_id, tenant_id = self._required_identity(deployment)
        if worker_id in self._current:
            raise WorkerLifecycleTransitionError(f"worker already registered in simulator: {worker_id}")

        state = deployment["lifecycle_state"]
        self._ensure_known_state(state)
        if state == "active":
            self._ensure_active_is_safe(deployment)

        self._current[worker_id] = copy.deepcopy(deployment)
        self._history[worker_id] = [
            LifecycleTransition(
                worker_id=worker_id,
                tenant_id=tenant_id,
                from_state=None,
                to_state=state,
                updated_at=deployment["updated_at"],
                reason_codes=tuple(deployment.get("reason_codes", [])),
            )
        ]
        return self.snapshot(worker_id)

    def transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        deployment = self._validate_payload(payload)
        worker_id, tenant_id = self._required_identity(deployment)
        current = self._current.get(worker_id)
        if current is None:
            raise WorkerLifecycleTransitionError(f"unknown worker: {worker_id}")
        if current.get("tenant_id") != tenant_id:
            raise WorkerLifecycleTransitionError("worker tenant mismatch")

        from_state = current["lifecycle_state"]
        to_state = deployment["lifecycle_state"]
        self._ensure_known_state(from_state)
        self._ensure_known_state(to_state)

        if from_state == to_state:
            self._current[worker_id] = copy.deepcopy(deployment)
            self._record_transition(deployment, from_state=from_state, to_state=to_state)
            return self.snapshot(worker_id)

        if from_state == "revoked" and to_state == "active":
            raise WorkerLifecycleTransitionError("revoked worker cannot transition to active")
        if from_state == "retired" and to_state == "active":
            raise WorkerLifecycleTransitionError("retired worker cannot transition to active")
        if from_state == "quarantined" and to_state == "active":
            raise WorkerLifecycleTransitionError(
                "quarantined worker cannot transition directly to active; use reenrollment path"
            )

        allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
        if to_state not in allowed:
            raise WorkerLifecycleTransitionError(f"invalid lifecycle transition: {from_state} -> {to_state}")

        if to_state == "active":
            self._ensure_active_is_safe(deployment)
            self._ensure_reenrollment_gate(worker_id)

        self._current[worker_id] = copy.deepcopy(deployment)
        self._record_transition(deployment, from_state=from_state, to_state=to_state)
        return self.snapshot(worker_id)

    def snapshot(self, worker_id: str) -> dict[str, Any]:
        current = self._current.get(worker_id)
        if current is None:
            raise WorkerLifecycleTransitionError(f"unknown worker: {worker_id}")
        result = copy.deepcopy(current)
        result["authorization_allowed"] = False
        return result

    def history(self, worker_id: str) -> list[dict[str, Any]]:
        transitions = self._history.get(worker_id)
        if transitions is None:
            raise WorkerLifecycleTransitionError(f"unknown worker: {worker_id}")
        return [
            {
                "worker_id": transition.worker_id,
                "tenant_id": transition.tenant_id,
                "from_state": transition.from_state,
                "to_state": transition.to_state,
                "updated_at": transition.updated_at,
                "reason_codes": list(transition.reason_codes),
            }
            for transition in transitions
        ]

    def authorize_real_action(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("worker lifecycle simulator never authorizes real actions")

    def _validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.validator.validate(payload, "worker.deployment")
        except Exception as exc:  # pragma: no cover - explicit fail-closed mapping
            raise WorkerLifecycleValidationError(str(exc)) from exc

    @staticmethod
    def _required_identity(payload: dict[str, Any]) -> tuple[str, str]:
        worker_id = payload.get("worker_id")
        tenant_id = payload.get("tenant_id")
        if not isinstance(worker_id, str) or not worker_id:
            raise WorkerLifecycleValidationError("worker_id is required")
        if not isinstance(tenant_id, str) or not tenant_id:
            raise WorkerLifecycleValidationError("tenant_id is required")
        return worker_id, tenant_id

    @staticmethod
    def _ensure_known_state(state: str) -> None:
        if state not in LIFECYCLE_STATES:
            raise WorkerLifecycleTransitionError(f"unknown lifecycle state: {state}")

    def _ensure_active_is_safe(self, payload: dict[str, Any]) -> None:
        attestation_status = payload.get("attestation_status")
        trust_root_status = payload.get("trust_root_status")
        environment = payload.get("environment")
        reason_codes = set(payload.get("reason_codes", []))

        if attestation_status in ACTIVE_BLOCKED_ATTESTATION:
            raise WorkerLifecycleTransitionError(f"attestation status blocks active state: {attestation_status}")
        if trust_root_status in ACTIVE_BLOCKED_TRUST:
            raise WorkerLifecycleTransitionError(f"trust root status blocks active state: {trust_root_status}")
        if environment == "blocked_mvp":
            raise WorkerLifecycleTransitionError("blocked_mvp environment cannot transition to active")
        if "device_untrusted" in reason_codes or "model_route_device_untrusted" in reason_codes:
            raise WorkerLifecycleTransitionError("device untrusted metadata blocks active state")
        if "model_route_blocked_mvp" in reason_codes:
            raise WorkerLifecycleTransitionError("blocked_mvp reason code blocks active state")

    def _ensure_reenrollment_gate(self, worker_id: str) -> None:
        transitions = self._history.get(worker_id, [])
        if not transitions:
            return
        seen_quarantined = any(item.to_state == "quarantined" for item in transitions)
        if not seen_quarantined:
            return
        required_path = ("quarantined", "reenrollment_pending", "enrolled")
        compressed = [item.to_state for item in transitions if item.from_state != item.to_state]
        if compressed[-3:] != list(required_path):
            raise WorkerLifecycleTransitionError(
                "active transition requires quarantined -> reenrollment_pending -> enrolled path"
            )

    def _record_transition(self, payload: dict[str, Any], from_state: str | None, to_state: str) -> None:
        worker_id = payload["worker_id"]
        tenant_id = payload["tenant_id"]
        transition = LifecycleTransition(
            worker_id=worker_id,
            tenant_id=tenant_id,
            from_state=from_state,
            to_state=to_state,
            updated_at=payload["updated_at"],
            reason_codes=tuple(payload.get("reason_codes", [])),
        )
        self._history.setdefault(worker_id, []).append(transition)
