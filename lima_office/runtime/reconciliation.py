"""Mock-only approval/Guardian reconciliation classifier for Phase 1A tests."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.runtime.errors import EvidenceRequiredError, PolicyDenyError
from lima_office.runtime.invariants import (
    BLOCKED_GUARDIAN_ACTION_TYPES,
    BLOCKED_MVP_APPROVAL_ACTIONS,
    DEFAULT_REFERENCE_TIME,
    assert_guardian_decision_replay_safe,
)
from lima_office.runtime.taxonomy import validate_reason_codes


RECONCILIATION_ORDER = (
    "cross_tenant_blocked",
    "blocked_mvp",
    "stale_decision",
    "mismatched_binding",
    "replay_mismatch",
    "coordinator_mismatch",
    "evidence_missing",
    "missing_ref",
    "reconciled",
)

RECONCILIATION_REASON_CODE_MAP = {
    "missing_guardian_decision": "recon_missing_guardian_decision",
    "stale_guardian_decision": "recon_stale_guardian_decision",
    "mismatched_approval_binding": "recon_mismatched_approval_binding",
    "mismatched_token_verification": "recon_mismatched_token_verification",
    "replay_record_missing": "recon_replay_record_missing",
    "replay_record_mismatch": "recon_replay_record_mismatch",
    "evidence_ref_missing": "recon_evidence_ref_missing",
    "evidence_ledger_mismatch": "recon_evidence_ref_missing",
    "coordinator_event_mismatch": "recon_coordinator_event_mismatch",
    "transaction_boundary_mismatch": "recon_coordinator_event_mismatch",
    "cross_tenant_linkage": "recon_cross_tenant_linkage",
    "blocked_mvp_authorization_attempt": "blocked_mvp_authorization_attempt",
}


class ApprovalGuardianReconciler:
    """Classifies reconciliation posture across approval/Guardian metadata."""

    def __init__(self, *, reference_time: str | None = DEFAULT_REFERENCE_TIME) -> None:
        self.reference_time = reference_time

    def reconcile(
        self,
        *,
        approval_chain: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
        guardian_decision: dict[str, Any] | None = None,
        guardian_replay: dict[str, Any] | None = None,
        replay_record: dict[str, Any] | None = None,
        coordinator_event: dict[str, Any] | None = None,
        transaction_boundary: dict[str, Any] | None = None,
        ledger_entries: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        reasons: list[str] = []
        evidence_refs = self._collect_all_evidence_refs(
            approval_chain,
            approval_binding,
            token_verification,
            guardian_decision,
            guardian_replay,
            replay_record,
            coordinator_event,
            transaction_boundary,
            *(ledger_entries or []),
        )

        payloads = [payload for payload in (
            approval_chain,
            approval_binding,
            token_verification,
            guardian_decision,
            guardian_replay,
            replay_record,
            coordinator_event,
            transaction_boundary,
            *(ledger_entries or []),
        ) if isinstance(payload, dict)]

        canonical_tenant_id = self._first_value(payloads, "tenant_id")
        canonical_customer_context_id = self._first_value(payloads, "customer_context_id")
        canonical_task_id = self._first_value(
            payloads,
            "task_id",
            alt_fields=("bound_task_id", "canonical_task_id"),
        )
        canonical_worker_id = self._first_value(
            payloads,
            "worker_id",
            alt_fields=("bound_worker_id", "canonical_worker_id"),
        )
        canonical_action_type = self._first_value(
            payloads,
            "action_type",
            alt_fields=("bound_action_type", "canonical_action_type"),
        )
        canonical_tool_scope = self._first_value(
            payloads,
            "tool_scope",
            alt_fields=("bound_tool_scope", "canonical_tool_scope"),
        )
        canonical_approval_chain_id = self._first_value(payloads, "approval_chain_id")
        canonical_approval_binding_id = self._first_value(
            payloads,
            "approval_binding_id",
            alt_fields=("binding_id",),
        )
        canonical_token_verification_id = self._first_value(payloads, "token_verification_id")
        canonical_guardian_decision_id = self._first_value(
            payloads,
            "guardian_decision_id",
            alt_fields=("decision_id",),
        )
        canonical_guardian_replay_id = self._first_value(payloads, "replay_check_id")
        canonical_replay_record_id = self._first_value(payloads, "replay_record_id")
        canonical_transaction_id = self._first_value(payloads, "transaction_id", alt_fields=("related_transaction_id",))

        for payload in payloads:
            if canonical_tenant_id is not None and payload.get("tenant_id") != canonical_tenant_id:
                reasons.append("cross_tenant_linkage")
            if (
                canonical_customer_context_id is not None
                and payload.get("customer_context_id") not in {None, canonical_customer_context_id}
            ):
                reasons.append("cross_tenant_linkage")

        if guardian_decision is None:
            reasons.append("missing_guardian_decision")

        if guardian_decision is not None:
            if guardian_decision.get("replay_status") in {"expired", "stale"}:
                reasons.append("stale_guardian_decision")
            requested_action = {
                "tenant_id": canonical_tenant_id,
                "customer_context_id": canonical_customer_context_id,
                "task_id": canonical_task_id,
                "worker_id": canonical_worker_id,
                "guardian_decision_id": canonical_guardian_decision_id,
                "action_type": canonical_action_type,
                "tool_scope": copy.deepcopy(canonical_tool_scope),
                "approval_binding_id": canonical_approval_binding_id,
                "token_verification_id": canonical_token_verification_id,
                "evidence_required": True,
                "evidence_refs": sorted(evidence_refs) if evidence_refs else ["ev-reconciliation-placeholder"],
            }
            if approval_binding is not None:
                requested_action["approval_binding"] = approval_binding
            try:
                assert_guardian_decision_replay_safe(
                    guardian_decision,
                    requested_action,
                    reference_time=self.reference_time,
                    consumed_nonces=set(),
                    consume_nonce=False,
                )
            except (PolicyDenyError, EvidenceRequiredError) as exc:
                message = str(exc).lower()
                if (
                    "stale" in message
                    or "expired" in message
                    or "effective" in message
                    or "issued" in message
                    or "expiry" in message
                    or "timestamp" in message
                ):
                    reasons.append("stale_guardian_decision")
                if "blocked" in message and "mvp" in message:
                    reasons.append("blocked_mvp_authorization_attempt")

        if approval_binding is not None:
            if canonical_approval_chain_id is not None and approval_binding.get("approval_chain_id") != canonical_approval_chain_id:
                reasons.append("mismatched_approval_binding")
            if canonical_approval_binding_id is not None and approval_binding.get("binding_id") != canonical_approval_binding_id:
                reasons.append("mismatched_approval_binding")
            if canonical_task_id is not None and approval_binding.get("task_id") != canonical_task_id:
                reasons.append("mismatched_approval_binding")
            if canonical_worker_id is not None and approval_binding.get("worker_id") not in {None, canonical_worker_id}:
                reasons.append("mismatched_approval_binding")
            if canonical_action_type is not None and approval_binding.get("action_type") != canonical_action_type:
                reasons.append("mismatched_approval_binding")
            if canonical_tool_scope is not None and approval_binding.get("tool_scope") != canonical_tool_scope:
                reasons.append("mismatched_approval_binding")

        if token_verification is not None:
            if canonical_token_verification_id is not None and token_verification.get("token_verification_id") != canonical_token_verification_id:
                reasons.append("mismatched_token_verification")
            if canonical_guardian_decision_id is not None and token_verification.get("guardian_decision_id") != canonical_guardian_decision_id:
                reasons.append("mismatched_token_verification")
            if canonical_task_id is not None and token_verification.get("task_id") != canonical_task_id:
                reasons.append("mismatched_token_verification")

        if guardian_replay is None or replay_record is None:
            reasons.append("replay_record_missing")
        else:
            if canonical_replay_record_id is not None and guardian_replay.get("replay_record_id") != canonical_replay_record_id:
                reasons.append("replay_record_mismatch")
            if guardian_replay.get("replay_record_id") != replay_record.get("replay_record_id"):
                reasons.append("replay_record_mismatch")
            if guardian_replay.get("decision_nonce") != replay_record.get("decision_nonce"):
                reasons.append("replay_record_mismatch")
            if canonical_token_verification_id is not None and guardian_replay.get("token_verification_id") != canonical_token_verification_id:
                reasons.append("mismatched_token_verification")
            if canonical_approval_binding_id is not None and guardian_replay.get("approval_binding_id") not in {
                None,
                canonical_approval_binding_id,
            }:
                reasons.append("mismatched_approval_binding")
            if canonical_action_type is not None and guardian_replay.get("action_type") != canonical_action_type:
                reasons.append("replay_record_mismatch")
            if canonical_tool_scope is not None and guardian_replay.get("tool_scope") != canonical_tool_scope:
                reasons.append("replay_record_mismatch")

        if replay_record is not None and canonical_transaction_id is not None:
            if replay_record.get("related_transaction_id") not in {None, canonical_transaction_id}:
                reasons.append("coordinator_event_mismatch")

        if coordinator_event is not None and transaction_boundary is not None:
            tx_id = transaction_boundary.get("transaction_id")
            if canonical_transaction_id is not None and tx_id != canonical_transaction_id:
                reasons.append("transaction_boundary_mismatch")
            if coordinator_event.get("transaction_id") != tx_id:
                reasons.append("coordinator_event_mismatch")
            if coordinator_event.get("related_transaction_id") != tx_id:
                reasons.append("coordinator_event_mismatch")

        for entry in ledger_entries or []:
            if canonical_transaction_id is not None and entry.get("related_transaction_id") not in {None, canonical_transaction_id}:
                reasons.append("evidence_ledger_mismatch")
            if canonical_replay_record_id is not None and canonical_replay_record_id not in entry.get("related_replay_record_ids", []):
                reasons.append("evidence_ledger_mismatch")
            if canonical_tenant_id is not None and entry.get("tenant_id") != canonical_tenant_id:
                reasons.append("cross_tenant_linkage")

        denied_or_replay_denied = False
        if guardian_decision is not None and guardian_decision.get("replay_status") in {
            "replay_denied",
            "expired",
            "stale",
            "blocked_mvp",
        }:
            denied_or_replay_denied = True
            if not guardian_decision.get("denial_evidence_ref"):
                reasons.append("evidence_ref_missing")
        if guardian_decision is not None and guardian_decision.get("decision") in {
            "deny",
            "block_mvp",
            "quarantine_subject",
        }:
            denied_or_replay_denied = True
            if not guardian_decision.get("denial_evidence_ref"):
                reasons.append("evidence_ref_missing")
        if guardian_replay is not None and guardian_replay.get("replay_check_result") in {
            "replay_denied",
            "expired",
            "stale",
            "blocked_mvp",
        }:
            denied_or_replay_denied = True
            if guardian_replay.get("replay_check_result") in {"expired", "stale"}:
                reasons.append("stale_guardian_decision")
            if not guardian_replay.get("denial_evidence_ref"):
                reasons.append("evidence_ref_missing")
        if denied_or_replay_denied and not evidence_refs:
            reasons.append("evidence_ref_missing")

        action_candidates = [
            canonical_action_type,
            approval_binding.get("action_type") if approval_binding else None,
            guardian_replay.get("action_type") if guardian_replay else None,
            guardian_decision.get("bound_action_type") if guardian_decision else None,
        ]
        for action in action_candidates:
            if action in BLOCKED_MVP_APPROVAL_ACTIONS or action in BLOCKED_GUARDIAN_ACTION_TYPES:
                reasons.append("blocked_mvp_authorization_attempt")

        status = self._classify_status(reasons)
        deduped_reasons = sorted(set(reasons))
        mapped_reason_codes = [
            RECONCILIATION_REASON_CODE_MAP[reason]
            for reason in deduped_reasons
            if reason in RECONCILIATION_REASON_CODE_MAP
        ]
        reason_codes = validate_reason_codes(mapped_reason_codes)
        return {
            "reconciliation_status": status,
            "reconciliation_failure_reasons": deduped_reasons,
            "reason_codes": reason_codes,
            "reconciliation_evidence_refs": sorted(evidence_refs),
            "canonical_approval_chain_id": canonical_approval_chain_id,
            "canonical_approval_binding_id": canonical_approval_binding_id,
            "canonical_guardian_decision_id": canonical_guardian_decision_id,
            "canonical_token_verification_id": canonical_token_verification_id,
            "canonical_replay_record_id": canonical_replay_record_id,
            "canonical_transaction_id": canonical_transaction_id,
            "canonical_guardian_replay_id": canonical_guardian_replay_id,
            "can_authorize": False,
        }

    @staticmethod
    def _first_value(
        payloads: list[dict[str, Any]],
        field: str,
        *,
        alt_fields: tuple[str, ...] = (),
    ) -> Any:
        for payload in payloads:
            if field in payload and payload.get(field) is not None:
                return payload.get(field)
            for alt_field in alt_fields:
                if alt_field in payload and payload.get(alt_field) is not None:
                    return payload.get(alt_field)
        return None

    @staticmethod
    def _collect_all_evidence_refs(*payloads: Any) -> set[str]:
        refs: set[str] = set()
        for payload in payloads:
            if not isinstance(payload, dict):
                continue
            for field_name in (
                "evidence_refs",
                "evidence_artifact_ids",
                "reconciliation_evidence_refs",
                "pre_action_evidence_refs",
                "post_action_evidence_refs",
            ):
                field_value = payload.get(field_name)
                if isinstance(field_value, list):
                    for value in field_value:
                        if isinstance(value, str) and value:
                            refs.add(value)
            for field_name in ("evidence_artifact_id", "denial_evidence_ref"):
                field_value = payload.get(field_name)
                if isinstance(field_value, str) and field_value:
                    refs.add(field_value)
        return refs

    @staticmethod
    def _classify_status(reasons: list[str]) -> str:
        reason_set = set(reasons)
        if "cross_tenant_linkage" in reason_set:
            return "cross_tenant_blocked"
        if "blocked_mvp_authorization_attempt" in reason_set:
            return "blocked_mvp"
        if "stale_guardian_decision" in reason_set:
            return "stale_decision"
        if {"mismatched_approval_binding", "mismatched_token_verification"} & reason_set:
            return "mismatched_binding"
        if {"replay_record_missing", "replay_record_mismatch"} & reason_set:
            return "replay_mismatch"
        if {"coordinator_event_mismatch", "transaction_boundary_mismatch"} & reason_set:
            return "coordinator_mismatch"
        if {"evidence_ref_missing", "evidence_ledger_mismatch"} & reason_set:
            return "evidence_missing"
        if "missing_guardian_decision" in reason_set:
            return "missing_ref"
        return "reconciled"
