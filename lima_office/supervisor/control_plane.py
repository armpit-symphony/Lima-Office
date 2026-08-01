"""Guardian-mandatory, non-executing Supervisor-to-Arc control-plane slice."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from lima_office.contracts.validator import ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.guardian.authority import GuardianAuthority
from lima_office.runtime.errors import (
    ContractValidationError,
    PolicyDenyError,
    UnsafeRuntimeActionError,
    WorkerStateError,
)

from .arc_worker import ArcWorkerPreviewEndpoint
from .worker_registry import WorkerRegistry


ACTION_CATEGORIES = {
    "safe_read": "informational",
    "status": "informational",
    "external_write": "external_write",
    "shell": "shell",
    "credential_access": "credential_access",
    "file_mutation": "file_mutation",
    "unknown": "unknown",
}
ACTION_CAPABILITIES = {
    "safe_read": "document_read",
    "status": "it_diagnostics_read_only",
    "external_write": "draft_workspace",
    "file_mutation": "file_organize",
}
CALLER_FIELDS = frozenset(
    {
        "request_id",
        "tenant_id",
        "actor_id",
        "action",
        "resource_type",
        "resource_id",
        "worker_id",
        "idempotency_key",
    }
)
LIMA_GUARDIAN_SOURCE_POLICY = "guardian_core.policy"


def load_lima_runner() -> Callable[[dict[str, Any]], Any] | None:
    """Load only the supported LIMA API; absence is handled fail closed."""

    try:
        from lima.runtime import run_governed_request
    except (ImportError, ModuleNotFoundError):
        return None
    return run_governed_request


class SupervisorControlPlane:
    """Process one structured request through Guardian, LIMA, evidence, and Arc."""

    def __init__(
        self,
        *,
        tenant_id: str,
        customer_context_id: str,
        authenticated_actors: Mapping[str, str],
        validator: ContractValidator,
        registry: WorkerRegistry,
        evidence_store: SQLiteEvidenceStore,
        guardian_authority: GuardianAuthority,
        lima_runner: Callable[[dict[str, Any]], Any] | None,
        worker_endpoints: Mapping[str, ArcWorkerPreviewEndpoint],
        policy_version: str = "guardian-policy-lab-v1",
        require_authenticated_workers: bool = False,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not tenant_id or not customer_context_id:
            raise ValueError("tenant and customer context are required")
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.authenticated_actors = dict(authenticated_actors)
        self.validator = validator
        self.registry = registry
        self.evidence_store = evidence_store
        self.guardian_authority = guardian_authority
        self.lima_runner = lima_runner
        self.worker_endpoints = dict(worker_endpoints)
        self.policy_version = policy_version
        self.require_authenticated_workers = require_authenticated_workers
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def submit(self, raw_request: Mapping[str, Any]) -> dict[str, Any]:
        """Run the entire request synchronously and stop before execution."""

        request = self._normalize_request(raw_request)
        if not self.evidence_store.reserve_request(request):
            event = self._event(
                request,
                event_type="replay_rejected",
                component="supervisor",
                outcome="denied",
                summary="Duplicate request or idempotency identity rejected.",
                reason_codes=["nonce_replay_denied"],
            )
            self.evidence_store.append_event(event)
            return self._result(request, status="denied", reason_codes=["nonce_replay_denied"])

        request_event = self.evidence_store.append_event(
            self._event(
                request,
                event_type="request_received",
                component="supervisor",
                outcome="received",
                summary="Authenticated structured operator request received.",
            )
        )
        guardian_request = self._guardian_request(request, request_event["event_id"])
        guardian_request_event = self.evidence_store.append_event(
            self._event(
                request,
                event_type="guardian_request",
                component="supervisor",
                outcome="received",
                summary="Request-bound Guardian evaluation requested.",
                parent_event_id=request_event["event_id"],
            )
        )

        try:
            guardian_decision = self.guardian_authority.evaluate(guardian_request)
            self._validate_guardian_binding(request, guardian_decision)
        except Exception:
            denial = self.evidence_store.append_event(
                self._event(
                    request,
                    event_type="denial",
                    component="guardian",
                    outcome="denied",
                    summary="Guardian authority was unavailable or returned an invalid decision.",
                    reason_codes=["recon_missing_guardian_decision"],
                    parent_event_id=guardian_request_event["event_id"],
                )
            )
            return self._result(
                request,
                status="denied",
                reason_codes=list(denial["reason_codes"]),
            )

        guardian_outcome = self._guardian_outcome(guardian_decision)
        guardian_event = self.evidence_store.append_event(
            self._event(
                request,
                event_type="guardian_decision",
                component="guardian",
                outcome=guardian_outcome,
                summary="Guardian returned a request-bound policy decision.",
                reason_codes=[] if guardian_outcome == "allowed_dry_run" else ["guardian_denied"],
                guardian_decision_id=guardian_decision["decision_id"],
                parent_event_id=guardian_request_event["event_id"],
            )
        )

        lima_decision = self._run_lima(request, guardian_decision, guardian_event["event_id"])
        if lima_decision is None:
            failure = self.evidence_store.append_event(
                self._event(
                    request,
                    event_type="failure",
                    component="lima_runtime",
                    outcome="failed_closed",
                    summary="LIMA runtime was unavailable or returned an invalid governed decision.",
                    reason_codes=["health_degraded"],
                    guardian_decision_id=guardian_decision["decision_id"],
                    parent_event_id=guardian_event["event_id"],
                )
            )
            return self._result(
                request,
                status="denied",
                guardian_decision=guardian_decision,
                reason_codes=list(failure["reason_codes"]),
            )

        lima_event = self.evidence_store.append_event(
            self._event(
                request,
                event_type="lima_decision",
                component="lima_runtime",
                outcome=self._decision_outcome(lima_decision),
                summary="LIMA returned a non-executing governed decision.",
                decision_id=lima_decision["decision_id"],
                guardian_decision_id=guardian_decision["decision_id"],
                parent_event_id=guardian_event["event_id"],
            )
        )

        final_status = self._combined_status(guardian_decision, lima_decision)
        if final_status != "allowed_dry_run":
            event_type = "approval_requested" if final_status in {
                "confirm_required",
                "privileged_required",
            } else "denial"
            reason_codes = ["approval_missing"] if event_type == "approval_requested" else ["guardian_denied"]
            terminal = self.evidence_store.append_event(
                self._event(
                    request,
                    event_type=event_type,
                    component="supervisor",
                    outcome=final_status,
                    summary="Control plane stopped before worker assignment.",
                    reason_codes=reason_codes,
                    decision_id=lima_decision["decision_id"],
                    guardian_decision_id=guardian_decision["decision_id"],
                    parent_event_id=lima_event["event_id"],
                )
            )
            return self._result(
                request,
                status=final_status,
                guardian_decision=guardian_decision,
                lima_decision=lima_decision,
                reason_codes=list(terminal["reason_codes"]),
            )

        try:
            return self._route_assignment(
                request,
                guardian_decision,
                lima_decision,
                parent_event_id=lima_event["event_id"],
            )
        except (WorkerStateError, UnsafeRuntimeActionError):
            worker_reason = self._worker_block_reason(request["requested_worker_id"])
            blocked = self.evidence_store.append_event(
                self._event(
                    request,
                    event_type="denial",
                    component="supervisor",
                    outcome="blocked",
                    summary="Arc worker eligibility or preview boundary blocked assignment.",
                    reason_codes=[worker_reason],
                    decision_id=lima_decision["decision_id"],
                    guardian_decision_id=guardian_decision["decision_id"],
                    parent_event_id=lima_event["event_id"],
                )
            )
            return self._result(
                request,
                status="blocked",
                guardian_decision=guardian_decision,
                lima_decision=lima_decision,
                reason_codes=list(blocked["reason_codes"]),
            )

    def submit_many(
        self,
        raw_request: Mapping[str, Any],
        worker_ids: list[str] | tuple[str, ...],
    ) -> dict[str, Any]:
        """Apply least-privilege request binding independently to 1-8 Arc workers."""

        unique_workers = tuple(dict.fromkeys(worker_ids))
        if not unique_workers or len(unique_workers) > 8:
            raise ContractValidationError("worker_ids must contain 1-8 unique Arc workers")
        base_request_id = self._required_text(raw_request, "request_id")
        base_idempotency_key = self._required_text(raw_request, "idempotency_key")
        results: list[dict[str, Any]] = []
        for index, worker_id in enumerate(unique_workers, start=1):
            request = dict(raw_request)
            request["worker_id"] = worker_id
            request["request_id"] = f"{base_request_id}:worker-{index}"
            request["idempotency_key"] = f"{base_idempotency_key}:{worker_id}"
            if request.get("resource_type") == "worker_status":
                request["resource_id"] = worker_id
            results.append(self.submit(request))
        return {
            "worker_count": len(unique_workers),
            "results": results,
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }

    def _normalize_request(self, raw_request: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(raw_request, Mapping):
            raise ContractValidationError("operator request must be an object")
        unknown = sorted(set(raw_request) - CALLER_FIELDS)
        if unknown:
            raise ContractValidationError(
                f"caller fields are not authoritative or supported: {', '.join(unknown)}"
            )
        tenant_id = self._required_text(raw_request, "tenant_id")
        actor_id = self._required_text(raw_request, "actor_id")
        if tenant_id != self.tenant_id:
            raise PolicyDenyError("authenticated tenant mismatch")
        actor_role = self.authenticated_actors.get(actor_id)
        if actor_role is None:
            raise PolicyDenyError("actor is not authenticated for this Supervisor")

        action = self._required_text(raw_request, "action")
        if action not in ACTION_CATEGORIES:
            action = "unknown"
        worker_id = self._required_text(raw_request, "worker_id")
        resource_type = self._required_text(raw_request, "resource_type")
        resource_id = self._required_text(raw_request, "resource_id")
        request_id = self._required_text(raw_request, "request_id")
        idempotency_key = self._required_text(raw_request, "idempotency_key")
        now = self._now()
        canonical_identity = {
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "worker_id": worker_id,
        }
        request_hash = self._hash(canonical_identity)
        payload_hash = self._hash(
            {
                "request_hash": request_hash,
                "request_id": request_id,
                "idempotency_key": idempotency_key,
            }
        )
        request = {
            "contract_name": "supervisor.control_plane.request",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{request_id}",
            "causation_id": None,
            "idempotency_key": idempotency_key,
            "producer": {"component": "operator_console", "produced_at": now},
            "policy_version": self.policy_version,
            "request_id": request_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "action_category": ACTION_CATEGORIES[action],
            "classification_authority": "supervisor_server_derived",
            "resource": {
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
            "requested_worker_id": worker_id,
            "normalized_summary": (
                f"Operator requested {action} for {resource_type} through Arc worker metadata."
            ),
            "request_hash": request_hash,
            "payload_hash": payload_hash,
            "received_at": now,
        }
        return self.validator.validate(request, "supervisor.control_plane.request")

    def _guardian_request(
        self,
        request: dict[str, Any],
        pre_action_evidence_ref: str,
    ) -> dict[str, Any]:
        issued_at = self._now()
        expires_at = self._iso(self._parse_time(issued_at) + timedelta(minutes=5))
        payload = {
            "contract_name": "guardian.evaluation.request",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": request["tenant_id"],
            "customer_context_id": request["customer_context_id"],
            "environment": "phase0_lab",
            "correlation_id": request["correlation_id"],
            "causation_id": request["request_id"],
            "idempotency_key": f"guardian:{request['idempotency_key']}",
            "producer": {"component": "supervisor", "produced_at": issued_at},
            "policy_version": request["policy_version"],
            "request_id": request["request_id"],
            "actor_id": request["actor_id"],
            "actor_role": request["actor_role"],
            "action": request["action"],
            "resource": dict(request["resource"]),
            "worker_id": request["requested_worker_id"],
            "server_derived_category": request["action_category"],
            "classification_authority": "supervisor_server_derived",
            "request_hash": request["request_hash"],
            "payload_hash": request["payload_hash"],
            "evidence_refs": [pre_action_evidence_ref],
            "issued_at": issued_at,
            "expires_at": expires_at,
        }
        return self.validator.validate(payload, "guardian.evaluation.request")

    def _validate_guardian_binding(
        self,
        request: dict[str, Any],
        decision: dict[str, Any],
    ) -> None:
        decision = self.validator.validate(decision, "guardian.decision")
        expected = {
            "tenant_id": request["tenant_id"],
            "request_id": request["request_id"],
            "policy_version": request["policy_version"],
            "valid_for_action_ref": request["request_hash"],
            "decision_scope_hash": request["payload_hash"],
            "bound_tenant_id": request["tenant_id"],
            "bound_worker_id": request["requested_worker_id"],
            "bound_action_type": request["action"],
        }
        mismatches = [key for key, value in expected.items() if decision.get(key) != value]
        if mismatches:
            raise PolicyDenyError(
                f"Guardian decision request binding mismatch: {', '.join(sorted(mismatches))}"
            )
        if self._parse_time(str(decision["expires_at"])) <= self.clock():
            raise PolicyDenyError("Guardian decision expired")

    def _run_lima(
        self,
        request: dict[str, Any],
        guardian_decision: dict[str, Any],
        evidence_ref: str,
    ) -> dict[str, Any] | None:
        if self.lima_runner is None:
            return None
        capability = ACTION_CAPABILITIES.get(request["action"])
        payload = {
            "request_id": request["request_id"],
            "consumer": "lima_office_supervisor",
            "surface": "arc_assignment_preview",
            "actor_id": request["actor_id"],
            "normalized_request": {
                "action": request["action"],
                "resource": dict(request["resource"]),
                "classification_authority": "supervisor_server_derived",
            },
            "requested_action": request["action"],
            "action_category": request["action_category"],
            "tool_name": capability or "arc_blocked_preview",
            "tool_args": {},
            "trust_context": {
                "authenticated_tenant_id": request["tenant_id"],
                "authenticated_actor_role": request["actor_role"],
                "guardian_decision_id": guardian_decision["decision_id"],
                "guardian_policy_version": guardian_decision["policy_version"],
                "request_hash": request["request_hash"],
                "payload_hash": request["payload_hash"],
                "room_execution_allowed": False,
                "execution_gate_present": False,
            },
            "evidence_refs": [evidence_ref],
        }
        try:
            raw = self.lima_runner(payload)
            decision = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw)
            self._validate_lima_decision(request, decision)
            return decision
        except Exception:
            return None

    @staticmethod
    def _validate_lima_decision(
        request: dict[str, Any],
        decision: dict[str, Any],
    ) -> None:
        if decision.get("request_id") != request["request_id"]:
            raise UnsafeRuntimeActionError("LIMA decision request mismatch")
        if decision.get("source_policy") != LIMA_GUARDIAN_SOURCE_POLICY:
            raise UnsafeRuntimeActionError("LIMA static policy fallback is forbidden")
        if any(
            decision.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise UnsafeRuntimeActionError("LIMA decision cannot authorize execution")

    def _route_assignment(
        self,
        request: dict[str, Any],
        guardian_decision: dict[str, Any],
        lima_decision: dict[str, Any],
        *,
        parent_event_id: str,
    ) -> dict[str, Any]:
        worker_id = request["requested_worker_id"]
        capability = ACTION_CAPABILITIES.get(request["action"])
        if capability is None:
            raise UnsafeRuntimeActionError("no Arc preview capability exists for action")
        worker = self.registry.require_assignable(worker_id, request["tenant_id"])
        if self.require_authenticated_workers and not worker.authenticated:
            raise WorkerStateError(
                "operational control-plane routing requires authenticated Arc registration"
            )
        if capability not in worker.capabilities:
            raise WorkerStateError("Arc worker lacks the required preview capability")
        endpoint = self.worker_endpoints.get(worker_id)
        if endpoint is None:
            raise WorkerStateError("Arc worker preview endpoint is unavailable")

        created_at = self._now()
        assignment_id = f"assignment:{uuid4().hex}"
        assignment_event = self.evidence_store.append_event(
            self._event(
                request,
                event_type="assignment_preview",
                component="supervisor",
                outcome="allowed_dry_run",
                summary="Non-executing assignment preview offered to an eligible Arc worker.",
                decision_id=lima_decision["decision_id"],
                guardian_decision_id=guardian_decision["decision_id"],
                parent_event_id=parent_event_id,
            )
        )
        assignment = {
            "contract_name": "worker.assignment.preview",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": request["tenant_id"],
            "customer_context_id": request["customer_context_id"],
            "environment": "phase0_lab",
            "correlation_id": request["correlation_id"],
            "causation_id": lima_decision["decision_id"],
            "idempotency_key": f"assignment:{request['idempotency_key']}",
            "producer": {"component": "supervisor", "produced_at": created_at},
            "policy_version": guardian_decision["policy_version"],
            "assignment_id": assignment_id,
            "request_id": request["request_id"],
            "guardian_decision_id": guardian_decision["decision_id"],
            "lima_decision_id": lima_decision["decision_id"],
            "worker_id": worker_id,
            "capability": capability,
            "status": "offered",
            "reason_codes": [],
            "evidence_refs": [assignment_event["event_id"]],
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
            "created_at": created_at,
            "acknowledged_at": None,
        }
        assignment = self.validator.validate(assignment, "worker.assignment.preview")
        try:
            acknowledgement = endpoint.acknowledge_preview(assignment)
        except Exception:
            rejection = self.evidence_store.append_event(
                self._event(
                    request,
                    event_type="worker_acknowledgement",
                    component="worker",
                    outcome="rejected",
                    summary="Arc worker rejected or failed to acknowledge the assignment preview.",
                    reason_codes=["capability_mismatch"],
                    decision_id=lima_decision["decision_id"],
                    guardian_decision_id=guardian_decision["decision_id"],
                    parent_event_id=assignment_event["event_id"],
                )
            )
            return self._result(
                request,
                status="rejected",
                guardian_decision=guardian_decision,
                lima_decision=lima_decision,
                reason_codes=list(rejection["reason_codes"]),
            )

        acknowledgement = self.validator.validate(
            acknowledgement,
            "worker.assignment.preview",
        )
        acknowledged = acknowledgement["status"] == "acknowledged"
        acknowledgement_event = self.evidence_store.append_event(
            self._event(
                request,
                event_type="worker_acknowledgement",
                component="worker",
                outcome="acknowledged" if acknowledged else "rejected",
                summary=(
                    "Arc worker acknowledged the non-executing assignment preview."
                    if acknowledged
                    else "Arc worker rejected the non-executing assignment preview."
                ),
                reason_codes=[] if acknowledged else ["capability_mismatch"],
                decision_id=lima_decision["decision_id"],
                guardian_decision_id=guardian_decision["decision_id"],
                parent_event_id=assignment_event["event_id"],
            )
        )
        return self._result(
            request,
            status="acknowledged" if acknowledged else "rejected",
            guardian_decision=guardian_decision,
            lima_decision=lima_decision,
            assignment=acknowledgement,
            reason_codes=list(acknowledgement_event["reason_codes"]),
        )

    def _worker_block_reason(self, worker_id: str) -> str:
        try:
            worker = self.registry.get(worker_id)
        except WorkerStateError:
            return "worker_stale"
        if worker.state == "quarantined":
            return "worker_quarantined"
        return "worker_stale"

    def _event(
        self,
        request: dict[str, Any],
        *,
        event_type: str,
        component: str,
        outcome: str,
        summary: str,
        reason_codes: list[str] | None = None,
        decision_id: str | None = None,
        guardian_decision_id: str | None = None,
        parent_event_id: str | None = None,
    ) -> dict[str, Any]:
        created_at = self._now()
        return {
            "contract_name": "control_plane.event",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": request["tenant_id"],
            "customer_context_id": request["customer_context_id"],
            "environment": "phase0_lab",
            "correlation_id": request["correlation_id"],
            "causation_id": parent_event_id,
            "idempotency_key": f"event:{request['idempotency_key']}:{event_type}:{uuid4().hex}",
            "producer": {"component": component, "produced_at": created_at},
            "policy_version": request["policy_version"],
            "event_id": f"ev-control-plane:{uuid4().hex}",
            "event_type": event_type,
            "actor_id": request["actor_id"],
            "worker_id": request["requested_worker_id"],
            "request_id": request["request_id"],
            "decision_id": decision_id,
            "guardian_decision_id": guardian_decision_id,
            "parent_event_id": parent_event_id,
            "payload_hash": request["payload_hash"],
            "redacted_summary": summary,
            "outcome": outcome,
            "reason_codes": reason_codes or [],
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
            "created_at": created_at,
        }

    def _result(
        self,
        request: dict[str, Any],
        *,
        status: str,
        guardian_decision: dict[str, Any] | None = None,
        lima_decision: dict[str, Any] | None = None,
        assignment: dict[str, Any] | None = None,
        reason_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "request_id": request["request_id"],
            "tenant_id": request["tenant_id"],
            "actor_id": request["actor_id"],
            "worker_id": request["requested_worker_id"],
            "status": status,
            "classification_authority": "supervisor_server_derived",
            "action_category": request["action_category"],
            "guardian": self._public_guardian(guardian_decision),
            "lima": self._public_lima(lima_decision),
            "assignment": assignment,
            "reason_codes": reason_codes or [],
            "evidence": self.evidence_store.events_for_request(
                request["request_id"],
                request["tenant_id"],
            ),
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }

    @staticmethod
    def _public_guardian(decision: dict[str, Any] | None) -> dict[str, Any] | None:
        if decision is None:
            return None
        return {
            "decision_id": decision["decision_id"],
            "decision": decision["decision"],
            "approval_required": decision["approval_required"],
            "policy_version": decision["policy_version"],
            "policy_snapshot_hash": decision["policy_snapshot_hash"],
            "request_binding": decision["valid_for_action_ref"],
            "expires_at": decision["expires_at"],
        }

    @staticmethod
    def _public_lima(decision: dict[str, Any] | None) -> dict[str, Any] | None:
        if decision is None:
            return None
        return {
            "decision_id": decision["decision_id"],
            "status": decision["status"],
            "allowed": bool(decision["allowed"]),
            "requires_approval": bool(decision["requires_approval"]),
            "risk_level": decision["risk_level"],
            "reason_codes": SupervisorControlPlane._safe_reason_codes(decision),
            "source_policy": decision["source_policy"],
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }

    @staticmethod
    def _safe_reason_codes(decision: dict[str, Any]) -> list[str]:
        safe: list[str] = []
        for value in decision.get("reason_codes") or []:
            code = str(value)
            if not code or len(code) > 80:
                continue
            if not code[0].islower():
                continue
            if all(character.islower() or character.isdigit() or character == "_" for character in code):
                safe.append(code)
        return safe

    @staticmethod
    def _guardian_outcome(decision: dict[str, Any]) -> str:
        value = decision["decision"]
        if value in {"allow", "allow_with_evidence"}:
            return "allowed_dry_run"
        if value == "requires_approval":
            return "confirm_required"
        return "denied"

    @staticmethod
    def _decision_outcome(decision: dict[str, Any]) -> str:
        status = str(decision.get("status") or "denied")
        return status if status in {
            "allowed_dry_run",
            "confirm_required",
            "privileged_required",
            "denied",
        } else "denied"

    @staticmethod
    def _combined_status(
        guardian_decision: dict[str, Any],
        lima_decision: dict[str, Any],
    ) -> str:
        guardian = guardian_decision["decision"]
        lima = str(lima_decision.get("status") or "denied")
        if guardian in {"deny", "block_mvp", "quarantine_subject"}:
            return "denied"
        if guardian == "requires_approval":
            return lima if lima in {"confirm_required", "privileged_required"} else "confirm_required"
        return "allowed_dry_run" if lima == "allowed_dry_run" else "denied"

    def _now(self) -> str:
        return self._iso(self.clock())

    @staticmethod
    def _iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _hash(payload: Mapping[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContractValidationError(f"{field} is required")
        return value.strip()
