"""In-memory evidence lifecycle simulator for the narrow Phase 1C slice."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import (
    EvidenceLifecycleTransitionError,
    EvidenceLifecycleValidationError,
    PolicyDenyError,
    UnsafeRuntimeActionError,
)
from lima_office.runtime.invariants import (
    DEFAULT_REFERENCE_TIME,
    assert_evidence_artifact_chain_consistent,
    assert_evidence_export_manifest_consistent,
    assert_guardian_decision_replay_safe,
    assert_token_verification_authorizes_task,
)


EVIDENCE_STATES = frozenset(
    {
        "planned",
        "pre_action_recorded",
        "post_action_recorded",
        "denial_recorded",
        "replay_denial_recorded",
        "failed_closed_recorded",
        "ledger_linked",
        "export_manifest_planned",
        "blocked",
        "rejected",
    }
)

ALLOWED_TRANSITIONS = {
    "planned": frozenset(
        {
            "pre_action_recorded",
            "denial_recorded",
            "replay_denial_recorded",
            "failed_closed_recorded",
            "blocked",
            "rejected",
        }
    ),
    "pre_action_recorded": frozenset({"post_action_recorded", "failed_closed_recorded", "blocked", "rejected"}),
    "post_action_recorded": frozenset({"ledger_linked"}),
    "denial_recorded": frozenset({"ledger_linked"}),
    "replay_denial_recorded": frozenset({"ledger_linked"}),
    "failed_closed_recorded": frozenset({"ledger_linked"}),
    "ledger_linked": frozenset({"export_manifest_planned"}),
    "export_manifest_planned": frozenset(),
    "blocked": frozenset(),
    "rejected": frozenset(),
}

CONTRACT_TO_SCHEMA = {
    "evidence.artifact": "evidence.artifact",
    "evidence.failure": "evidence.failure",
    "evidence.ledger.entry": "evidence.ledger.entry",
    "evidence.export_manifest": "evidence.export_manifest",
}

CONTRACT_ID_FIELD = {
    "evidence.artifact": "artifact_id",
    "evidence.failure": "evidence_failure_id",
    "evidence.ledger.entry": "ledger_entry_id",
    "evidence.export_manifest": "export_manifest_id",
}

EVIDENCE_REF_FIELDS = (
    "denial_evidence_ref",
    "pre_action_evidence_refs",
    "post_action_evidence_refs",
    "parent_evidence_refs",
    "related_evidence_artifact_ids",
    "evidence_refs",
    "included_evidence_refs",
    "excluded_evidence_refs",
    "conflict_evidence_refs",
)

COMPLETION_TASK_STATES = frozenset({"completed_mock", "evidence_recorded"})


@dataclass(frozen=True)
class EvidenceTransition:
    evidence_id: str
    tenant_id: str
    from_state: str | None
    to_state: str
    updated_at: str
    contract_name: str


class EvidenceLifecycleSimulator:
    """Validates and simulates evidence metadata lifecycle transitions in memory only."""

    def __init__(self, validator: ContractValidator, *, reference_time: str | None = DEFAULT_REFERENCE_TIME) -> None:
        self.validator = validator
        self.reference_time = reference_time
        self._counter = 0
        self._current: dict[str, dict[str, Any]] = {}
        self._history: dict[str, list[EvidenceTransition]] = {}
        self._tenant_by_evidence_ref: dict[str, str] = {}
        self._artifacts_by_id: dict[str, dict[str, Any]] = {}

    def register(
        self,
        payload: dict[str, Any],
        *,
        initial_state: str = "planned",
        evidence_id: str | None = None,
    ) -> dict[str, Any]:
        normalized = self._normalize_payload(payload, evidence_id=evidence_id)
        record_id = normalized["record_id"]
        tenant_id = normalized["tenant_id"]
        validated = normalized["payload"]
        contract_name = normalized["contract_name"]

        if record_id in self._current:
            raise EvidenceLifecycleTransitionError(f"evidence already registered in simulator: {record_id}")

        self._ensure_known_state(initial_state)
        self._enforce_fail_closed_rules(
            validated,
            tenant_id=tenant_id,
            to_state=initial_state,
            task_execution=None,
            guardian_decision=None,
            approval_binding=None,
            token_verification=None,
        )
        self._track_refs(validated, tenant_id=tenant_id)

        self._current[record_id] = {
            "tenant_id": tenant_id,
            "state": initial_state,
            "contract_name": contract_name,
            "payload": copy.deepcopy(validated),
        }
        self._history[record_id] = [
            EvidenceTransition(
                evidence_id=record_id,
                tenant_id=tenant_id,
                from_state=None,
                to_state=initial_state,
                updated_at=self._updated_at(validated),
                contract_name=contract_name,
            )
        ]
        return self.snapshot(record_id)

    def transition(
        self,
        evidence_id: str,
        to_state: str,
        payload: dict[str, Any],
        *,
        task_execution: dict[str, Any] | None = None,
        guardian_decision: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current = self._current.get(evidence_id)
        if current is None:
            raise EvidenceLifecycleTransitionError(f"unknown evidence id: {evidence_id}")

        normalized = self._normalize_payload(payload, evidence_id=evidence_id)
        record_id = normalized["record_id"]
        tenant_id = normalized["tenant_id"]
        validated = normalized["payload"]
        contract_name = normalized["contract_name"]
        if record_id != evidence_id:
            raise EvidenceLifecycleTransitionError("evidence payload id does not match transition target")
        if current["tenant_id"] != tenant_id:
            raise EvidenceLifecycleTransitionError("evidence tenant mismatch")

        from_state = current["state"]
        self._ensure_known_state(from_state)
        self._ensure_known_state(to_state)
        if from_state != to_state:
            allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
            if to_state not in allowed:
                raise EvidenceLifecycleTransitionError(f"invalid evidence transition: {from_state} -> {to_state}")

        self._enforce_fail_closed_rules(
            validated,
            tenant_id=tenant_id,
            to_state=to_state,
            task_execution=task_execution,
            guardian_decision=guardian_decision,
            approval_binding=approval_binding,
            token_verification=token_verification,
        )
        self._track_refs(validated, tenant_id=tenant_id)

        self._current[evidence_id] = {
            "tenant_id": tenant_id,
            "state": to_state,
            "contract_name": contract_name,
            "payload": copy.deepcopy(validated),
        }
        self._history.setdefault(evidence_id, []).append(
            EvidenceTransition(
                evidence_id=evidence_id,
                tenant_id=tenant_id,
                from_state=from_state,
                to_state=to_state,
                updated_at=self._updated_at(validated),
                contract_name=contract_name,
            )
        )
        return self.snapshot(evidence_id)

    def snapshot(self, evidence_id: str) -> dict[str, Any]:
        current = self._current.get(evidence_id)
        if current is None:
            raise EvidenceLifecycleTransitionError(f"unknown evidence id: {evidence_id}")
        result = copy.deepcopy(current["payload"])
        result["evidence_state"] = current["state"]
        result["evidence_id"] = evidence_id
        result["authorization_allowed"] = False
        result["execution_allowed"] = False
        result["export_allowed"] = False
        result["delete_allowed"] = False
        return result

    def history(self, evidence_id: str) -> list[dict[str, Any]]:
        transitions = self._history.get(evidence_id)
        if transitions is None:
            raise EvidenceLifecycleTransitionError(f"unknown evidence id: {evidence_id}")
        return [
            {
                "evidence_id": item.evidence_id,
                "tenant_id": item.tenant_id,
                "from_state": item.from_state,
                "to_state": item.to_state,
                "updated_at": item.updated_at,
                "contract_name": item.contract_name,
            }
            for item in transitions
        ]

    def execute_tools(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("evidence lifecycle simulator never executes tools")

    def authorize_real_action(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("evidence lifecycle simulator never authorizes real actions")

    def export_evidence(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("evidence lifecycle simulator never executes export runtime behavior")

    def delete_evidence(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("evidence lifecycle simulator never executes delete runtime behavior")

    def _normalize_payload(self, payload: dict[str, Any], *, evidence_id: str | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise EvidenceLifecycleValidationError("evidence payload must be a JSON object")
        candidate = copy.deepcopy(payload)
        contract_name = candidate.get("contract_name")
        if contract_name not in CONTRACT_TO_SCHEMA:
            raise EvidenceLifecycleValidationError("unsupported evidence contract for lifecycle simulator")

        id_field = CONTRACT_ID_FIELD[contract_name]
        record_id = candidate.get(id_field)
        if (not isinstance(record_id, str) or not record_id) and evidence_id:
            candidate[id_field] = evidence_id
            record_id = evidence_id
        if not isinstance(record_id, str) or not record_id:
            self._counter += 1
            generated_id = f"sim-evidence-{self._counter:04d}"
            candidate[id_field] = generated_id
            record_id = generated_id

        validated = self._validate_contract(candidate, CONTRACT_TO_SCHEMA[contract_name])
        tenant_id = validated.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id:
            raise EvidenceLifecycleValidationError("tenant_id is required")
        return {
            "payload": validated,
            "contract_name": contract_name,
            "record_id": record_id,
            "tenant_id": tenant_id,
        }

    def _enforce_fail_closed_rules(
        self,
        payload: dict[str, Any],
        *,
        tenant_id: str,
        to_state: str,
        task_execution: dict[str, Any] | None,
        guardian_decision: dict[str, Any] | None,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
    ) -> None:
        self._reject_raw_or_secret(payload)
        self._reject_runtime_export_delete_claims(payload)
        self._assert_evidence_refs_well_formed(payload)
        self._assert_ref_tenant_consistency(payload, tenant_id=tenant_id)
        self._assert_contract_specific_invariants(payload, tenant_id=tenant_id)

        if to_state in {"pre_action_recorded", "post_action_recorded"}:
            self._assert_guardian_task_approval_linkage(
                payload,
                tenant_id=tenant_id,
                task_execution=task_execution,
                guardian_decision=guardian_decision,
                approval_binding=approval_binding,
                token_verification=token_verification,
            )
        if to_state in {"denial_recorded", "replay_denial_recorded"}:
            self._assert_denial_linkage(payload)
        if to_state == "failed_closed_recorded":
            self._assert_failed_closed_linkage(payload)
        if to_state == "export_manifest_planned":
            if payload.get("contract_name") != "evidence.export_manifest":
                raise EvidenceLifecycleTransitionError(
                    "export_manifest_planned requires evidence.export_manifest metadata payload"
                )

    def _assert_guardian_task_approval_linkage(
        self,
        payload: dict[str, Any],
        *,
        tenant_id: str,
        task_execution: dict[str, Any] | None,
        guardian_decision: dict[str, Any] | None,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
    ) -> None:
        if task_execution is None:
            raise EvidenceLifecycleTransitionError("task metadata is required for pre/post action evidence states")
        if guardian_decision is None:
            raise EvidenceLifecycleTransitionError("guardian decision metadata is required for pre/post action evidence states")

        task = self._validate_contract(task_execution, "task.execution")
        if task.get("tenant_id") != tenant_id:
            raise EvidenceLifecycleTransitionError("task tenant mismatch")
        if task.get("status") in COMPLETION_TASK_STATES and not task.get("evidence_artifact_ids"):
            raise EvidenceLifecycleTransitionError("evidence-required completion metadata is missing evidence refs")

        decision = self._validate_contract(guardian_decision, "guardian.decision")
        if decision.get("tenant_id") != tenant_id:
            raise EvidenceLifecycleTransitionError("guardian decision tenant mismatch")
        try:
            assert_guardian_decision_replay_safe(
                decision,
                {
                    "tenant_id": task.get("tenant_id"),
                    "customer_context_id": task.get("customer_context_id"),
                    "task_id": task.get("task_id"),
                    "worker_id": task.get("assigned_worker_id"),
                    "guardian_decision_id": task.get("guardian_decision_id"),
                    "binding_id": task.get("binding_id"),
                    "approval_binding_id": task.get("binding_id"),
                    "approval_chain_id": task.get("approval_chain_id"),
                    "approval_request_id": task.get("approval_request_id"),
                    "approval_result_id": task.get("approval_result_id"),
                    "approval_token_id": task.get("approval_token_id"),
                    "token_verification_id": task.get("token_verification_id"),
                    "action_type": task.get("bound_action_type") or decision.get("bound_action_type") or "form_preparation_review",
                    "tool_scope": task.get("bound_tool_scope") or decision.get("bound_tool_scope"),
                    "decision_scope_hash": decision.get("decision_scope_hash"),
                    "evidence_required": True,
                    "evidence_refs": task.get("evidence_artifact_ids"),
                },
                reference_time=self.reference_time,
                consume_nonce=False,
            )
        except PolicyDenyError as exc:
            raise EvidenceLifecycleTransitionError(str(exc)) from exc

        if task.get("approval_required"):
            if approval_binding is None or token_verification is None:
                raise EvidenceLifecycleTransitionError(
                    "approval-required evidence metadata requires approval binding and token verification"
                )
            binding = self._validate_contract(approval_binding, "approval.binding")
            token = self._validate_contract(token_verification, "token.verification")
            if binding.get("tenant_id") != tenant_id or token.get("tenant_id") != tenant_id:
                raise EvidenceLifecycleTransitionError("approval/token tenant mismatch")
            try:
                assert_token_verification_authorizes_task(task, token, binding, reference_time=self.reference_time)
            except PolicyDenyError as exc:
                raise EvidenceLifecycleTransitionError(str(exc)) from exc

    @staticmethod
    def _assert_denial_linkage(payload: dict[str, Any]) -> None:
        reason_codes = payload.get("reason_codes") or payload.get("linkage_failure_reasons") or []
        if not reason_codes:
            raise EvidenceLifecycleTransitionError("denial/replay-denial evidence requires reason linkage")
        if not (payload.get("denial_evidence_ref") or payload.get("pre_action_evidence_refs")):
            raise EvidenceLifecycleTransitionError("denial/replay-denial evidence requires denial evidence linkage")

    @staticmethod
    def _assert_failed_closed_linkage(payload: dict[str, Any]) -> None:
        has_reason = bool(payload.get("failure_reason")) or bool(payload.get("reason_codes"))
        has_evidence = bool(payload.get("denial_evidence_ref")) or bool(payload.get("evidence_refs"))
        if not has_reason or not has_evidence:
            raise EvidenceLifecycleTransitionError("failed-closed evidence metadata requires reason and evidence linkage")

    def _assert_contract_specific_invariants(self, payload: dict[str, Any], *, tenant_id: str) -> None:
        contract_name = payload.get("contract_name")
        if contract_name == "evidence.artifact":
            checked = assert_evidence_artifact_chain_consistent(
                payload,
                expected_tenant_id=tenant_id,
                evidence_by_id=self._artifacts_by_id,
            )
            if checked.get("linkage_status") == "mismatched_tenant":
                raise EvidenceLifecycleTransitionError("cross-tenant evidence chain linkage is blocked")
        elif contract_name == "evidence.export_manifest":
            assert_evidence_export_manifest_consistent(payload)
            if payload.get("linkage_status") == "mismatched_tenant":
                raise EvidenceLifecycleTransitionError("cross-tenant evidence export linkage is blocked")
        elif contract_name == "evidence.ledger.entry":
            if payload.get("linkage_status") == "mismatched_tenant":
                raise EvidenceLifecycleTransitionError("cross-tenant ledger linkage is blocked")

    @staticmethod
    def _reject_raw_or_secret(payload: dict[str, Any]) -> None:
        if payload.get("raw_content_included") is True:
            raise EvidenceLifecycleTransitionError("raw_content_included true is blocked")
        if payload.get("secret_material_included") is True:
            raise EvidenceLifecycleTransitionError("secret_material_included true is blocked")

    @staticmethod
    def _reject_runtime_export_delete_claims(payload: dict[str, Any]) -> None:
        contract_name = payload.get("contract_name")
        if contract_name == "evidence.export_manifest":
            if payload.get("export_status") == "exported" or payload.get("export_review_status") == "exported":
                raise EvidenceLifecycleTransitionError("exported runtime behavior is blocked in evidence lifecycle simulator")
            if payload.get("delete_review_status") == "approved":
                raise EvidenceLifecycleTransitionError("delete approval runtime behavior is blocked in evidence lifecycle simulator")
            if payload.get("delete_proof_refs"):
                raise EvidenceLifecycleTransitionError("delete proof runtime behavior is blocked in evidence lifecycle simulator")
        if payload.get("export_package_refs"):
            raise EvidenceLifecycleTransitionError("export package runtime behavior is blocked in evidence lifecycle simulator")
        if payload.get("delete_proof_refs"):
            raise EvidenceLifecycleTransitionError("delete proof runtime behavior is blocked in evidence lifecycle simulator")

    @staticmethod
    def _assert_evidence_refs_well_formed(payload: dict[str, Any]) -> None:
        for field in EVIDENCE_REF_FIELDS:
            value = payload.get(field)
            if value is None:
                continue
            if isinstance(value, str):
                refs = [value]
            elif isinstance(value, list):
                refs = value
            else:
                raise EvidenceLifecycleTransitionError(f"{field} must be a string or list of strings")
            for item in refs:
                if not isinstance(item, str) or not item:
                    raise EvidenceLifecycleTransitionError(f"malformed evidence reference in {field}")
                if not item.startswith("ev-"):
                    raise EvidenceLifecycleTransitionError(f"malformed evidence reference in {field}: {item}")

    def _assert_ref_tenant_consistency(self, payload: dict[str, Any], *, tenant_id: str) -> None:
        for field in EVIDENCE_REF_FIELDS:
            value = payload.get(field)
            if value is None:
                continue
            refs = [value] if isinstance(value, str) else value
            if not isinstance(refs, list):
                continue
            for evidence_ref in refs:
                existing_tenant = self._tenant_by_evidence_ref.get(evidence_ref)
                if existing_tenant is not None and existing_tenant != tenant_id:
                    raise EvidenceLifecycleTransitionError("cross-tenant evidence chain linkage is blocked")

    def _track_refs(self, payload: dict[str, Any], *, tenant_id: str) -> None:
        contract_name = payload.get("contract_name")
        if contract_name == "evidence.artifact":
            artifact_id = payload.get("artifact_id")
            if isinstance(artifact_id, str) and artifact_id:
                self._tenant_by_evidence_ref[artifact_id] = tenant_id
                self._artifacts_by_id[artifact_id] = copy.deepcopy(payload)
        for field in EVIDENCE_REF_FIELDS:
            value = payload.get(field)
            if value is None:
                continue
            refs = [value] if isinstance(value, str) else value
            if not isinstance(refs, list):
                continue
            for evidence_ref in refs:
                if isinstance(evidence_ref, str) and evidence_ref.startswith("ev-"):
                    self._tenant_by_evidence_ref.setdefault(evidence_ref, tenant_id)

    def _validate_contract(self, payload: dict[str, Any], schema_ref: str) -> dict[str, Any]:
        try:
            return self.validator.validate(copy.deepcopy(payload), schema_ref)
        except Exception as exc:  # pragma: no cover - explicit fail-closed mapping
            raise EvidenceLifecycleValidationError(str(exc)) from exc

    @staticmethod
    def _ensure_known_state(state: str) -> None:
        if state not in EVIDENCE_STATES:
            raise EvidenceLifecycleTransitionError(f"unknown evidence lifecycle state: {state}")

    @staticmethod
    def _updated_at(payload: dict[str, Any]) -> str:
        for key in ("created_at", "detected_at", "prepared_at"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return "1970-01-01T00:00:00Z"
