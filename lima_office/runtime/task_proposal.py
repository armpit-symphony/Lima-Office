"""Guardian-gated, tokenless Supervisor task proposals for the Phase 0 lab."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Protocol
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.guardian import GuardianPolicy


CREATE_CONFIRMATION = "CREATE SYNTHETIC TASK DRAFT"
EDIT_CONFIRMATION = "EDIT SYNTHETIC TASK DRAFT"
TRANSITION_CONFIRMATION = "CHANGE SYNTHETIC TASK STATE"
POLICY_VERSION = "policy-supervisor-task-proposal-lab-v1"
ALLOWED_PRIORITIES = ("low", "normal")
ALLOWED_STEP_IDS = (
    "review_synthetic_scenario",
    "resolve_human_input_fields",
    "owner_review_prepared_form",
)
TRANSITIONS = {
    ("draft", "propose"): ("proposed", "none", "task_proposal_proposed"),
    ("draft", "cancel"): ("cancelled", "cancelled", "task_proposal_cancelled"),
    ("proposed", "accept"): (
        "accepted_for_future_approval",
        "accepted",
        "task_proposal_accepted_for_future_approval",
    ),
    ("proposed", "deny"): ("denied", "denied", "task_proposal_denied"),
    ("proposed", "cancel"): ("cancelled", "cancelled", "task_proposal_cancelled"),
}


class TaskProposalError(RuntimeError):
    """Safe, operator-visible failure for the bounded proposal surface."""


class ProposalStore(Protocol):
    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str: ...

    def office_proposal(self, proposal_id: str) -> dict[str, Any] | None: ...

    def office_proposals(self, limit: int = 50) -> list[dict[str, Any]]: ...

    def commit_office_proposal(
        self,
        proposal: Mapping[str, Any],
        *,
        event_id: str,
        event_type: str,
        event_payload: Mapping[str, Any],
        expected_revision: int | None,
    ) -> str: ...


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat().replace("+00:00", "Z")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class OfficeTaskProposalService:
    """Create and review synthetic plans without granting execution authority."""

    def __init__(
        self,
        store: ProposalStore,
        *,
        tenant_id: str = "tenant-lab-001",
        customer_context_id: str = "customer-context-main",
        validator: ContractValidator | None = None,
        guardian: GuardianPolicy | None = None,
    ) -> None:
        self.store = store
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.validator = validator or ContractValidator()
        self.guardian = guardian or GuardianPolicy()

    def state_summary(self) -> dict[str, Any]:
        proposals = self.store.office_proposals(limit=50)
        for proposal in proposals:
            self.validator.validate(proposal, "supervisor.task.proposal")
        return {
            "runtime_enabled": True,
            "synthetic_data_only": True,
            "free_form_content_allowed": False,
            "approval_tokens_enabled": False,
            "arc_dispatch_enabled": False,
            "allowed_priorities": list(ALLOWED_PRIORITIES),
            "allowed_step_ids": list(ALLOWED_STEP_IDS),
            "proposals": proposals,
        }

    def create_from_helper(
        self, *, helper_result: Any, confirmation: Any
    ) -> dict[str, Any]:
        if confirmation != CREATE_CONFIRMATION:
            raise TaskProposalError("Explicit synthetic task-draft confirmation is required.")
        if not isinstance(helper_result, Mapping):
            raise TaskProposalError("A current synthetic helper result is required.")
        source = dict(helper_result)
        self.validator.validate(source, "helper.result")
        self._require_safe_helper_result(source)
        if (
            source.get("tenant_id") != self.tenant_id
            or source.get("customer_context_id") != self.customer_context_id
        ):
            raise TaskProposalError("Helper result belongs to a different tenant context.")
        if any(
            item.get("source_helper_result_id") == source["helper_result_id"]
            for item in self.store.office_proposals(limit=100)
        ):
            raise TaskProposalError("That helper result already has a task proposal.")

        token = uuid4().hex
        proposal_id = f"task-proposal:{token}"
        now = _now()
        issue_fields = sorted(
            {
                finding["field"]
                for finding in source.get("findings", [])
                if isinstance(finding, Mapping) and isinstance(finding.get("field"), str)
            }
        )
        return self._commit_change(
            operation="create",
            proposal_id=proposal_id,
            expected_revision=None,
            reason_code="task_proposal_created",
            base={
                "source_helper_result_id": source["helper_result_id"],
                "scenario_id": source["scenario_id"],
                "task_class": "form_preparation",
                "priority": "normal",
                "selected_step_ids": list(ALLOWED_STEP_IDS),
                "issue_fields": issue_fields,
                "human_input_required": bool(source.get("findings")),
                "state": "draft",
                "owner_decision": "none",
                "created_at": _timestamp(now),
            },
            now=now,
        )

    def edit(
        self,
        *,
        proposal_id: Any,
        expected_revision: Any,
        priority: Any,
        selected_step_ids: Any,
        confirmation: Any,
    ) -> dict[str, Any]:
        if confirmation != EDIT_CONFIRMATION:
            raise TaskProposalError("Explicit task-draft edit confirmation is required.")
        current = self._current(proposal_id, expected_revision)
        if current["state"] != "draft":
            raise TaskProposalError("Only a draft proposal can be edited.")
        if priority not in ALLOWED_PRIORITIES:
            raise TaskProposalError("Task priority must be low or normal.")
        steps = self._validated_steps(selected_step_ids)
        base = dict(current)
        base["priority"] = priority
        base["selected_step_ids"] = steps
        return self._commit_change(
            operation="edit",
            proposal_id=current["proposal_id"],
            expected_revision=current["revision"],
            reason_code="task_proposal_edited",
            base=base,
            now=_now(),
        )

    def transition(
        self,
        *,
        proposal_id: Any,
        expected_revision: Any,
        action: Any,
        confirmation: Any,
    ) -> dict[str, Any]:
        if confirmation != TRANSITION_CONFIRMATION:
            raise TaskProposalError("Explicit task-state confirmation is required.")
        current = self._current(proposal_id, expected_revision)
        if not isinstance(action, str):
            raise TaskProposalError("A fixed proposal state action is required.")
        transition = TRANSITIONS.get((current["state"], action))
        if transition is None:
            raise TaskProposalError("That proposal state transition is not allowed.")
        next_state, owner_decision, reason_code = transition
        base = dict(current)
        base["state"] = next_state
        base["owner_decision"] = owner_decision
        return self._commit_change(
            operation=str(action),
            proposal_id=current["proposal_id"],
            expected_revision=current["revision"],
            reason_code=reason_code,
            base=base,
            now=_now(),
        )

    def _current(self, proposal_id: Any, expected_revision: Any) -> dict[str, Any]:
        if not isinstance(proposal_id, str) or not proposal_id.startswith("task-proposal:"):
            raise TaskProposalError("A valid task proposal id is required.")
        if (
            not isinstance(expected_revision, int)
            or isinstance(expected_revision, bool)
            or expected_revision < 1
        ):
            raise TaskProposalError("A positive expected revision is required.")
        current = self.store.office_proposal(proposal_id)
        if current is None:
            raise TaskProposalError("Task proposal was not found.")
        self.validator.validate(current, "supervisor.task.proposal")
        if current["revision"] != expected_revision:
            raise TaskProposalError("Task proposal changed; reload before trying again.")
        return current

    @staticmethod
    def _validated_steps(value: Any) -> list[str]:
        if not isinstance(value, list) or not value:
            raise TaskProposalError("Select at least one fixed task step.")
        if any(not isinstance(item, str) or item not in ALLOWED_STEP_IDS for item in value):
            raise TaskProposalError("Only the fixed synthetic task steps are allowed.")
        if len(set(value)) != len(value):
            raise TaskProposalError("Task steps must not be duplicated.")
        return [step for step in ALLOWED_STEP_IDS if step in value]

    @staticmethod
    def _require_safe_helper_result(source: Mapping[str, Any]) -> None:
        required_true = ("synthetic_data_only", "deterministic_review", "human_review_required")
        required_false = (
            "raw_profile_included", "model_called", "tools_used", "memory_used",
            "approval_requested", "arc_dispatched", "connector_accessed",
            "submission_allowed", "external_side_effects",
        )
        if source.get("status") != "completed" or any(source.get(key) is not True for key in required_true):
            raise TaskProposalError("Helper result is not an eligible synthetic completed result.")
        if any(source.get(key) is not False for key in required_false):
            raise TaskProposalError("Helper result contains capability use outside this proposal boundary.")

    def _commit_change(
        self,
        *,
        operation: str,
        proposal_id: str,
        expected_revision: int | None,
        reason_code: str,
        base: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any]:
        revision = 1 if expected_revision is None else expected_revision + 1
        evidence_token = uuid4().hex
        formal_evidence_id = f"ev-task-proposal:{evidence_token}"
        safe_evidence = {
            "proposal_id": proposal_id,
            "operation": operation,
            "expected_revision": expected_revision,
            "next_revision": revision,
            "reason_code": reason_code,
            "synthetic_data_only": True,
            "free_form_content_included": False,
            "approval_token_issued": False,
            "arc_dispatched": False,
            "external_side_effects": False,
        }
        try:
            pre_evidence = self.store.record_event(
                "office_task_proposal_change_requested", safe_evidence
            )
        except Exception as exc:
            raise TaskProposalError(
                "Pre-action evidence could not be written; proposal change denied."
            ) from exc

        decision = self.guardian.decide(
            "office_task_proposal_manage",
            self._guardian_context(
                proposal_id=proposal_id,
                operation=operation,
                evidence_id=formal_evidence_id,
                storage_evidence_ref=pre_evidence,
                token=evidence_token,
            ),
        )
        self.validator.validate(decision, "guardian.decision")
        if decision["decision"] not in {"allow", "allow_with_evidence"}:
            raise TaskProposalError("Guardian denied the task proposal change.")
        try:
            guardian_evidence = self.store.record_event(
                "office_task_proposal_change_authorized",
                {
                    **safe_evidence,
                    "guardian_decision_id": decision["decision_id"],
                    "guardian_decision": decision["decision"],
                    "pre_action_evidence_ref": pre_evidence,
                },
            )
        except Exception as exc:
            raise TaskProposalError(
                "Guardian evidence could not be written; proposal change denied."
            ) from exc

        post_evidence = f"harness-event:{uuid4().hex}"
        proposal = {
            key: value
            for key, value in base.items()
            if key
            not in {
                "contract_name", "contract_version", "schema_version", "taxonomy_version",
                "tenant_id", "customer_context_id", "environment", "correlation_id",
                "causation_id", "idempotency_key", "producer", "policy_version",
                "revision", "transition_reason_codes", "guardian_decision_id",
                "pre_action_evidence_ref", "post_action_evidence_ref", "updated_at",
            }
        }
        proposal.update(
            {
                "contract_name": "supervisor.task.proposal",
                "contract_version": "1.0.0",
                "schema_version": "1.0.0",
                "taxonomy_version": "taxonomy-reason-v1",
                "tenant_id": self.tenant_id,
                "customer_context_id": self.customer_context_id,
                "environment": "phase0_lab",
                "correlation_id": f"corr-{proposal_id}",
                "causation_id": str(base["source_helper_result_id"]),
                "idempotency_key": f"idem-{proposal_id}-r{revision}",
                "producer": {"component": "supervisor", "produced_at": _timestamp(now)},
                "policy_version": POLICY_VERSION,
                "proposal_id": proposal_id,
                "revision": revision,
                "transition_reason_codes": [reason_code],
                "guardian_decision_id": decision["decision_id"],
                "pre_action_evidence_ref": pre_evidence,
                "post_action_evidence_ref": post_evidence,
                "synthetic_data_only": True,
                "free_form_content_allowed": False,
                "approval_required_for_future_execution": True,
                "approval_token_issued": False,
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
        self.validator.validate(proposal, "supervisor.task.proposal")
        completion = {
            **safe_evidence,
            "state": proposal["state"],
            "owner_decision": proposal["owner_decision"],
            "guardian_decision_id": decision["decision_id"],
            "guardian_evidence_ref": guardian_evidence,
            "record_sha256": _digest(proposal),
        }
        try:
            self.store.commit_office_proposal(
                proposal,
                event_id=post_evidence,
                event_type="office_task_proposal_change_committed",
                event_payload=completion,
                expected_revision=expected_revision,
            )
        except Exception as exc:
            raise TaskProposalError(
                "Proposal and completion evidence could not be committed atomically."
            ) from exc
        return proposal

    def _guardian_context(
        self,
        *,
        proposal_id: str,
        operation: str,
        evidence_id: str,
        storage_evidence_ref: str,
        token: str,
    ) -> dict[str, Any]:
        return {
            "decision_id": f"gd-task-proposal:{token}",
            "request_id": f"request-task-proposal:{token}",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "subject": {"subject_type": "task", "subject_id": proposal_id},
            "schema_action_class": "internal_task_proposal",
            "resource_ref": {
                "resource_type": "task_proposal",
                "resource_id": proposal_id,
                "resource_scope": "task_scoped",
            },
            "data_classification": "synthetic_fixture_only",
            "risk_tier": "low",
            "policy_refs": [
                "policy.supervisor.task_proposal.v1",
                "policy.guardian.syscall_gate.v1",
            ],
            "policy_version": POLICY_VERSION,
            "valid_for_action_ref": f"{proposal_id}:{operation}",
            "decision_scope_hash": _digest({"proposal_id": proposal_id, "operation": operation}),
            "bound_action_type": "office_task_proposal_manage",
            "bound_tool_scope": {
                "resource_refs": [proposal_id],
                "allowed_operations": [operation],
                "prohibited_operations": [
                    "approval_token_request", "worker_assignment", "arc_dispatch",
                    "model_call", "tool_use", "connector_access", "form_submission",
                ],
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
            "model_call_allowed": False,
            "tool_execution_allowed": False,
            "approval_token_access_allowed": False,
            "arc_dispatch_allowed": False,
            "connector_access_allowed": False,
            "submission_allowed": False,
            "approval_required": False,
        }
