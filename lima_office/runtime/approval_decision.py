"""Durable, non-authorizing terminal decisions for synthetic approval requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.guardian import GuardianPolicy
from lima_office.runtime.operator_session import AttendedOperatorSessionService, OperatorSessionError
from lima_office.runtime.pending_approval_request import _digest, _parse_timestamp, _timestamp

DECISION_CONFIRMATION = "RECORD NON-AUTHORIZING APPROVAL DECISION"
POLICY_VERSION = "policy-non-authorizing-approval-decision-lab-v1"

_TRANSITIONS = {
    "deny": ("denied", "denied_by_approver", "attended_deny",
             "Denied by the attended business owner."),
    "cancel": ("cancelled", "cancelled", "attended_cancel",
               "Cancelled by the original attended requester."),
    "expire": ("expired", "expired", "explicit_expire",
               "Recorded expired after the request validity window elapsed."),
}


class ApprovalDecisionError(RuntimeError):
    """Safe failure at the non-authorizing approval-decision boundary."""


class ApprovalDecisionStore(Protocol):
    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str: ...
    def office_approval_request(self, approval_request_id: str) -> dict[str, Any] | None: ...
    def office_approval_result_for_request(self, approval_request_id: str) -> dict[str, Any] | None: ...
    def office_proposal(self, proposal_id: str) -> dict[str, Any] | None: ...
    def office_approval_preview(self, preview_id: str) -> dict[str, Any] | None: ...
    def commit_office_non_authorizing_approval_decision(
        self, request: Mapping[str, Any], result: Mapping[str, Any], *,
        expected_request_hash: str, event_id: str, event_type: str,
        event_payload: Mapping[str, Any],
    ) -> str: ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NonAuthorizingApprovalDecisionService:
    """Close a synthetic request without ever granting execution authority."""

    def __init__(self, store: ApprovalDecisionStore,
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

    def transition(self, *, approval_request_id: Any, expected_request_hash: Any,
                   action: Any, operator_session_binding_id: Any = None,
                   confirmation: Any) -> dict[str, Any]:
        if confirmation != DECISION_CONFIRMATION:
            raise ApprovalDecisionError("Fresh non-authorizing decision intent is required.")
        if action not in _TRANSITIONS:
            raise ApprovalDecisionError("Only deny, cancel, or expire is supported.")
        if not isinstance(approval_request_id, str) or not approval_request_id.startswith(
                "approval-request:"):
            raise ApprovalDecisionError("A valid approval request id is required.")
        if (not isinstance(expected_request_hash, str)
                or not expected_request_hash.startswith("sha256:")
                or len(expected_request_hash) != 71):
            raise ApprovalDecisionError("An exact approval request hash is required.")

        request = self.store.office_approval_request(approval_request_id)
        if request is None:
            raise ApprovalDecisionError("Approval request was not found.")
        self.validator.validate(request, "approval.request")
        if _digest(request) != expected_request_hash:
            raise ApprovalDecisionError("Approval request changed; reload before deciding.")
        if request["tenant_id"] != self.tenant_id:
            raise ApprovalDecisionError("Approval request belongs to another tenant.")
        if request["status"] != "pending_review" or request["approval_result"] != "pending":
            raise ApprovalDecisionError("Approval request is not pending review.")
        if request["action_class"] != "synthetic_form_preparation_review":
            raise ApprovalDecisionError("Only the synthetic lab approval lane is supported.")
        if self.store.office_approval_result_for_request(approval_request_id) is not None:
            raise ApprovalDecisionError("Approval result already exists.")

        now = self.clock()
        expired = now >= _parse_timestamp(request["expires_at"])
        session: Mapping[str, Any] | None = None
        if action == "expire":
            if not expired:
                raise ApprovalDecisionError("Approval request has not expired.")
            if operator_session_binding_id not in {None, ""}:
                raise ApprovalDecisionError("Expiry recording does not accept an operator session.")
        else:
            if expired:
                raise ApprovalDecisionError("Approval request expired; record expiry instead.")
            try:
                session = self.operator_sessions.require_active(operator_session_binding_id)
            except OperatorSessionError as exc:
                raise ApprovalDecisionError(str(exc)) from exc
            if session["tenant_id"] != self.tenant_id:
                raise ApprovalDecisionError("Operator session belongs to another tenant.")
            if action == "cancel" and session["binding_id"] != request["bound_requester_ref"]:
                raise ApprovalDecisionError("Only the original attended requester may cancel.")
            self._require_current_source(request)

        result_value, reason_code, decision_kind, denial_reason = _TRANSITIONS[action]
        token = uuid4().hex
        result_id = f"approval-result:{token}"
        evidence_id = f"ev-approval-decision:{token}"
        safe = {
            "approval_request_id": approval_request_id, "action": action,
            "result": result_value, "non_authorizing": True,
            "approval_result_created": True, "approval_token_issued": False,
            "approval_binding_created": False, "token_verification_performed": False,
            "replay_record_created": False, "assigned_worker_id": None,
            "arc_dispatched": False, "external_side_effects": False,
        }
        try:
            pre = self.store.record_event(
                "office_non_authorizing_approval_decision_requested", safe)
        except Exception as exc:
            raise ApprovalDecisionError("Pre-action evidence failed; decision denied.") from exc
        context = self._guardian_context(
            request, action, result_value, session, evidence_id, pre, token, expired)
        decision = self.guardian.decide("office_non_authorizing_approval_decision", context)
        self.validator.validate(decision, "guardian.decision")
        if decision["decision"] != "allow_with_evidence":
            raise ApprovalDecisionError("Guardian denied the non-authorizing decision.")

        decided_at = _timestamp(now)
        fresh_intent = f"fresh-intent:{token}"
        updated = dict(request)
        updated.update({
            "status": result_value, "approval_result": result_value,
            "approver_operator_id": session["operator_id"] if session else None,
            "decided_at": decided_at, "denial_reason": denial_reason,
            "approval_result_created": True,
            "approval_token_id": None, "approval_chain_id": None, "binding_id": None,
            "approval_binding_created": False, "token_verification_performed": False,
            "replay_record_created": False, "assigned_worker_id": None,
            "arc_dispatch_allowed": False, "arc_dispatched": False,
            "external_side_effects": False,
            "evidence_artifact_ids": [*request["evidence_artifact_ids"], evidence_id],
        })
        result = {
            "contract_name": "approval.result", "contract_version": "1.0.0",
            "schema_version": "1.0.0", "taxonomy_version": "taxonomy-reason-v1",
            "tenant_id": self.tenant_id, "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab", "correlation_id": request["correlation_id"],
            "causation_id": approval_request_id, "idempotency_key": f"idem-{result_id}",
            "approval_result_id": result_id, "approval_request_id": approval_request_id,
            "task_id": request["task_id"], "guardian_decision_id": decision["decision_id"],
            "producer": {"component": "operator_console", "produced_at": decided_at},
            "result": result_value, "result_reason_code": reason_code,
            "approver_operator_id": session["operator_id"] if session else None,
            "approver_role_ref": "business_owner" if session else None,
            "action_class": request["action_class"], "risk_tier": request["risk_tier"],
            "data_classification": request["data_classification"],
            "requested_scope_hash": request["scope_hash"], "approved_scope_hash": None,
            "approval_token_id": None, "approval_chain_id": None, "binding_id": None,
            "token_use_policy": None, "nonce_ref": None,
            "bound_tenant_id": request["bound_tenant_id"],
            "bound_task_id": request["bound_task_id"],
            "bound_action_type": request["bound_action_type"],
            "bound_tool_scope": request["bound_tool_scope"], "bound_worker_id": None,
            "bound_requester_ref": request["bound_requester_ref"],
            "bound_approver_ref": session["binding_id"] if session else None,
            "blocked_mvp_action": False, "denial_reason": denial_reason,
            "fresh_operator_intent_ref": fresh_intent, "policy_version": POLICY_VERSION,
            "evidence_artifact_ids": [evidence_id], "decided_at": decided_at,
            "decision_kind": decision_kind,
            "operator_session_binding_id": session["binding_id"] if session else None,
            "approval_binding_created": False, "token_verification_performed": False,
            "replay_record_created": False, "assigned_worker_id": None,
            "arc_dispatch_allowed": False, "arc_dispatched": False,
            "external_side_effects": False,
        }
        self.validator.validate(updated, "approval.request")
        self.validator.validate(result, "approval.result")
        guardian_evidence = self.store.record_event(
            "office_non_authorizing_approval_decision_guardian_allowed",
            {**safe, "guardian_decision_id": decision["decision_id"],
             "pre_action_evidence_ref": pre})
        post = f"harness-event:{uuid4().hex}"
        try:
            self.store.commit_office_non_authorizing_approval_decision(
                updated, result, expected_request_hash=expected_request_hash,
                event_id=post, event_type="office_non_authorizing_approval_decision_recorded",
                event_payload={**safe, "approval_result_id": result_id,
                    "guardian_decision_id": decision["decision_id"],
                    "guardian_evidence_ref": guardian_evidence,
                    "request_record_sha256": _digest(updated),
                    "result_record_sha256": _digest(result)})
        except Exception as exc:
            raise ApprovalDecisionError(
                "Decision records and completion evidence could not be committed atomically.") from exc
        return {"request": updated, "result": result}

    def _require_current_source(self, request: Mapping[str, Any]) -> None:
        preview = self.store.office_approval_preview(request["source_approval_preview_id"])
        proposal = self.store.office_proposal(request["task_id"])
        if preview is None or proposal is None:
            raise ApprovalDecisionError("Source records are unavailable; decision denied.")
        self.validator.validate(preview, "supervisor.approval.preview")
        self.validator.validate(proposal, "supervisor.task.proposal")
        if not all((preview["revision"] == request["source_approval_preview_revision"],
                    _digest(preview) == request["source_approval_preview_hash"],
                    preview["state"] == "reviewed_no_authority",
                    preview["source_proposal_revision"] == proposal["revision"],
                    preview["source_proposal_hash"] == _digest(proposal),
                    proposal["tenant_id"] == self.tenant_id)):
            raise ApprovalDecisionError("Source records changed; reload before deciding.")

    def _guardian_context(self, request: Mapping[str, Any], action: str,
                          result: str, session: Mapping[str, Any] | None,
                          evidence_id: str, pre: str, token: str,
                          expired: bool) -> dict[str, Any]:
        attended = session is not None
        return {
            "decision_id": f"gd-non-authorizing-approval:{token}",
            "request_id": f"request-non-authorizing-approval:{token}",
            "approval_request_id": request["approval_request_id"],
            "tenant_id": self.tenant_id, "customer_context_id": self.customer_context_id,
            "requested_by": ({"actor_type": "operator", "actor_id": session["operator_id"]}
                             if session else {"actor_type": "supervisor", "actor_id": "expiry-recorder"}),
            "subject": {"subject_type": "task", "subject_id": request["task_id"]},
            "schema_action_class": "internal_approval_decision",
            "resource_ref": {"resource_type": "approval_request",
                             "resource_id": request["approval_request_id"],
                             "resource_scope": "task_scoped"},
            "data_classification": "synthetic_fixture_only", "risk_tier": "medium",
            "policy_refs": ["policy.non.authorizing.approval.decision.lab.v1",
                            "policy.guardian.syscall_gate.v1"],
            "policy_version": POLICY_VERSION,
            "valid_for_action_ref": request["approval_request_id"],
            "decision_scope_hash": request["scope_hash"],
            "bound_tenant_id": self.tenant_id, "bound_task_id": request["task_id"],
            "bound_worker_id": None,
            "bound_action_type": "office_non_authorizing_approval_decision",
            "bound_tool_scope": request["bound_tool_scope"],
            "execution_mode": "decision_metadata_only", "external_effect": "none",
            "evidence_required": True, "evidence_artifact_id": evidence_id,
            "evidence_artifact_ids": [evidence_id], "pre_action_evidence_refs": [evidence_id],
            "post_action_evidence_refs": [evidence_id], "storage_evidence_ref": pre,
            "operation": action, "result": result, "non_authorizing": True,
            "request_pending": True, "request_expired": expired,
            "attended": attended, "operator_confirmation": True,
            "operator_session_active": attended,
            "operator_session_binding_id": session["binding_id"] if session else None,
            "fresh_intent": True, "synthetic_data_only": True,
            "approval_result_created": True, "approval_token_access_allowed": False,
            "approval_binding_allowed": False, "token_verification_allowed": False,
            "replay_record_allowed": False, "model_call_allowed": False,
            "tool_execution_allowed": False, "arc_dispatch_allowed": False,
            "connector_access_allowed": False, "submission_allowed": False,
            "external_side_effects": False, "approval_required": False,
        }
