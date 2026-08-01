"""In-memory mock Arc worker registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lima_office.runtime.errors import WorkerStateError


MAX_ARC_WORKERS = 8
ASSIGNABLE_STATES = {"registered", "healthy"}
BLOCKING_STATES = {"offline", "quarantined", "revoked", "replaced"}
ALLOWED_CAPABILITIES = {
    "document_read",
    "draft_workspace",
    "ticket_triage",
    "file_organize",
    "it_diagnostics_read_only",
    "mock_connector_readiness",
}


@dataclass
class WorkerRecord:
    worker_id: str
    tenant_id: str
    role: str
    capabilities: tuple[str, ...]
    state: str = "registered"
    policy_hash: str = "hash-ref-phase1a-policy"
    model_hash: str = "hash-ref-phase1a-model"
    heartbeat: dict[str, Any] | None = None
    missed_heartbeat_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def can_accept_task(self) -> bool:
        return self.state in ASSIGNABLE_STATES


class WorkerRegistry:
    """Stores mock worker records in memory only."""

    def __init__(self, max_workers: int = MAX_ARC_WORKERS) -> None:
        if max_workers < 1 or max_workers > MAX_ARC_WORKERS:
            raise WorkerStateError(f"worker registry max_workers must be 1-{MAX_ARC_WORKERS}")
        self.max_workers = max_workers
        self._workers: dict[str, WorkerRecord] = {}
        self._tenant_id: str | None = None

    def register_mock_worker(
        self,
        *,
        worker_id: str,
        tenant_id: str,
        role: str,
        capabilities: list[str] | tuple[str, ...],
        policy_hash: str = "hash-ref-phase1a-policy",
        model_hash: str = "hash-ref-phase1a-model",
    ) -> WorkerRecord:
        if not worker_id or not tenant_id:
            raise WorkerStateError("worker_id and tenant_id are required")
        if self._tenant_id is not None and tenant_id != self._tenant_id:
            raise WorkerStateError("Phase 1A registry supports one tenant at a time")
        unknown_capabilities = sorted(set(capabilities) - ALLOWED_CAPABILITIES)
        if unknown_capabilities:
            raise WorkerStateError(f"unknown worker capabilities: {', '.join(unknown_capabilities)}")
        if worker_id in self._workers:
            raise WorkerStateError(f"worker already registered: {worker_id}")
        if len(self._workers) >= self.max_workers:
            raise WorkerStateError(f"worker registry is limited to {self.max_workers} Arc workers")
        record = WorkerRecord(
            worker_id=worker_id,
            tenant_id=tenant_id,
            role=role,
            capabilities=tuple(capabilities),
            policy_hash=policy_hash,
            model_hash=model_hash,
        )
        self._workers[worker_id] = record
        self._tenant_id = tenant_id
        return record

    def get(self, worker_id: str) -> WorkerRecord:
        try:
            return self._workers[worker_id]
        except KeyError as exc:
            raise WorkerStateError(f"unknown worker: {worker_id}") from exc

    def require_worker(self, worker_id: str, tenant_id: str | None = None) -> WorkerRecord:
        worker = self.get(worker_id)
        if tenant_id is not None and worker.tenant_id != tenant_id:
            raise WorkerStateError("worker tenant mismatch")
        return worker

    def require_assignable(self, worker_id: str, tenant_id: str | None = None) -> WorkerRecord:
        worker = self.require_worker(worker_id, tenant_id)
        if worker.state in BLOCKING_STATES or not worker.can_accept_task():
            raise WorkerStateError(f"worker {worker_id} cannot accept tasks while {worker.state}")
        return worker

    def update_state(self, worker_id: str, state: str, reason: str | None = None) -> WorkerRecord:
        worker = self.get(worker_id)
        if worker.state == "revoked" and state != "revoked":
            raise WorkerStateError(f"worker {worker_id} cannot leave {worker.state} in Phase 1A scaffolding")
        if worker.state == "quarantined" and state not in {"quarantined", "revoked"}:
            raise WorkerStateError(f"worker {worker_id} cannot leave {worker.state} in Phase 1A scaffolding")
        worker.state = state
        if reason is not None:
            worker.metadata["state_reason"] = reason
        return worker

    def quarantine(self, worker_id: str, reason: str) -> WorkerRecord:
        return self.update_state(worker_id, "quarantined", reason)

    def revoke(self, worker_id: str, reason: str) -> WorkerRecord:
        return self.update_state(worker_id, "revoked", reason)

    def update_heartbeat(self, worker_id: str, heartbeat: dict[str, Any]) -> WorkerRecord:
        worker = self.require_worker(worker_id, heartbeat.get("tenant_id"))
        lifecycle_state = heartbeat.get("lifecycle_state")
        health_state = heartbeat.get("health_state")
        proposed_state = worker.state
        if lifecycle_state in {"quarantined", "revoked", "offline"}:
            proposed_state = lifecycle_state
        elif health_state in {"quarantined", "revoked", "offline"}:
            proposed_state = health_state
        else:
            proposed_state = lifecycle_state if isinstance(lifecycle_state, str) else worker.state
        if worker.state == "revoked" and proposed_state != "revoked":
            raise WorkerStateError(f"worker {worker_id} cannot leave {worker.state} from heartbeat")
        if worker.state == "quarantined" and proposed_state not in {"quarantined", "revoked"}:
            raise WorkerStateError(f"worker {worker_id} cannot leave {worker.state} from heartbeat")
        worker.state = proposed_state
        worker.heartbeat = heartbeat
        missed = heartbeat.get("missed_heartbeat_count")
        worker.missed_heartbeat_count = missed if isinstance(missed, int) else worker.missed_heartbeat_count
        return worker

    def summary(self) -> dict[str, Any]:
        return {
            "worker_count": len(self._workers),
            "max_workers": self.max_workers,
            "assignable_workers": sum(1 for worker in self._workers.values() if worker.can_accept_task()),
            "quarantined_workers": sum(1 for worker in self._workers.values() if worker.state == "quarantined"),
            "revoked_workers": sum(1 for worker in self._workers.values() if worker.state == "revoked"),
        }
