"""Deterministic, Guardian-gated Office Operations Helper for the lab."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import threading
from typing import Any, Protocol
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.guardian import GuardianPolicy
from lima_office.runtime.registration_practice import catalog, run_scenario


HELPER_CONFIRMATION = "RUN SYNTHETIC HELPER REVIEW"
HELPER_AGENT_ID = "office-operations-helper-001"
HELPER_SCOPE_ID = "helper-scope-office-operations-001"
POLICY_VERSION = "policy-office-helper-lab-v1"
ALLOWED_PREVIEW_WORK = (
    "sop_review",
    "task_decomposition",
    "missing_field_check",
    "draft_review",
    "arc_result_review",
)
BLOCKED_CAPABILITIES = (
    "external_send",
    "file_delete",
    "file_overwrite",
    "customer_record_update",
    "software_install_update",
    "production_remediation",
    "production_server_touch",
    "payment_or_regulated_system",
    "cross_tenant_memory",
    "unrestricted_tool_execution",
    "model_call",
    "worker_dispatch",
    "approval_token_request",
    "browser_automation",
    "form_submission",
)


class OfficeHelperError(RuntimeError):
    """Safe, operator-visible failure for the bounded helper surface."""


class EvidenceStore(Protocol):
    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str: ...


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat().replace("+00:00", "Z")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class OfficeOperationsHelperService:
    """Review one fixed synthetic registration scenario without model or tools."""

    def __init__(
        self,
        store: EvidenceStore,
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
        self._review_lock = threading.Lock()
        self._last_review: dict[str, Any] | None = None
        self._last_result: dict[str, Any] | None = None

    def proposal_source(self, helper_result_id: Any) -> dict[str, Any]:
        if (
            not isinstance(helper_result_id, str)
            or self._last_result is None
            or self._last_result.get("helper_result_id") != helper_result_id
        ):
            raise OfficeHelperError(
                "Run a synthetic helper review in this process before creating a task draft."
            )
        return deepcopy(self._last_result)

    def state_summary(self) -> dict[str, Any]:
        scenarios = [
            {"scenario_id": item["scenario_id"], "title": item["title"]}
            for item in catalog()["scenarios"]
        ]
        return {
            "role": "office_operations_helper",
            "status": "ready",
            "runtime_enabled": True,
            "review_type": "registration_sop_review",
            "supervisor_side_only": True,
            "independent_worker": False,
            "requires_confirmation": True,
            "synthetic_data_only": True,
            "deterministic_review": True,
            "model_calls_enabled": False,
            "tools_enabled": False,
            "memory_enabled": False,
            "may_dispatch_workers": False,
            "may_request_approval_token": False,
            "external_side_effects": False,
            "allowed_preview_work": list(ALLOWED_PREVIEW_WORK),
            "scenarios": scenarios,
            "last_review": dict(self._last_review) if self._last_review else None,
        }

    def review_registration(self, *, scenario_id: Any, confirmation: Any) -> dict[str, Any]:
        if not self._review_lock.acquire(blocking=False):
            raise OfficeHelperError("An Office Helper review is already running.")
        try:
            return self._review_registration(
                scenario_id=scenario_id,
                confirmation=confirmation,
            )
        finally:
            self._review_lock.release()

    def _review_registration(self, *, scenario_id: Any, confirmation: Any) -> dict[str, Any]:
        known = {item["scenario_id"] for item in catalog()["scenarios"]}
        if not isinstance(scenario_id, str) or scenario_id not in known:
            raise OfficeHelperError("Select a fixed synthetic registration scenario.")
        if confirmation != HELPER_CONFIRMATION:
            raise OfficeHelperError("Explicit synthetic helper confirmation is required.")

        started = _now()
        token = uuid4().hex
        request_id = f"helper-request:{token}"
        assignment_id = f"helper-assignment:{token}"
        result_id = f"helper-result:{token}"
        correlation_id = f"corr-helper:{token}"
        formal_evidence_id = f"ev-helper-request:{token}"
        try:
            pre_evidence = self.store.record_event(
                "office_helper_review_requested",
                {
                    "request_id": request_id,
                    "assignment_id": assignment_id,
                    "evidence_artifact_id": formal_evidence_id,
                    "review_type": "registration_sop_review",
                    "scenario_id": scenario_id,
                    "synthetic_data_only": True,
                    "operator_confirmation": True,
                    "model_call_allowed": False,
                    "tool_execution_allowed": False,
                    "arc_dispatch_allowed": False,
                    "external_side_effects": False,
                },
            )
        except Exception as exc:
            raise OfficeHelperError(
                "Pre-action evidence could not be written; helper review denied."
            ) from exc

        decision = self.guardian.decide(
            "helper_synthetic_review",
            self._guardian_context(
                request_id=request_id,
                assignment_id=assignment_id,
                scenario_id=scenario_id,
                token=token,
                formal_evidence_id=formal_evidence_id,
                storage_evidence_ref=pre_evidence,
            ),
        )
        self.validator.validate(decision, "guardian.decision")
        if decision["decision"] not in {"allow", "allow_with_evidence"}:
            raise OfficeHelperError("Guardian denied the Office Helper review.")
        try:
            guardian_evidence = self.store.record_event(
                "office_helper_review_authorized",
                {
                    "request_id": request_id,
                    "assignment_id": assignment_id,
                    "guardian_decision_id": decision["decision_id"],
                    "guardian_decision": decision["decision"],
                    "pre_action_evidence_ref": pre_evidence,
                    "synthetic_data_only": True,
                    "deterministic_review": True,
                    "model_called": False,
                    "tools_used": False,
                },
            )
        except Exception as exc:
            raise OfficeHelperError(
                "Guardian evidence could not be written; helper review denied."
            ) from exc

        scope = self._scope(
            correlation_id=correlation_id,
            assignment_id=assignment_id,
            decision_id=decision["decision_id"],
            evidence_id=formal_evidence_id,
            started=started,
        )
        assignment = self._assignment(
            correlation_id=correlation_id,
            assignment_id=assignment_id,
            request_id=request_id,
            scenario_id=scenario_id,
            decision_id=decision["decision_id"],
            pre_evidence=pre_evidence,
            started=started,
        )
        self.validator.validate(scope, "helper.scope")
        self.validator.validate(assignment, "helper.assignment")

        practice = run_scenario(scenario_id)
        findings = [
            {
                "field": item["field"],
                "status": item["status"],
                "reason_code": item["reason_code"],
            }
            for item in practice["issues"]
        ]
        recommendations = self._recommendations(findings)
        steps = [
            "Review the fixed synthetic scenario against the registration SOP.",
            "Resolve every NEEDS_HUMAN_INPUT field with an attended human decision.",
            "Present the prepared form for owner review without submitting it.",
        ]
        disposition = "needs_human_input" if findings else "ready_for_owner_review"
        reason_codes = ["helper_review_completed"]
        reason_codes.append(
            "helper_human_input_required"
            if findings
            else "helper_ready_for_owner_review"
        )
        output_digest = _digest(
            {
                "scenario_id": scenario_id,
                "findings": findings,
                "recommendations": recommendations,
                "steps": steps,
            }
        )
        try:
            post_evidence = self.store.record_event(
                "office_helper_review_completed",
                {
                    "request_id": request_id,
                    "assignment_id": assignment_id,
                    "helper_result_id": result_id,
                    "guardian_decision_id": decision["decision_id"],
                    "guardian_evidence_ref": guardian_evidence,
                    "scenario_id": scenario_id,
                    "disposition": disposition,
                    "finding_count": len(findings),
                    "recommendation_count": len(recommendations),
                    "result_sha256": output_digest,
                    "raw_profile_included": False,
                    "model_called": False,
                    "tools_used": False,
                    "memory_used": False,
                    "arc_dispatched": False,
                    "external_side_effects": False,
                },
            )
        except Exception as exc:
            raise OfficeHelperError(
                "Post-action evidence failed; helper result withheld."
            ) from exc

        completed = _now()
        result = {
            "contract_name": "helper.result",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-reason-v1",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": correlation_id,
            "causation_id": assignment_id,
            "idempotency_key": f"idem-{result_id}",
            "producer": {"component": "supervisor", "produced_at": _timestamp(completed)},
            "policy_version": POLICY_VERSION,
            "helper_result_id": result_id,
            "assignment_id": assignment_id,
            "request_id": request_id,
            "helper_scope_id": HELPER_SCOPE_ID,
            "helper_agent_id": HELPER_AGENT_ID,
            "helper_role": "office_operations_helper",
            "review_type": "registration_sop_review",
            "scenario_id": scenario_id,
            "status": "completed",
            "disposition": disposition,
            "reason_codes": reason_codes,
            "findings": findings,
            "recommendations": recommendations,
            "proposed_task_steps": steps,
            "guardian_decision_id": decision["decision_id"],
            "pre_action_evidence_ref": pre_evidence,
            "post_action_evidence_ref": post_evidence,
            "human_review_required": True,
            "synthetic_data_only": True,
            "deterministic_review": True,
            "raw_profile_included": False,
            "model_called": False,
            "tools_used": False,
            "memory_used": False,
            "approval_requested": False,
            "arc_dispatched": False,
            "connector_accessed": False,
            "submission_allowed": False,
            "external_side_effects": False,
            "created_at": _timestamp(started),
            "completed_at": _timestamp(completed),
        }
        self.validator.validate(result, "helper.result")
        self._last_review = {
            "helper_result_id": result_id,
            "scenario_id": scenario_id,
            "status": "completed",
            "disposition": disposition,
            "finding_count": len(findings),
            "guardian_decision_id": decision["decision_id"],
            "evidence_ref": post_evidence,
            "completed_at": _timestamp(completed),
        }
        self._last_result = deepcopy(result)
        return result

    @staticmethod
    def _recommendations(findings: list[dict[str, str]]) -> list[str]:
        if not findings:
            return [
                "All fixed synthetic fields passed deterministic checks; complete human review before any later action.",
                "Keep external submission blocked in this lab helper slice.",
            ]
        recommendations = []
        for finding in findings:
            field = finding["field"].replace("_", " ")
            if finding["reason_code"] == "missing_value":
                recommendations.append(
                    f"Request the missing {field} value from a human; do not invent it."
                )
            elif finding["reason_code"] == "consent_not_granted":
                recommendations.append(
                    "Preserve the contact refusal and stop before contact or submission."
                )
            else:
                recommendations.append(
                    f"Ask a human to correct {field}; do not repair or guess it."
                )
        recommendations.append(
            "Keep external submission blocked until the owner reviews the prepared form."
        )
        return recommendations

    def _guardian_context(
        self, *, request_id: str, assignment_id: str, scenario_id: str,
        token: str, formal_evidence_id: str, storage_evidence_ref: str,
    ) -> dict[str, Any]:
        return {
            "decision_id": f"gd-helper-review:{token}",
            "request_id": request_id,
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "subject": {"subject_type": "helper_agent", "subject_id": HELPER_AGENT_ID},
            "schema_action_class": "internal_helper_review",
            "resource_ref": {"resource_type": "synthetic_registration_scenario", "resource_id": scenario_id, "resource_scope": "fixed_lab_fixture"},
            "data_classification": "synthetic_fixture_only",
            "risk_tier": "low",
            "policy_refs": ["policy.office_helper.synthetic_review.v1", "policy.guardian.syscall_gate.v1"],
            "policy_version": POLICY_VERSION,
            "valid_for_action_ref": assignment_id,
            "decision_scope_hash": _digest({"scenario_id": scenario_id}),
            "bound_action_type": "helper_synthetic_review",
            "bound_tool_scope": {"resource_refs": [scenario_id], "allowed_operations": ["deterministic_registration_review"], "prohibited_operations": ["model_call", "tool_use", "memory_access", "worker_dispatch", "approval_token_request", "connector_access", "form_submission"]},
            "execution_mode": "plan_only",
            "external_effect": "none",
            "evidence_required": True,
            "evidence_artifact_id": formal_evidence_id,
            "evidence_artifact_ids": [formal_evidence_id],
            "pre_action_evidence_refs": [formal_evidence_id],
            "post_action_evidence_refs": [formal_evidence_id],
            "storage_evidence_ref": storage_evidence_ref,
            "attended": True,
            "operator_confirmation": True,
            "helper_role": "office_operations_helper",
            "review_type": "registration_sop_review",
            "synthetic_data_only": True,
            "deterministic_review": True,
            "model_call_allowed": False,
            "tool_execution_allowed": False,
            "memory_access_allowed": False,
            "approval_token_access_allowed": False,
            "arc_dispatch_allowed": False,
            "connector_access_allowed": False,
            "submission_allowed": False,
            "approval_required": False,
        }

    def _scope(
        self, *, correlation_id: str, assignment_id: str, decision_id: str,
        evidence_id: str, started: datetime,
    ) -> dict[str, Any]:
        return {
            "contract_name": "helper.scope", "contract_version": "1.0.0", "schema_version": "1.0.0",
            "tenant_id": self.tenant_id, "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab", "correlation_id": correlation_id,
            "causation_id": assignment_id, "idempotency_key": f"idem-{HELPER_SCOPE_ID}-{assignment_id}",
            "producer": {"component": "supervisor", "produced_at": _timestamp(started)},
            "helper_scope_id": HELPER_SCOPE_ID, "helper_agent_id": HELPER_AGENT_ID,
            "helper_role": "office_operations_helper", "parent_supervisor_id": "supervisor-lab-001",
            "delegated_by_actor": {"actor_type": "supervisor", "actor_id": "supervisor-lab-001"},
            "supervisor_side_only": True, "independent_worker": False,
            "allowed_task_classes": list(ALLOWED_PREVIEW_WORK), "allowed_tool_packs": [],
            "blocked_tool_packs": ["unrestricted_browser", "unrestricted_filesystem", "unrestricted_network", "live_connector_write", "production_remediation", "payment_or_regulated_system"],
            "data_classifications_allowed": ["synthetic_fixture_only"],
            "connector_access": "none", "network_scope": "none", "file_scope": "none",
            "memory_scope": {"tenant_namespace": self.tenant_id, "read_allowed": False, "write_summary_allowed": False, "delete_or_export_allowed": False, "raw_content_allowed": False},
            "may_request_approval_token": False, "approval_required_capabilities": [],
            "blocked_capabilities": list(BLOCKED_CAPABILITIES), "status": "active",
            "lease_expires_at": _timestamp(started + timedelta(minutes=10)),
            "revoked_at": None, "revocation_reason": None,
            "guardian_decision_id": decision_id, "policy_version": POLICY_VERSION,
            "evidence_artifact_ids": [evidence_id], "created_at": _timestamp(started),
        }

    def _assignment(
        self, *, correlation_id: str, assignment_id: str, request_id: str,
        scenario_id: str, decision_id: str, pre_evidence: str, started: datetime,
    ) -> dict[str, Any]:
        return {
            "contract_name": "helper.assignment", "contract_version": "1.0.0", "schema_version": "1.0.0", "taxonomy_version": "taxonomy-reason-v1",
            "tenant_id": self.tenant_id, "customer_context_id": self.customer_context_id, "environment": "phase0_lab",
            "correlation_id": correlation_id, "causation_id": None, "idempotency_key": f"idem-{assignment_id}",
            "producer": {"component": "supervisor", "produced_at": _timestamp(started)}, "policy_version": POLICY_VERSION,
            "assignment_id": assignment_id, "request_id": request_id, "helper_scope_id": HELPER_SCOPE_ID,
            "helper_agent_id": HELPER_AGENT_ID, "helper_role": "office_operations_helper", "review_type": "registration_sop_review",
            "scenario_id": scenario_id, "data_classification": "synthetic_fixture_only", "status": "assigned",
            "reason_codes": ["helper_synthetic_review_assigned"], "guardian_decision_id": decision_id,
            "pre_action_evidence_ref": pre_evidence, "attended": True, "operator_confirmation": True,
            "synthetic_data_only": True, "deterministic_review": True, "model_call_allowed": False,
            "tool_execution_allowed": False, "memory_access_allowed": False, "approval_token_access_allowed": False,
            "arc_dispatch_allowed": False, "connector_access_allowed": False, "submission_allowed": False,
            "external_side_effects": False, "created_at": _timestamp(started),
        }
