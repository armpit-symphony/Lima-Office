"""Authenticated worker registration and heartbeat ingestion for the lab Supervisor."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from lima_office.contracts.validator import ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.runtime.errors import EvidenceWriteError, WorkerStateError

from .heartbeat import HeartbeatService
from .worker_channel import payload_hash
from .worker_client import AuthenticatedArcWorkerClient
from .worker_registry import WorkerRecord, WorkerRegistry


class AuthenticatedWorkerLifecycleService:
    """Poll and persist one-to-eight authenticated Arc worker identities."""

    def __init__(
        self,
        *,
        tenant_id: str,
        customer_context_id: str,
        policy_version: str,
        validator: ContractValidator,
        registry: WorkerRegistry,
        evidence_store: SQLiteEvidenceStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.policy_version = policy_version
        self.validator = validator
        self.registry = registry
        self.evidence_store = evidence_store
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.heartbeat_service = HeartbeatService(
            registry,
            validator,
            require_authenticated=True,
        )

    def register(
        self,
        client: AuthenticatedArcWorkerClient,
    ) -> WorkerRecord:
        registration = client.request_registration()
        self._assert_registration_binding(client, registration)
        record = self.registry.register_authenticated_worker(
            worker_id=registration["worker_id"],
            tenant_id=registration["tenant_id"],
            role=registration["worker_role"],
            capabilities=registration["capabilities"],
            channel_identity_ref=registration["channel_identity_ref"],
            boot_id=registration["boot_id"],
            worker_version=registration["worker_version"],
            policy_hash=registration["policy_version"],
        )
        try:
            self._persist_record(record)
            self.evidence_store.append_event(
                self._event(
                    event_type="worker_registration",
                    worker_id=record.worker_id,
                    request_id=registration["registration_id"],
                    payload=registration,
                    outcome="acknowledged",
                    summary="Authenticated Arc worker registration persisted.",
                )
            )
        except EvidenceWriteError:
            self.registry.quarantine(
                record.worker_id,
                "worker_registration_evidence_failed",
            )
            raise
        return record

    def heartbeat(
        self,
        client: AuthenticatedArcWorkerClient,
    ) -> WorkerRecord:
        heartbeat = self._normalize_heartbeat(client.request_heartbeat())
        worker = self.registry.require_worker(
            heartbeat["worker_id"],
            heartbeat["tenant_id"],
        )
        if not worker.authenticated:
            raise WorkerStateError(
                "worker heartbeat requires authenticated registration"
            )
        if worker.channel_identity_ref != client.channel.key_id:
            raise WorkerStateError("heartbeat channel identity mismatch")
        self.heartbeat_service.accept(heartbeat)
        try:
            self._persist_record(worker)
            self.evidence_store.append_event(
                self._event(
                    event_type="worker_heartbeat",
                    worker_id=worker.worker_id,
                    request_id=heartbeat["heartbeat_id"],
                    payload=heartbeat,
                    outcome="received",
                    summary="Authenticated Arc worker heartbeat persisted.",
                )
            )
        except EvidenceWriteError:
            self.registry.quarantine(
                worker.worker_id,
                "worker_heartbeat_evidence_failed",
            )
            raise
        return worker

    def _normalize_heartbeat(
        self,
        heartbeat: dict[str, Any],
    ) -> dict[str, Any]:
        expected = {
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "policy_version": self.policy_version,
        }
        if any(heartbeat.get(key) != value for key, value in expected.items()):
            raise WorkerStateError(
                "heartbeat tenant, customer context, or policy binding mismatch"
            )
        if heartbeat.get("producer", {}).get("component") != "worker":
            raise WorkerStateError("heartbeat producer mismatch")
        try:
            reported_at = datetime.fromisoformat(
                str(heartbeat["reported_at"]).replace("Z", "+00:00")
            ).astimezone(timezone.utc)
        except (KeyError, TypeError, ValueError) as exc:
            raise WorkerStateError("heartbeat reported_at is invalid") from exc
        received_at = self.clock()
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)
        received_at = received_at.astimezone(timezone.utc)
        if reported_at > received_at:
            raise WorkerStateError(
                "heartbeat reported_at cannot be in the Supervisor's future"
            )
        normalized = dict(heartbeat)
        normalized["supervisor_received_at"] = received_at.isoformat().replace(
            "+00:00",
            "Z",
        )
        normalized["heartbeat_age_seconds"] = int(
            (received_at - reported_at).total_seconds()
        )
        return self.validator.validate(normalized, "worker.heartbeat")

    def restore(self) -> list[WorkerRecord]:
        restored: list[WorkerRecord] = []
        for payload in self.evidence_store.worker_records(self.tenant_id):
            restored.append(self.registry.restore_authenticated_worker(payload))
        return restored

    def _assert_registration_binding(
        self,
        client: AuthenticatedArcWorkerClient,
        registration: dict[str, Any],
    ) -> None:
        expected = {
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "worker_id": client.channel.worker_id,
            "channel_identity_ref": client.channel.key_id,
            "policy_version": self.policy_version,
        }
        mismatches = [
            key for key, value in expected.items() if registration.get(key) != value
        ]
        if mismatches:
            raise WorkerStateError(
                "worker registration identity or policy binding mismatch"
            )
        if registration["producer"]["component"] != "worker":
            raise WorkerStateError("worker registration producer mismatch")
        if registration.get("runtime_authority_blocked") is not True:
            raise WorkerStateError("worker registration must block runtime authority")
        if any(
            registration.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise WorkerStateError(
                "worker registration cannot authorize execution"
            )

    def _persist_record(self, worker: WorkerRecord) -> None:
        self.evidence_store.upsert_worker_record(
            worker.to_record(updated_at=self._now())
        )

    def _event(
        self,
        *,
        event_type: str,
        worker_id: str,
        request_id: str,
        payload: dict[str, Any],
        outcome: str,
        summary: str,
    ) -> dict[str, Any]:
        now = self._now()
        return {
            "contract_name": "control_plane.event",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{request_id}",
            "causation_id": None,
            "idempotency_key": f"event:{event_type}:{request_id}",
            "producer": {"component": "supervisor", "produced_at": now},
            "policy_version": self.policy_version,
            "event_id": f"ev-worker:{uuid4().hex}",
            "event_type": event_type,
            "actor_id": f"worker:{worker_id}",
            "worker_id": worker_id,
            "request_id": request_id,
            "decision_id": None,
            "guardian_decision_id": None,
            "parent_event_id": None,
            "payload_hash": payload_hash(payload),
            "redacted_summary": summary,
            "outcome": outcome,
            "reason_codes": [],
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
            "created_at": now,
        }

    def _now(self) -> str:
        value = self.clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
