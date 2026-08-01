"""Validated worker heartbeat intake."""

from __future__ import annotations

from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import WorkerStateError

from .worker_registry import WorkerRegistry


STALE_HEARTBEAT_SECONDS = 180


class HeartbeatService:
    """Validates heartbeat payloads and updates the active registry view."""

    def __init__(
        self,
        registry: WorkerRegistry,
        validator: ContractValidator,
        *,
        require_authenticated: bool = False,
    ) -> None:
        self.registry = registry
        self.validator = validator
        self.require_authenticated = require_authenticated
        self.stale_threshold_seconds = STALE_HEARTBEAT_SECONDS

    def accept(self, payload: dict[str, Any]) -> dict[str, Any]:
        heartbeat = self.validator.validate(payload, "worker.heartbeat")
        worker_id = heartbeat.get("worker_id")
        if not isinstance(worker_id, str):
            raise WorkerStateError("heartbeat worker_id is required")
        worker = self.registry.require_worker(worker_id, heartbeat.get("tenant_id"))
        if self.require_authenticated and not worker.authenticated:
            raise WorkerStateError("unauthenticated worker heartbeat is forbidden")
        if heartbeat.get("worker_id") != worker.worker_id:
            raise WorkerStateError("heartbeat worker identity mismatch")
        self.registry.update_heartbeat(worker_id, heartbeat)
        if self.is_stale(heartbeat):
            self.registry.update_state(worker_id, "offline", "stale_heartbeat")
            raise WorkerStateError("stale heartbeat blocks assignment")
        if heartbeat.get("guardian_reachability") != "reachable":
            self.registry.quarantine(worker_id, "guardian_unreachable")
            raise WorkerStateError("guardian-unreachable heartbeat blocks assignment")
        if heartbeat.get("evidence_writer_status") == "failed":
            self.registry.quarantine(worker_id, "evidence_writer_failed")
            raise WorkerStateError("evidence-writer failure blocks assignment")
        if heartbeat.get("evidence_writer_status") == "degraded":
            self.registry.update_state(worker_id, "degraded", "evidence_writer_degraded")
        return heartbeat

    def is_stale(self, heartbeat: dict[str, Any]) -> bool:
        age = heartbeat.get("heartbeat_age_seconds")
        return isinstance(age, int) and age > self.stale_threshold_seconds
