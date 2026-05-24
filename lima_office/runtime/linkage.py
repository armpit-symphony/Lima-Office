"""Mock-only cross-contract linkage validator for Phase 1A hardening tests."""

from __future__ import annotations

import copy
from typing import Any


class CrossContractLinkageValidator:
    """Validates cross-contract metadata linkage in memory only."""

    def __init__(self) -> None:
        self._idempotency_index: dict[tuple[str, str, str, str], str] = {}

    @property
    def idempotency_index(self) -> dict[tuple[str, str, str, str], str]:
        return copy.deepcopy(self._idempotency_index)

    def validate_chain(
        self,
        *,
        coordinator_event: dict[str, Any],
        transaction_boundary: dict[str, Any],
        replay_record: dict[str, Any],
        ledger_entries: list[dict[str, Any]],
        evidence_artifacts: dict[str, dict[str, Any]],
        export_manifest: dict[str, Any] | None = None,
        guardian_decision: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
        expected_nonce: str | None = None,
    ) -> dict[str, Any]:
        linkage_failure_reasons: list[str] = []
        forced_status: str | None = None
        coordinator_event_id = coordinator_event.get("coordinator_event_id")

        self._check_tenant_idempotency(
            coordinator_event.get("tenant_id"),
            coordinator_event.get("customer_context_id"),
            coordinator_event.get("idempotency_scope"),
            coordinator_event.get("idempotency_key"),
            coordinator_event.get("transaction_id"),
            linkage_failure_reasons,
        )

        tx_id = transaction_boundary.get("transaction_id")
        if coordinator_event.get("transaction_id") != tx_id:
            linkage_failure_reasons.append("coordinator_transaction_mismatch")
        if coordinator_event_id not in transaction_boundary.get("related_coordinator_event_ids", []):
            linkage_failure_reasons.append("boundary_related_coordinator_event_missing")
        if replay_record.get("related_transaction_id") not in {None, tx_id}:
            linkage_failure_reasons.append("replay_related_transaction_mismatch")

        tenant_id = coordinator_event.get("tenant_id")
        customer_context_id = coordinator_event.get("customer_context_id")
        correlation_id = coordinator_event.get("correlation_id")
        idempotency_key = coordinator_event.get("idempotency_key")
        replay_record_id = replay_record.get("replay_record_id")

        for name, payload in (
            ("coordinator_event", coordinator_event),
            ("transaction_boundary", transaction_boundary),
            ("replay_record", replay_record),
        ):
            self._check_envelope_and_canonical_fields(
                name=name,
                payload=payload,
                tenant_id=tenant_id,
                customer_context_id=customer_context_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                linkage_failure_reasons=linkage_failure_reasons,
            )

        if replay_record_id not in transaction_boundary.get("related_replay_record_ids", []):
            linkage_failure_reasons.append("boundary_related_replay_record_missing")
        if replay_record_id not in coordinator_event.get("related_replay_record_ids", []):
            linkage_failure_reasons.append("coordinator_related_replay_record_missing")
        if coordinator_event_id not in replay_record.get("related_coordinator_event_ids", []):
            linkage_failure_reasons.append("replay_related_coordinator_event_missing")

        if expected_nonce is not None and replay_record.get("decision_nonce") != expected_nonce:
            linkage_failure_reasons.append("replay_nonce_mismatch")
        if replay_record.get("canonical_decision_nonce") not in {None, replay_record.get("decision_nonce")}:
            linkage_failure_reasons.append("replay_canonical_nonce_mismatch")

        if replay_record.get("canonical_action_type") not in {None, replay_record.get("action_type")}:
            linkage_failure_reasons.append("replay_action_type_mismatch")
        canonical_tool_scope = replay_record.get("canonical_tool_scope")
        if canonical_tool_scope is not None and canonical_tool_scope != replay_record.get("tool_scope"):
            linkage_failure_reasons.append("replay_tool_scope_mismatch")

        ledger_by_id = {entry.get("ledger_entry_id"): entry for entry in ledger_entries}
        linked_ledger_ids = set()
        for entry in ledger_entries:
            self._check_envelope_and_canonical_fields(
                name="ledger",
                payload=entry,
                tenant_id=tenant_id,
                customer_context_id=customer_context_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                linkage_failure_reasons=linkage_failure_reasons,
            )
            if entry.get("related_transaction_id") not in {None, tx_id}:
                linkage_failure_reasons.append("ledger_transaction_mismatch")
            if replay_record_id not in entry.get("related_replay_record_ids", []):
                linkage_failure_reasons.append("ledger_related_replay_record_missing")
            if coordinator_event_id not in entry.get("related_coordinator_event_ids", []):
                linkage_failure_reasons.append("ledger_related_coordinator_event_missing")
            if entry.get("ledger_entry_id"):
                linked_ledger_ids.add(entry["ledger_entry_id"])
            for parent_id in entry.get("parent_entry_ids", []):
                if parent_id not in ledger_by_id:
                    linkage_failure_reasons.append("ledger_parent_missing")

        for artifact_id, artifact in evidence_artifacts.items():
            self._check_envelope_and_canonical_fields(
                name="artifact",
                payload=artifact,
                tenant_id=tenant_id,
                customer_context_id=customer_context_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                linkage_failure_reasons=linkage_failure_reasons,
                allow_canonical_absent=True,
            )
            if artifact.get("raw_content_included") is not False:
                linkage_failure_reasons.append("artifact_raw_content_included")
            if artifact.get("secret_material_included") is not False:
                linkage_failure_reasons.append("artifact_secret_material_included")
            if artifact_id != artifact.get("artifact_id"):
                linkage_failure_reasons.append("artifact_id_map_mismatch")
            if linked_ledger_ids and not set(artifact.get("related_ledger_entry_ids", [])).intersection(linked_ledger_ids):
                linkage_failure_reasons.append("artifact_related_ledger_entry_missing")

        for entry in ledger_entries:
            for artifact_ref in entry.get("related_evidence_artifact_ids", []):
                if artifact_ref not in evidence_artifacts:
                    linkage_failure_reasons.append("ledger_artifact_ref_missing")

        if export_manifest is not None:
            self._check_envelope_and_canonical_fields(
                name="manifest",
                payload=export_manifest,
                tenant_id=tenant_id,
                customer_context_id=customer_context_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                linkage_failure_reasons=linkage_failure_reasons,
            )
            included = set(export_manifest.get("included_evidence_refs", []))
            excluded = set(export_manifest.get("excluded_evidence_refs", []))
            evidence_refs = set(export_manifest.get("evidence_refs", []))
            if included & excluded:
                linkage_failure_reasons.append("manifest_include_exclude_overlap")
            if not included.issubset(evidence_refs):
                linkage_failure_reasons.append("manifest_included_non_evidence_ref")
            for evidence_ref in included | excluded | evidence_refs:
                artifact = evidence_artifacts.get(evidence_ref)
                if artifact is None:
                    linkage_failure_reasons.append("manifest_included_unknown_evidence_ref")
                    continue
                if artifact.get("tenant_id") != tenant_id:
                    linkage_failure_reasons.append("manifest_cross_tenant_evidence_ref")
                if artifact.get("customer_context_id") not in {None, customer_context_id}:
                    linkage_failure_reasons.append("manifest_cross_context_evidence_ref")
            if export_manifest.get("export_status") in {"denied", "blocked_mvp"}:
                if not export_manifest.get("delete_conflict_refs"):
                    linkage_failure_reasons.append("manifest_missing_delete_conflict_ref")
                else:
                    linkage_failure_reasons.append("manifest_delete_export_conflict")
                forced_status = "blocked_mvp"

        if coordinator_event.get("event_type") == "transaction_failed_closed" and (
            transaction_boundary.get("transaction_status") == "committed"
        ):
            linkage_failure_reasons.append("reconciliation_drift_terminal_state")
        if coordinator_event.get("event_type") == "transaction_committed" and (
            transaction_boundary.get("transaction_status") == "failed_closed"
        ):
            linkage_failure_reasons.append("reconciliation_drift_terminal_state")
        if coordinator_event.get("event_type") == "transaction_rolled_back" and (
            transaction_boundary.get("transaction_status") == "committed"
        ):
            linkage_failure_reasons.append("reconciliation_drift_terminal_state")

        if guardian_decision is not None:
            self._check_envelope_and_canonical_fields(
                name="guardian_decision",
                payload=guardian_decision,
                tenant_id=tenant_id,
                customer_context_id=customer_context_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                linkage_failure_reasons=linkage_failure_reasons,
                allow_canonical_absent=True,
            )
            if replay_record.get("decision_nonce") and guardian_decision.get("decision_nonce") not in {
                None,
                replay_record.get("decision_nonce"),
            }:
                linkage_failure_reasons.append("guardian_nonce_mismatch")
            if guardian_decision.get("bound_action_type") not in {None, replay_record.get("action_type")}:
                linkage_failure_reasons.append("guardian_action_type_mismatch")
            guardian_bound_tool_scope = guardian_decision.get("bound_tool_scope")
            if guardian_bound_tool_scope is not None and guardian_bound_tool_scope != replay_record.get("tool_scope"):
                linkage_failure_reasons.append("guardian_tool_scope_mismatch")
            if replay_record.get("approval_binding_id") and guardian_decision.get("approval_binding_id") not in {
                None,
                replay_record.get("approval_binding_id"),
            }:
                linkage_failure_reasons.append("guardian_approval_binding_mismatch")

        if approval_binding is not None:
            self._check_envelope_and_canonical_fields(
                name="approval_binding",
                payload=approval_binding,
                tenant_id=tenant_id,
                customer_context_id=customer_context_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                linkage_failure_reasons=linkage_failure_reasons,
                allow_canonical_absent=True,
            )
            if replay_record.get("approval_binding_id") and approval_binding.get("binding_id") not in {
                None,
                replay_record.get("approval_binding_id"),
            }:
                linkage_failure_reasons.append("binding_id_mismatch")
            if replay_record.get("action_type") and approval_binding.get("bound_action_type") not in {
                None,
                replay_record.get("action_type"),
            }:
                linkage_failure_reasons.append("binding_action_type_mismatch")
            binding_tool_scope = approval_binding.get("bound_tool_scope")
            if replay_record.get("tool_scope") and binding_tool_scope is not None and binding_tool_scope != replay_record.get("tool_scope"):
                linkage_failure_reasons.append("binding_tool_scope_mismatch")

        deduped_reasons = sorted(set(linkage_failure_reasons))
        status = self._classify_linkage_status(deduped_reasons, forced_status=forced_status)
        return {
            "linkage_status": status,
            "failure_reasons": deduped_reasons,
            "linkage_failure_reasons": deduped_reasons,
            "can_authorize": False,
        }

    def _check_tenant_idempotency(
        self,
        tenant_id: Any,
        customer_context_id: Any,
        idempotency_scope: Any,
        idempotency_key: Any,
        transaction_id: Any,
        linkage_failure_reasons: list[str],
    ) -> None:
        if (
            not isinstance(tenant_id, str)
            or not isinstance(customer_context_id, str)
            or not isinstance(idempotency_scope, str)
            or not isinstance(idempotency_key, str)
            or not isinstance(transaction_id, str)
        ):
            linkage_failure_reasons.append("invalid_idempotency_context")
            return
        key = (tenant_id, customer_context_id, idempotency_scope, idempotency_key)
        existing_transaction = self._idempotency_index.get(key)
        if existing_transaction is None:
            self._idempotency_index[key] = transaction_id
            return
        if existing_transaction != transaction_id:
            linkage_failure_reasons.append("duplicate_idempotency_key_same_tenant")

    @staticmethod
    def _check_envelope_and_canonical_fields(
        *,
        name: str,
        payload: dict[str, Any],
        tenant_id: Any,
        customer_context_id: Any,
        correlation_id: Any,
        idempotency_key: Any,
        linkage_failure_reasons: list[str],
        allow_canonical_absent: bool = False,
    ) -> None:
        if payload.get("tenant_id") != tenant_id:
            linkage_failure_reasons.append(f"{name}_tenant_mismatch")
        if payload.get("customer_context_id") != customer_context_id:
            linkage_failure_reasons.append(f"{name}_customer_context_mismatch")
        if payload.get("correlation_id") != correlation_id:
            linkage_failure_reasons.append(f"{name}_correlation_mismatch")
        if payload.get("idempotency_key") != idempotency_key:
            linkage_failure_reasons.append(f"{name}_idempotency_mismatch")

        canonical_tenant = payload.get("canonical_tenant_id")
        canonical_correlation = payload.get("canonical_correlation_id")
        canonical_idempotency = payload.get("canonical_idempotency_key")
        if not allow_canonical_absent or canonical_tenant is not None:
            if canonical_tenant != payload.get("tenant_id"):
                linkage_failure_reasons.append(f"{name}_canonical_tenant_mismatch")
        if not allow_canonical_absent or canonical_correlation is not None:
            if canonical_correlation != payload.get("correlation_id"):
                linkage_failure_reasons.append(f"{name}_canonical_correlation_mismatch")
        if not allow_canonical_absent or canonical_idempotency is not None:
            if canonical_idempotency != payload.get("idempotency_key"):
                linkage_failure_reasons.append(f"{name}_canonical_idempotency_mismatch")

    @staticmethod
    def _classify_linkage_status(linkage_failure_reasons: list[str], *, forced_status: str | None = None) -> str:
        if forced_status == "blocked_mvp":
            return "blocked_mvp"
        if not linkage_failure_reasons:
            return "linked"

        if any("tenant_mismatch" in reason for reason in linkage_failure_reasons):
            return "mismatched_tenant"
        if any("nonce" in reason for reason in linkage_failure_reasons):
            return "mismatched_nonce"
        if any(("scope_mismatch" in reason) or ("action_type_mismatch" in reason) for reason in linkage_failure_reasons):
            return "mismatched_scope"
        if any(("missing" in reason) or ("unknown" in reason) for reason in linkage_failure_reasons):
            return "missing_ref"
        return "drift_detected"
