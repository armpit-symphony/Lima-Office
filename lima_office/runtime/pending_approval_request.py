"""Durable, non-executing approval requests from reviewed lab previews."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Protocol
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.guardian import GuardianPolicy
from lima_office.runtime.operator_session import AttendedOperatorSessionService, OperatorSessionError

CREATE_CONFIRMATION = "CREATE PENDING APPROVAL REQUEST"
POLICY_VERSION = "policy-pending-approval-request-lab-v1"
REQUEST_TTL_SECONDS = 900
ALLOWED_OPERATION = "review_prepared_form_plan"
PROHIBITED_OPERATIONS = (
    "approve_request", "issue_approval_token", "create_approval_binding",
    "verify_token", "create_replay_record", "assign_worker", "dispatch_arc",
    "model_call", "tool_use", "connector_access", "form_submission", "external_effect",
)


class PendingApprovalRequestError(RuntimeError):
    """Safe pending-request boundary failure."""


class PendingApprovalRequestStore(Protocol):
    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str: ...
    def office_proposal(self, proposal_id: str) -> dict[str, Any] | None: ...
    def office_approval_preview(self, preview_id: str) -> dict[str, Any] | None: ...
    def office_pending_approval_requests(self, limit: int = 50) -> list[dict[str, Any]]: ...
    def office_pending_approval_request_for_preview(self, preview_id: str) -> dict[str, Any] | None: ...
    def office_approval_result_for_request(self, approval_request_id: str) -> dict[str, Any] | None: ...
    def commit_office_pending_approval_request(self, request: Mapping[str, Any], *,
        event_id: str, event_type: str, event_payload: Mapping[str, Any]) -> str: ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()


class PendingApprovalRequestService:
    """Materialize only pending request metadata; never approval authority."""

    def __init__(self, store: PendingApprovalRequestStore,
                 operator_sessions: AttendedOperatorSessionService, *,
                 tenant_id: str = "tenant-lab-001",
                 customer_context_id: str = "customer-context-main",
                 validator: ContractValidator | None = None,
                 guardian: GuardianPolicy | None = None,
                 clock: Callable[[], datetime] | None = None) -> None:
        self.store = store
        self.operator_sessions = operator_sessions
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.validator = validator or ContractValidator()
        self.guardian = guardian or GuardianPolicy()
        self.clock = clock or _utc_now

    def state_summary(self) -> dict[str, Any]:
        now, items = self.clock(), []
        for record in self.store.office_pending_approval_requests(limit=50):
            self.validator.validate(record, "approval.request")
            item = dict(record)
            item["record_hash"] = _digest(record)
            item["expired_for_decision"] = now >= _parse_timestamp(record["expires_at"])
            result = self.store.office_approval_result_for_request(
                record["approval_request_id"]
            )
            if result is not None:
                self.validator.validate(result, "approval.result")
                item["approval_result_id"] = result["approval_result_id"]
                item["result_reason_code"] = result["result_reason_code"]
                item["decision_kind"] = result.get("decision_kind")
            items.append(item)
        return {"runtime_enabled": True, "request_creation_enabled": True,
                "decision_runtime_enabled": True,
                "non_authorizing_terminal_results_enabled": True,
                "positive_approval_results_enabled": False,
                "approval_tokens_enabled": False, "approval_bindings_enabled": False,
                "token_verification_enabled": False, "replay_records_enabled": False,
                "arc_dispatch_enabled": False, "requests": items}

    def create(self, *, approval_preview_id: Any, expected_preview_revision: Any,
               operator_session_binding_id: Any, confirmation: Any) -> dict[str, Any]:
        if confirmation != CREATE_CONFIRMATION:
            raise PendingApprovalRequestError("Fresh request-creation intent is required.")
        preview = self._reviewed_preview(approval_preview_id, expected_preview_revision)
        try:
            session = self.operator_sessions.require_active(operator_session_binding_id)
        except OperatorSessionError as exc:
            raise PendingApprovalRequestError(str(exc)) from exc
        if session["tenant_id"] != self.tenant_id:
            raise PendingApprovalRequestError("Operator session belongs to another tenant.")
        if self.store.office_pending_approval_request_for_preview(preview["approval_preview_id"]):
            raise PendingApprovalRequestError("That preview already has an approval request.")
        proposal = self._matching_proposal(preview)
        now, token = self.clock(), uuid4().hex
        request_id = f"approval-request:{token}"
        evidence_id, fresh_intent = f"ev-approval-request:{token}", f"fresh-intent:{token}"
        safe = {"approval_request_id": request_id,
            "approval_preview_id": preview["approval_preview_id"],
            "source_proposal_id": proposal["proposal_id"],
            "operator_session_binding_id": session["binding_id"],
            "operator_id": session["operator_id"], "status": "pending_review",
            "approval_result_created": False, "approval_token_issued": False,
            "approval_binding_created": False, "token_verification_performed": False,
            "replay_record_created": False, "assigned_worker_id": None,
            "arc_dispatched": False, "external_side_effects": False}
        try:
            pre = self.store.record_event(
                "office_pending_approval_request_creation_requested", safe)
        except Exception as exc:
            raise PendingApprovalRequestError("Pre-action evidence failed; request denied.") from exc
        decision = self.guardian.decide(
            "office_pending_approval_request_create",
            self._guardian_context(request_id, preview, proposal, session, evidence_id, pre, token))
        self.validator.validate(decision, "guardian.decision")
        if decision["decision"] != "requires_approval":
            raise PendingApprovalRequestError("Guardian did not require pending review.")
        guardian_evidence = self.store.record_event(
            "office_pending_approval_request_guardian_required_review",
            {**safe, "guardian_decision_id": decision["decision_id"],
             "guardian_decision": decision["decision"], "pre_action_evidence_ref": pre})
        scope = {"external_effect": "none", "resource_refs": [proposal["proposal_id"]],
                 "allowed_operations": [ALLOWED_OPERATION],
                 "prohibited_operations": list(PROHIBITED_OPERATIONS), "max_uses": 0}
        expires = now + timedelta(seconds=REQUEST_TTL_SECONDS)
        post = f"harness-event:{uuid4().hex}"
        request = {
            "contract_name": "approval.request", "contract_version": "1.0.0",
            "schema_version": "1.0.0", "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id, "environment": "phase0_lab",
            "correlation_id": f"corr-{request_id}",
            "causation_id": preview["approval_preview_id"],
            "idempotency_key": f"idem-{request_id}", "approval_request_id": request_id,
            "task_id": proposal["proposal_id"], "guardian_decision_id": decision["decision_id"],
            "producer": {"component": "supervisor", "produced_at": _timestamp(now)},
            "requested_by": {"actor_type": "operator", "actor_id": session["operator_id"]},
            "action_class": "synthetic_form_preparation_review", "risk_tier": "medium",
            "data_classification": "synthetic_fixture_only", "requested_scope": scope,
            "scope_hash": _digest({"preview_hash": _digest(preview),
                "proposal_hash": _digest(proposal), "session_binding_id": session["binding_id"],
                "requested_scope": scope}),
            "reason": "Attended review of a fixed synthetic form-preparation plan; no execution authority.",
            "status": "pending_review", "approval_result": "pending",
            "approver_roles": ["business_owner"], "policy_version": POLICY_VERSION,
            "evidence_required": True, "evidence_artifact_ids": [evidence_id],
            "expires_at": _timestamp(expires), "created_at": _timestamp(now),
            "approver_operator_id": None, "decided_at": None, "denial_reason": None,
            "approval_token_id": None, "approval_chain_id": None, "binding_id": None,
            "bound_tenant_id": self.tenant_id, "bound_task_id": proposal["proposal_id"],
            "bound_action_type": ALLOWED_OPERATION,
            "bound_tool_scope": {"resource_refs": [proposal["proposal_id"]],
                "allowed_operations": [ALLOWED_OPERATION],
                "prohibited_operations": list(PROHIBITED_OPERATIONS)},
            "bound_worker_id": None, "bound_requester_ref": session["binding_id"],
            "source_approval_preview_id": preview["approval_preview_id"],
            "source_approval_preview_revision": preview["revision"],
            "source_approval_preview_hash": _digest(preview),
            "operator_session_binding_id": session["binding_id"],
            "fresh_intent_evidence_ref": fresh_intent,
            "approval_result_created": False, "approval_binding_created": False,
            "token_verification_performed": False, "replay_record_created": False,
            "assigned_worker_id": None, "arc_dispatch_allowed": False,
            "arc_dispatched": False, "external_side_effects": False}
        self.validator.validate(request, "approval.request")
        completion = {**safe, "guardian_decision_id": decision["decision_id"],
                      "guardian_evidence_ref": guardian_evidence,
                      "fresh_intent_evidence_ref": fresh_intent,
                      "record_sha256": _digest(request)}
        try:
            self.store.commit_office_pending_approval_request(
                request, event_id=post, event_type="office_pending_approval_request_created",
                event_payload=completion)
        except Exception as exc:
            raise PendingApprovalRequestError(
                "Request and completion evidence could not be committed atomically.") from exc
        return request

    def _reviewed_preview(self, preview_id: Any, revision: Any) -> dict[str, Any]:
        if not isinstance(preview_id, str) or not preview_id.startswith("approval-preview:"):
            raise PendingApprovalRequestError("A valid approval preview id is required.")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise PendingApprovalRequestError("A positive preview revision is required.")
        preview = self.store.office_approval_preview(preview_id)
        if preview is None:
            raise PendingApprovalRequestError("Approval preview was not found.")
        self.validator.validate(preview, "supervisor.approval.preview")
        if preview["revision"] != revision:
            raise PendingApprovalRequestError("Approval preview changed; reload and review it again.")
        if preview["state"] != "reviewed_no_authority":
            raise PendingApprovalRequestError("The approval preview has not been reviewed.")
        if self.clock() >= _parse_timestamp(preview["preview_expires_at"]):
            raise PendingApprovalRequestError("The approval preview expired; restart the proposal flow.")
        if preview["tenant_id"] != self.tenant_id:
            raise PendingApprovalRequestError("Approval preview belongs to another tenant.")
        return preview

    def _matching_proposal(self, preview: Mapping[str, Any]) -> dict[str, Any]:
        proposal = self.store.office_proposal(str(preview["source_proposal_id"]))
        if proposal is None:
            raise PendingApprovalRequestError("The source proposal is unavailable.")
        self.validator.validate(proposal, "supervisor.task.proposal")
        if not all((proposal.get("tenant_id") == self.tenant_id,
            proposal.get("customer_context_id") == self.customer_context_id,
            proposal.get("state") == "accepted_for_future_approval",
            proposal.get("revision") == preview.get("source_proposal_revision"),
            _digest(proposal) == preview.get("source_proposal_hash"))):
            raise PendingApprovalRequestError("Source proposal changed; request creation denied.")
        return proposal

    def _guardian_context(self, request_id: str, preview: Mapping[str, Any],
                          proposal: Mapping[str, Any], session: Mapping[str, Any],
                          evidence_id: str, pre: str, token: str) -> dict[str, Any]:
        return {"decision_id": f"gd-pending-approval-request:{token}",
            "request_id": f"request-pending-approval:{token}",
            "approval_request_id": request_id, "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "requested_by": {"actor_type": "operator", "actor_id": session["operator_id"]},
            "subject": {"subject_type": "task", "subject_id": proposal["proposal_id"]},
            "schema_action_class": "internal_pending_approval_request",
            "resource_ref": {"resource_type": "approval_request", "resource_id": request_id,
                             "resource_scope": "task_scoped"},
            "data_classification": "synthetic_fixture_only", "risk_tier": "medium",
            "policy_refs": ["policy.pending.approval.request.lab.v1",
                            "policy.guardian.syscall_gate.v1"],
            "policy_version": POLICY_VERSION, "valid_for_action_ref": request_id,
            "decision_scope_hash": _digest({"preview": _digest(preview),
                "proposal": _digest(proposal), "session": session["binding_id"]}),
            "bound_tenant_id": self.tenant_id, "bound_task_id": proposal["proposal_id"],
            "bound_worker_id": None,
            "bound_action_type": "office_pending_approval_request_create",
            "bound_tool_scope": {"resource_refs": [proposal["proposal_id"]],
                "allowed_operations": [ALLOWED_OPERATION],
                "prohibited_operations": list(PROHIBITED_OPERATIONS)},
            "execution_mode": "request_metadata_only", "external_effect": "none",
            "evidence_required": True, "evidence_artifact_id": evidence_id,
            "evidence_artifact_ids": [evidence_id], "pre_action_evidence_refs": [evidence_id],
            "post_action_evidence_refs": [evidence_id], "storage_evidence_ref": pre,
            "attended": True, "operator_confirmation": True,
            "operator_session_active": True,
            "operator_session_binding_id": session["binding_id"],
            "production_identity_verified": False, "fresh_intent": True,
            "preview_reviewed_no_authority": True, "source_current": True,
            "synthetic_data_only": True, "free_form_content_allowed": False,
            "request_only": True, "approval_result_allowed": False,
            "approval_token_access_allowed": False, "approval_binding_allowed": False,
            "token_verification_allowed": False, "replay_record_allowed": False,
            "model_call_allowed": False, "tool_execution_allowed": False,
            "arc_dispatch_allowed": False, "connector_access_allowed": False,
            "submission_allowed": False, "external_side_effects": False,
            "approval_required": True}
