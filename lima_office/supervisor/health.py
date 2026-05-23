"""Metadata-only supervisor health summaries for Phase 1A mock runtime."""

from __future__ import annotations

import copy
import re
from collections import Counter
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.guardian.decision import FIXED_CREATED_AT
from lima_office.supervisor.task_queue import TaskQueue
from lima_office.supervisor.worker_registry import WorkerRegistry


STALE_HEARTBEAT_SECONDS = 180


class SupervisorHealthReporter:
    """Builds supervisor.health-shaped in-memory payloads.

    The reporter summarizes contract metadata only. It never reads customer
    payloads, never sends telemetry, and never monitors production systems.
    """

    def __init__(
        self,
        validator: ContractValidator,
        *,
        supervisor_id: str = "supervisor-lab-001",
        tenant_id: str = "tenant-lab-001",
        customer_context_id: str = "customer-context-main",
    ) -> None:
        self.validator = validator
        self.supervisor_id = supervisor_id
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id

    def build(
        self,
        *,
        registry: WorkerRegistry,
        task_queue: TaskQueue | None = None,
        evidence_writer: Any | None = None,
        guardian_decisions: list[dict[str, Any]] | None = None,
        mode: str = "mock",
    ) -> dict[str, Any]:
        workers = list(getattr(registry, "_workers", {}).values())
        tasks = list(getattr(task_queue, "_tasks", {}).values()) if task_queue is not None else []
        stored_decisions = (
            list(getattr(task_queue, "_guardian_decisions", {}).values()) if task_queue is not None else []
        )
        decisions = [*stored_decisions, *(guardian_decisions or [])]
        evidence_failures = list(getattr(evidence_writer, "_failures", {}).values()) if evidence_writer is not None else []
        evidence_artifacts = list(getattr(evidence_writer, "_artifacts", {}).values()) if evidence_writer is not None else []

        worker_state_counts = Counter(worker.state for worker in workers)
        task_state_counts = Counter(task.get("status", "unknown") for task in tasks)
        guardian_decision_counts = Counter(decision.get("decision", "unknown") for decision in decisions)
        evidence_status_counts = self._evidence_counts(evidence_writer, evidence_artifacts, evidence_failures)

        stale_heartbeat_count = sum(1 for worker in workers if self._worker_is_stale(worker))
        quarantined_worker_count = worker_state_counts.get("quarantined", 0)
        revoked_worker_count = worker_state_counts.get("revoked", 0)
        blocked_task_count = sum(1 for task in tasks if task.get("status") in {"blocked", "denied", "blocked_evidence_unavailable"})
        denied_action_count = sum(
            1
            for decision in decisions
            if decision.get("decision") in {"deny", "block_mvp", "quarantine_subject"}
        )

        reasons: list[str] = []
        if stale_heartbeat_count:
            reasons.append("worker_stale")
        if quarantined_worker_count:
            reasons.append("worker_quarantined")
        if revoked_worker_count:
            reasons.append("worker_revoked")
        if evidence_status_counts.get("failed", 0):
            reasons.append("evidence_writer_degraded")
        if blocked_task_count:
            reasons.append("task_blocked")
        if denied_action_count:
            reasons.append("guardian_denied")

        degraded_component_count = sum(
            1
            for condition in (
                stale_heartbeat_count,
                evidence_status_counts.get("degraded", 0),
                evidence_status_counts.get("failed", 0),
            )
            if condition
        )
        blocked_conditions = [
            quarantined_worker_count,
            revoked_worker_count,
            blocked_task_count,
            denied_action_count,
            sum(1 for failure in evidence_failures if failure.get("pre_action_blocked")),
        ]
        if any(blocked_conditions):
            health_status = "blocked"
        elif degraded_component_count:
            health_status = "degraded"
        else:
            health_status = "healthy"

        payload = {
            "contract_name": "supervisor.health",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": "corr-supervisor-health-001",
            "causation_id": None,
            "idempotency_key": "idem-supervisor-health-001",
            "producer": {"component": "supervisor", "produced_at": FIXED_CREATED_AT},
            "supervisor_id": self.supervisor_id,
            "generated_at": FIXED_CREATED_AT,
            "mode": mode,
            "worker_count": len(workers),
            "worker_state_counts": dict(sorted(worker_state_counts.items())),
            "task_state_counts": dict(sorted(task_state_counts.items())),
            "guardian_decision_counts": dict(sorted(guardian_decision_counts.items())),
            "evidence_status_counts": dict(sorted(evidence_status_counts.items())),
            "stale_heartbeat_count": stale_heartbeat_count,
            "quarantined_worker_count": quarantined_worker_count,
            "revoked_worker_count": revoked_worker_count,
            "blocked_task_count": blocked_task_count,
            "denied_action_count": denied_action_count,
            "degraded_component_count": degraded_component_count,
            "health_status": health_status,
            "reasons": reasons,
            "evidence_refs": self._refs_from_artifacts(evidence_artifacts),
            "policy_refs": ["policy-phase1a-invariants-v2"],
            "related_contract_refs": self._related_refs(workers, tasks, decisions),
            "data_classification": "internal",
            "redaction_level": "metadata_only",
            "raw_customer_content_present": False,
            "secret_material_present": False,
            "policy_version": "policy-phase1a-invariants-v2",
        }
        self._assert_metadata_only(payload)
        return copy.deepcopy(self.validator.validate(payload, "supervisor.health"))

    @staticmethod
    def _worker_is_stale(worker: Any) -> bool:
        heartbeat = getattr(worker, "heartbeat", None)
        if not isinstance(heartbeat, dict):
            return False
        age = heartbeat.get("heartbeat_age_seconds")
        return isinstance(age, int) and age > STALE_HEARTBEAT_SECONDS

    @staticmethod
    def _evidence_counts(
        evidence_writer: Any | None,
        artifacts: list[dict[str, Any]],
        failures: list[dict[str, Any]],
    ) -> Counter:
        counts: Counter = Counter()
        if evidence_writer is None:
            counts["not_configured"] = 1
            return counts
        summary = evidence_writer.health_summary() if hasattr(evidence_writer, "health_summary") else {}
        status = summary.get("evidence_writer_status", "healthy")
        counts[status] += 1
        counts["artifact_recorded"] += len(artifacts)
        counts["failure_recorded"] += len(failures)
        if any(failure.get("post_action_degraded") for failure in failures):
            counts["degraded"] += 1
        return counts

    @staticmethod
    def _refs_from_artifacts(artifacts: list[dict[str, Any]]) -> list[str]:
        return sorted(artifact["artifact_id"] for artifact in artifacts if isinstance(artifact.get("artifact_id"), str))

    @staticmethod
    def _related_refs(workers: list[Any], tasks: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[str]:
        refs = [f"worker:{worker.worker_id}" for worker in workers]
        refs.extend(f"task:{task['task_id']}" for task in tasks if isinstance(task.get("task_id"), str))
        refs.extend(
            f"guardian.decision:{decision['decision_id']}"
            for decision in decisions
            if isinstance(decision.get("decision_id"), str)
        )
        return sorted(set(refs))

    @staticmethod
    def _assert_metadata_only(payload: dict[str, Any]) -> None:
        encoded = repr(payload)
        secret_patterns = (
            re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
            re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{20,}\b"),
            re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
            re.compile(r"(?i)\b(password|secret_value|private_key|api_key)\b"),
        )
        if any(pattern.search(encoded) for pattern in secret_patterns):
            from lima_office.runtime.errors import UnsafeRuntimeActionError

            raise UnsafeRuntimeActionError("supervisor health payload cannot include secret-like material")
