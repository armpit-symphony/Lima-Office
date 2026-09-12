"""Process-bound attended operator sessions for the single-user Phase 0 lab."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import threading
from typing import Any, Protocol
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.guardian import GuardianPolicy

BIND_CONFIRMATION = "BIND ATTENDED LOCAL OPERATOR SESSION"
POLICY_VERSION = "policy-operator-session-binding-lab-v1"
SESSION_TTL_SECONDS = 1800


class OperatorSessionError(RuntimeError):
    """Safe failure for the attended local-session boundary."""


class OperatorSessionStore(Protocol):
    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str: ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class AttendedOperatorSessionService:
    """Bind this process to a pseudonymous OS subject with lab-only assurance."""

    def __init__(self, store: OperatorSessionStore, *, tenant_id: str = "tenant-lab-001",
                 customer_context_id: str = "customer-context-main",
                 validator: ContractValidator | None = None,
                 guardian: GuardianPolicy | None = None,
                 clock: Callable[[], datetime] | None = None,
                 subject_provider: Callable[[], str] | None = None) -> None:
        self.store = store
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.validator = validator or ContractValidator()
        self.guardian = guardian or GuardianPolicy()
        self.clock = clock or _utc_now
        self.subject_provider = subject_provider or getpass.getuser
        self._lock = threading.RLock()
        self._active: dict[str, Any] | None = None

    def state_summary(self) -> dict[str, Any]:
        with self._lock:
            record = dict(self._active) if self._active is not None else None
        active = bool(record) and self.clock() < _parse_timestamp(record["expires_at"])
        return {"runtime_enabled": True, "binding": record if active else None,
                "active": active, "process_bound": True, "survives_restart": False,
                "production_identity_verified": False, "approval_authority": False,
                "pin_required": False}

    def bind(self, *, confirmation: Any) -> dict[str, Any]:
        if confirmation != BIND_CONFIRMATION:
            raise OperatorSessionError("Explicit attended-session confirmation is required.")
        try:
            local_subject = self.subject_provider()
        except Exception as exc:
            raise OperatorSessionError("The local OS subject could not be read.") from exc
        if not isinstance(local_subject, str) or not local_subject.strip():
            raise OperatorSessionError("The local OS subject is unavailable.")
        now, token = self.clock(), uuid4().hex
        binding_id = f"operator-session-binding:{token}"
        operator_id = "operator-lab:" + hashlib.sha256(
            f"{self.tenant_id}:{local_subject}:{token}".encode()).hexdigest()[:24]
        evidence_id = f"ev-operator-session:{token}"
        safe = {"binding_id": binding_id, "operator_id": operator_id,
                "assurance_level": "personal_pc_attended_lab",
                "raw_os_username_stored": False, "credentials_collected": False,
                "production_identity_verified": False, "approval_authority": False}
        try:
            pre = self.store.record_event("operator_session_binding_requested", safe)
        except Exception as exc:
            raise OperatorSessionError("Pre-action evidence failed; binding denied.") from exc
        context = {
            "decision_id": f"gd-operator-session:{token}",
            "request_id": f"request-operator-session:{token}",
            "tenant_id": self.tenant_id, "customer_context_id": self.customer_context_id,
            "subject": {"subject_type": "operator", "subject_id": operator_id},
            "schema_action_class": "internal_operator_session_binding",
            "resource_ref": {"resource_type": "operator_session", "resource_id": binding_id,
                             "resource_scope": "operator_scoped"},
            "data_classification": "internal", "risk_tier": "low",
            "policy_refs": ["policy.operator.session.binding.lab.v1",
                            "policy.guardian.syscall_gate.v1"],
            "policy_version": POLICY_VERSION, "valid_for_action_ref": binding_id,
            "decision_scope_hash": "sha256:" + hashlib.sha256(binding_id.encode()).hexdigest(),
            "bound_action_type": "operator_session_bind",
            "bound_tool_scope": {"resource_refs": [binding_id],
                "allowed_operations": ["bind_attended_local_session"],
                "prohibited_operations": ["approve_request", "issue_token", "dispatch_arc",
                                          "connector_access", "external_effect"]},
            "execution_mode": "identity_metadata_only", "external_effect": "none",
            "evidence_required": True, "evidence_artifact_id": evidence_id,
            "evidence_artifact_ids": [evidence_id], "pre_action_evidence_refs": [evidence_id],
            "post_action_evidence_refs": [evidence_id], "storage_evidence_ref": pre,
            "attended": True, "operator_confirmation": True, "local_loopback_only": True,
            "process_bound": True, "raw_os_username_stored": False,
            "credentials_collected": False, "production_identity_verified": False,
            "approval_authority": False, "approval_result_allowed": False,
            "approval_token_access_allowed": False, "arc_dispatch_allowed": False,
            "connector_access_allowed": False, "submission_allowed": False,
            "approval_required": False}
        decision = self.guardian.decide("operator_session_bind", context)
        self.validator.validate(decision, "guardian.decision")
        if decision["decision"] not in {"allow", "allow_with_evidence"}:
            raise OperatorSessionError("Guardian denied the attended session binding.")
        expires = now + timedelta(seconds=SESSION_TTL_SECONDS)
        post = self.store.record_event("operator_session_binding_committed", {
            **safe, "guardian_decision_id": decision["decision_id"],
            "pre_action_evidence_ref": pre, "expires_at": _timestamp(expires)})
        record = {
            "contract_name": "operator.session.binding", "contract_version": "1.0.0",
            "schema_version": "1.0.0", "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id, "environment": "phase0_lab",
            "correlation_id": f"corr-{binding_id}", "causation_id": None,
            "idempotency_key": f"idem-{binding_id}",
            "producer": {"component": "operator_console", "produced_at": _timestamp(now)},
            "policy_version": POLICY_VERSION, "binding_id": binding_id,
            "operator_id": operator_id, "auth_method": "local_os_session_attended_lab",
            "assurance_level": "personal_pc_attended_lab", "status": "active",
            "local_loopback_only": True, "process_bound": True,
            "survives_process_restart": False, "raw_os_username_stored": False,
            "credentials_collected": False, "pin_required": False, "mfa_verified": False,
            "production_identity_verified": False, "pending_request_creation_allowed": True,
            "approval_authority": False, "approval_result_allowed": False,
            "approval_token_allowed": False, "arc_dispatch_allowed": False,
            "guardian_decision_id": decision["decision_id"], "pre_action_evidence_ref": pre,
            "post_action_evidence_ref": post, "issued_at": _timestamp(now),
            "expires_at": _timestamp(expires)}
        self.validator.validate(record, "operator.session.binding")
        with self._lock:
            self._active = record
        return dict(record)

    def require_active(self, binding_id: Any) -> dict[str, Any]:
        with self._lock:
            record = dict(self._active) if self._active is not None else None
        if not isinstance(binding_id, str) or record is None or record["binding_id"] != binding_id:
            raise OperatorSessionError("The attended operator session is not active.")
        if self.clock() >= _parse_timestamp(record["expires_at"]):
            raise OperatorSessionError("The attended operator session expired; bind again.")
        self.validator.validate(record, "operator.session.binding")
        return record
