"""Guardian-gated, tokenless approval-request previews for the Phase 0 lab."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Protocol
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.guardian import GuardianPolicy


CREATE_CONFIRMATION = "CREATE TOKENLESS APPROVAL PREVIEW"
TRANSITION_CONFIRMATION = "CHANGE TOKENLESS APPROVAL PREVIEW STATE"
POLICY_VERSION = "policy-supervisor-approval-preview-lab-v1"
PREVIEW_TTL_SECONDS = 900
ALLOWED_OPERATION = "review_prepared_form_plan"
PROHIBITED_OPERATIONS = (
    "create_real_approval_request",
    "issue_approval_token",
    "create_approval_binding",
    "assign_worker",
    "dispatch_arc",
    "model_call",
    "tool_use",
    "connector_access",
    "form_submission",
    "external_effect",
)
TRANSITIONS = {
    ("preview_ready", "review"): (
        "reviewed_no_authority",
        "reviewed_no_authority",
        "approval_preview_reviewed_no_authority",
    ),
    ("preview_ready", "deny"): (
        "denied",
        "denied",
        "approval_preview_denied",
    ),
    ("preview_ready", "withdraw"): (
        "withdrawn",
        "withdrawn",
        "approval_preview_withdrawn",
    ),
}


class ApprovalPreviewError(RuntimeError):
    """Safe, operator-visible failure for the tokenless preview surface."""


class ApprovalPreviewStore(Protocol):
    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str: ...

    def office_proposal(self, proposal_id: str) -> dict[str, Any] | None: ...

    def office_approval_preview(self, approval_preview_id: str) -> dict[str, Any] | None: ...

    def office_approval_previews(self, limit: int = 50) -> list[dict[str, Any]]: ...

    def commit_office_approval_preview(
        self,
        preview: Mapping[str, Any],
        *,
        event_id: str,
        event_type: str,
        event_payload: Mapping[str, Any],
        expected_revision: int | None,
    ) -> str: ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class OfficeApprovalPreviewService:
    """Preview a future approval request without creating authority artifacts."""

    def __init__(
        self,
        store: ApprovalPreviewStore,
        *,
        tenant_id: str = "tenant-lab-001",
        customer_context_id: str = "customer-context-main",
        validator: ContractValidator | None = None,
        guardian: GuardianPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store = store
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.validator = validator or ContractValidator()
        self.guardian = guardian or GuardianPolicy()
        self.clock = clock or _utc_now

    def state_summary(self) -> dict[str, Any]:
        now = self.clock()
        items = []
        for record in self.store.office_approval_previews(limit=50):
            self.validator.validate(record, "supervisor.approval.preview")
            item = dict(record)
            source_current = self._source_matches(record, raise_on_failure=False)
            expired = now >= _parse_timestamp(record["preview_expires_at"])
            item["source_current"] = source_current
            item["expired_for_review"] = expired
            item["review_available"] = (
                record["state"] == "preview_ready" and source_current and not expired
            )
            items.append(item)
        return {
            "runtime_enabled": True,
            "preview_only": True,
            "real_approval_requests_enabled": False,
            "approval_results_enabled": False,
            "approval_tokens_enabled": False,
            "approval_bindings_enabled": False,
            "token_verification_enabled": False,
            "replay_records_enabled": False,
            "arc_dispatch_enabled": False,
            "previews": items,
        }

    def create_from_proposal(
        self,
        *,
        proposal_id: Any,
        expected_proposal_revision: Any,
        confirmation: Any,
    ) -> dict[str, Any]:
        if confirmation != CREATE_CONFIRMATION:
            raise ApprovalPreviewError("Explicit tokenless preview confirmation is required.")
        proposal = self._proposal(proposal_id, expected_proposal_revision)
        if proposal["state"] != "accepted_for_future_approval":
            raise ApprovalPreviewError(
                "Only an accepted-for-future-approval proposal can create a preview."
            )
        if any(
            item.get("source_proposal_id") == proposal["proposal_id"]
            for item in self.store.office_approval_previews(limit=100)
        ):
            raise ApprovalPreviewError("That proposal already has an approval preview.")
        self._require_safe_proposal(proposal)

        now = self.clock()
        preview_id = f"approval-preview:{uuid4().hex}"
        scope_binding = {
            "source_proposal_id": proposal["proposal_id"],
            "source_proposal_revision": proposal["revision"],
            "priority": proposal["priority"],
            "selected_step_ids": proposal["selected_step_ids"],
            "issue_fields": proposal["issue_fields"],
            "allowed_operation": ALLOWED_OPERATION,
        }
        return self._commit_change(
            operation="create",
            preview_id=preview_id,
            expected_revision=None,
            reason_code="approval_preview_created",
            base={
                "source_proposal_id": proposal["proposal_id"],
                "source_proposal_revision": proposal["revision"],
                "source_proposal_state": proposal["state"],
                "source_proposal_hash": _digest(proposal),
                "state": "preview_ready",
                "review_outcome": "pending",
                "preview_scope": {
                    "requested_action_class": "form_preparation_review",
                    "external_effect": "none",
                    "resource_refs": [proposal["proposal_id"]],
                    "allowed_operations": [ALLOWED_OPERATION],
                    "prohibited_operations": list(PROHIBITED_OPERATIONS),
                    "data_classification": "synthetic_fixture_only",
                    "risk_tier": "low",
                    "scope_hash": _digest(scope_binding),
                    "max_uses": 0,
                },
                "approver_requirements": {
                    "approver_roles": ["business_owner"],
                    "identity_binding_required": True,
                    "identity_binding_status": "not_bound_in_preview",
                    "fresh_intent_required": True,
                    "separation_of_duties_review_required": True,
                },
                "future_request_policy": {
                    "guardian_recheck_required": True,
                    "proposal_revision_recheck_required": True,
                    "single_use_token_required_if_later_approved": True,
                    "suggested_request_ttl_seconds": PREVIEW_TTL_SECONDS,
                    "silent_promotion_allowed": False,
                },
                "preview_expires_at": _timestamp(
                    now + timedelta(seconds=PREVIEW_TTL_SECONDS)
                ),
                "created_at": _timestamp(now),
            },
            now=now,
        )

    def transition(
        self,
        *,
        approval_preview_id: Any,
        expected_revision: Any,
        action: Any,
        confirmation: Any,
    ) -> dict[str, Any]:
        if confirmation != TRANSITION_CONFIRMATION:
            raise ApprovalPreviewError("Explicit preview-state confirmation is required.")
        current = self._current(approval_preview_id, expected_revision)
        if not isinstance(action, str):
            raise ApprovalPreviewError("A fixed preview-state action is required.")
        transition = TRANSITIONS.get((current["state"], action))
        if transition is None:
            raise ApprovalPreviewError("That approval-preview state transition is not allowed.")
        self._source_matches(current, raise_on_failure=True)
        if action == "review" and self.clock() >= _parse_timestamp(current["preview_expires_at"]):
            raise ApprovalPreviewError(
                "The preview review window expired; no authority was created."
            )
        next_state, outcome, reason_code = transition
        base = dict(current)
        base["state"] = next_state
        base["review_outcome"] = outcome
        return self._commit_change(
            operation=action,
            preview_id=current["approval_preview_id"],
            expected_revision=current["revision"],
            reason_code=reason_code,
            base=base,
            now=self.clock(),
        )

    def _proposal(self, proposal_id: Any, expected_revision: Any) -> dict[str, Any]:
        if not isinstance(proposal_id, str) or not proposal_id.startswith("task-proposal:"):
            raise ApprovalPreviewError("A valid task proposal id is required.")
        if (
            not isinstance(expected_revision, int)
            or isinstance(expected_revision, bool)
            or expected_revision < 1
        ):
            raise ApprovalPreviewError("A positive proposal revision is required.")
        proposal = self.store.office_proposal(proposal_id)
        if proposal is None:
            raise ApprovalPreviewError("Task proposal was not found.")
        self.validator.validate(proposal, "supervisor.task.proposal")
        if proposal["revision"] != expected_revision:
            raise ApprovalPreviewError("Task proposal changed; reload before previewing it.")
        if (
            proposal["tenant_id"] != self.tenant_id
            or proposal["customer_context_id"] != self.customer_context_id
        ):
            raise ApprovalPreviewError("Task proposal belongs to a different tenant context.")
        return proposal

    def _current(self, preview_id: Any, expected_revision: Any) -> dict[str, Any]:
        if not isinstance(preview_id, str) or not preview_id.startswith("approval-preview:"):
            raise ApprovalPreviewError("A valid approval preview id is required.")
        if (
            not isinstance(expected_revision, int)
            or isinstance(expected_revision, bool)
            or expected_revision < 1
        ):
            raise ApprovalPreviewError("A positive expected revision is required.")
        current = self.store.office_approval_preview(preview_id)
        if current is None:
            raise ApprovalPreviewError("Approval preview was not found.")
        self.validator.validate(current, "supervisor.approval.preview")
        if current["revision"] != expected_revision:
            raise ApprovalPreviewError("Approval preview changed; reload before trying again.")
        return current

    @staticmethod
    def _require_safe_proposal(proposal: Mapping[str, Any]) -> None:
        required_false = (
            "approval_token_issued", "arc_dispatch_allowed", "arc_dispatched",
            "model_called", "tools_used", "connector_accessed",
            "submission_allowed", "external_side_effects",
        )
        if proposal.get("synthetic_data_only") is not True:
            raise ApprovalPreviewError("Only synthetic proposals are eligible for preview.")
        if proposal.get("free_form_content_allowed") is not False:
            raise ApprovalPreviewError("Free-form proposal content is outside this preview.")
        if proposal.get("assigned_worker_id") is not None:
            raise ApprovalPreviewError("Assigned proposals cannot enter the preview boundary.")
        if any(proposal.get(key) is not False for key in required_false):
            raise ApprovalPreviewError("Proposal contains authority outside this preview boundary.")

    def _source_matches(
        self, preview: Mapping[str, Any], *, raise_on_failure: bool
    ) -> bool:
        source = self.store.office_proposal(str(preview["source_proposal_id"]))
        matches = False
        if source is not None:
            try:
                self.validator.validate(source, "supervisor.task.proposal")
                matches = all(
                    (
                        source.get("tenant_id") == self.tenant_id,
                        source.get("customer_context_id") == self.customer_context_id,
                        source.get("state") == "accepted_for_future_approval",
                        source.get("revision") == preview.get("source_proposal_revision"),
                        _digest(source) == preview.get("source_proposal_hash"),
                    )
                )
            except Exception:
                matches = False
        if not matches and raise_on_failure:
            raise ApprovalPreviewError(
                "Source proposal no longer matches this preview; no authority was created."
            )
        return matches

    def _commit_change(
        self,
        *,
        operation: str,
        preview_id: str,
        expected_revision: int | None,
        reason_code: str,
        base: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any]:
        revision = 1 if expected_revision is None else expected_revision + 1
        evidence_token = uuid4().hex
        formal_evidence_id = f"ev-approval-preview:{evidence_token}"
        safe_evidence = {
            "approval_preview_id": preview_id,
            "source_proposal_id": base["source_proposal_id"],
            "source_proposal_revision": base["source_proposal_revision"],
            "operation": operation,
            "expected_revision": expected_revision,
            "next_revision": revision,
            "reason_code": reason_code,
            "preview_only": True,
            "real_approval_request_created": False,
            "approval_result_created": False,
            "approval_token_issued": False,
            "approval_binding_created": False,
            "assigned_worker_id": None,
            "arc_dispatched": False,
            "external_side_effects": False,
        }
        try:
            pre_evidence = self.store.record_event(
                "office_approval_preview_change_requested", safe_evidence
            )
        except Exception as exc:
            raise ApprovalPreviewError(
                "Pre-action evidence could not be written; preview change denied."
            ) from exc

        decision = self.guardian.decide(
            "office_approval_preview_manage",
            self._guardian_context(
                preview_id=preview_id,
                operation=operation,
                evidence_id=formal_evidence_id,
                storage_evidence_ref=pre_evidence,
                token=evidence_token,
            ),
        )
        self.validator.validate(decision, "guardian.decision")
        if decision["decision"] not in {"allow", "allow_with_evidence"}:
            raise ApprovalPreviewError("Guardian denied the approval preview change.")
        try:
            guardian_evidence = self.store.record_event(
                "office_approval_preview_change_authorized",
                {
                    **safe_evidence,
                    "guardian_decision_id": decision["decision_id"],
                    "guardian_decision": decision["decision"],
                    "pre_action_evidence_ref": pre_evidence,
                },
            )
        except Exception as exc:
            raise ApprovalPreviewError(
                "Guardian evidence could not be written; preview change denied."
            ) from exc

        post_evidence = f"harness-event:{uuid4().hex}"
        preview = {
            key: value
            for key, value in base.items()
            if key not in {
                "contract_name", "contract_version", "schema_version", "taxonomy_version",
                "tenant_id", "customer_context_id", "environment", "correlation_id",
                "causation_id", "idempotency_key", "producer", "policy_version",
                "approval_preview_id", "revision", "transition_reason_codes",
                "guardian_decision_id", "pre_action_evidence_ref",
                "post_action_evidence_ref", "updated_at", "source_current",
                "expired_for_review", "review_available",
            }
        }
        preview.update(
            {
                "contract_name": "supervisor.approval.preview",
                "contract_version": "1.0.0",
                "schema_version": "1.0.0",
                "taxonomy_version": "taxonomy-reason-v1",
                "tenant_id": self.tenant_id,
                "customer_context_id": self.customer_context_id,
                "environment": "phase0_lab",
                "correlation_id": f"corr-{preview_id}",
                "causation_id": str(base["source_proposal_id"]),
                "idempotency_key": f"idem-{preview_id}-r{revision}",
                "producer": {"component": "supervisor", "produced_at": _timestamp(now)},
                "policy_version": POLICY_VERSION,
                "approval_preview_id": preview_id,
                "revision": revision,
                "transition_reason_codes": [reason_code],
                "guardian_decision_id": decision["decision_id"],
                "pre_action_evidence_ref": pre_evidence,
                "post_action_evidence_ref": post_evidence,
                "synthetic_data_only": True,
                "free_form_content_allowed": False,
                "real_approval_request_created": False,
                "approval_result_created": False,
                "approval_token_issued": False,
                "approval_binding_created": False,
                "token_verification_performed": False,
                "replay_record_created": False,
                "assigned_worker_id": None,
                "arc_dispatch_allowed": False,
                "arc_dispatched": False,
                "model_called": False,
                "tools_used": False,
                "connector_accessed": False,
                "submission_allowed": False,
                "external_side_effects": False,
                "updated_at": _timestamp(now),
            }
        )
        self.validator.validate(preview, "supervisor.approval.preview")
        completion = {
            **safe_evidence,
            "state": preview["state"],
            "review_outcome": preview["review_outcome"],
            "guardian_decision_id": decision["decision_id"],
            "guardian_evidence_ref": guardian_evidence,
            "record_sha256": _digest(preview),
        }
        try:
            self.store.commit_office_approval_preview(
                preview,
                event_id=post_evidence,
                event_type="office_approval_preview_change_committed",
                event_payload=completion,
                expected_revision=expected_revision,
            )
        except Exception as exc:
            raise ApprovalPreviewError(
                "Preview and completion evidence could not be committed atomically."
            ) from exc
        return preview

    def _guardian_context(
        self,
        *,
        preview_id: str,
        operation: str,
        evidence_id: str,
        storage_evidence_ref: str,
        token: str,
    ) -> dict[str, Any]:
        return {
            "decision_id": f"gd-approval-preview:{token}",
            "request_id": f"request-approval-preview:{token}",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "subject": {"subject_type": "task", "subject_id": preview_id},
            "schema_action_class": "internal_approval_preview",
            "resource_ref": {
                "resource_type": "approval_preview",
                "resource_id": preview_id,
                "resource_scope": "task_scoped",
            },
            "data_classification": "synthetic_fixture_only",
            "risk_tier": "low",
            "policy_refs": [
                "policy.supervisor.approval_preview.v1",
                "policy.guardian.syscall_gate.v1",
            ],
            "policy_version": POLICY_VERSION,
            "valid_for_action_ref": f"{preview_id}:{operation}",
            "decision_scope_hash": _digest({"preview_id": preview_id, "operation": operation}),
            "bound_action_type": "office_approval_preview_manage",
            "bound_tool_scope": {
                "resource_refs": [preview_id],
                "allowed_operations": [operation],
                "prohibited_operations": list(PROHIBITED_OPERATIONS),
            },
            "execution_mode": "plan_only",
            "external_effect": "none",
            "evidence_required": True,
            "evidence_artifact_id": evidence_id,
            "evidence_artifact_ids": [evidence_id],
            "pre_action_evidence_refs": [evidence_id],
            "post_action_evidence_refs": [evidence_id],
            "storage_evidence_ref": storage_evidence_ref,
            "attended": True,
            "operator_confirmation": True,
            "operation": operation,
            "synthetic_data_only": True,
            "free_form_content_allowed": False,
            "preview_only": True,
            "real_approval_request_allowed": False,
            "approval_result_allowed": False,
            "approval_token_access_allowed": False,
            "approval_binding_allowed": False,
            "token_verification_allowed": False,
            "replay_record_allowed": False,
            "model_call_allowed": False,
            "tool_execution_allowed": False,
            "arc_dispatch_allowed": False,
            "connector_access_allowed": False,
            "submission_allowed": False,
            "approval_required": False,
        }
