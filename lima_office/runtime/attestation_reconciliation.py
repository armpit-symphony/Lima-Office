"""Mock-only attestation revocation reconciliation classifier."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


DRIFT_REASON_MAP = {
    "reference_value_revoked_but_lineage_current": "trusted_result_with_revoked_reference",
    "endorsement_revoked_but_result_trusted": "trusted_result_with_revoked_endorsement",
    "appraisal_policy_revoked_but_route_selected": "appraisal_policy_revoked_but_active",
    "attestation_result_expired_but_worker_active": "attestation_result_expired",
    "revocation_pending_but_privileged_route_selected": "attestation_revocation_not_propagated",
    "quarantine_required_but_worker_active": "attestation_quarantine_mismatch",
    "model_route_selected_with_untrusted_lineage": "model_route_selected_with_untrusted_lineage",
    "transaction_committed_with_revoked_attestation": "transaction_committed_with_revoked_attestation",
    "evidence_missing_for_revocation": "evidence_ref_missing",
    "cross_tenant_attestation_linkage": "attestation_cross_tenant_linkage",
    "verifier_authority_revoked_but_appraisal_active": "verifier_authority_conflict",
}


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _collect_evidence_refs(*payloads: Any) -> set[str]:
    refs: set[str] = set()
    for payload in payloads:
        if isinstance(payload, dict):
            for key in ("evidence_refs", "attestation_evidence_refs"):
                values = payload.get(key)
                if isinstance(values, list):
                    for value in values:
                        if isinstance(value, str) and value:
                            refs.add(value)
            for key in ("denial_evidence_ref", "evidence_artifact_id"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    refs.add(value)
        elif isinstance(payload, list):
            refs.update(_collect_evidence_refs(*payload))
    return refs


def _collect_revocation_evidence_refs(
    lineage: dict[str, Any],
    attestation_result: dict[str, Any],
    model_routes: list[dict[str, Any]],
    transaction_boundaries: list[dict[str, Any]],
    coordinator_events: list[dict[str, Any]],
) -> set[str]:
    """Collect evidence refs that directly justify revocation/drift outcomes."""

    refs: set[str] = set()
    for payload in (
        lineage,
        attestation_result,
        *model_routes,
        *transaction_boundaries,
        *coordinator_events,
    ):
        if not isinstance(payload, dict):
            continue
        values = payload.get("evidence_refs")
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str) and value:
                    refs.add(value)
        denial_ref = payload.get("denial_evidence_ref")
        if isinstance(denial_ref, str) and denial_ref:
            refs.add(denial_ref)
    return refs


def _route_is_privileged_selected(route: dict[str, Any]) -> bool:
    return (
        route.get("route_status") == "selected"
        and route.get("risk_tier") == "high"
    )


def _worker_looks_active(worker_lifecycle: dict[str, Any] | None) -> bool:
    if not isinstance(worker_lifecycle, dict):
        return False
    state = str(
        worker_lifecycle.get("worker_state")
        or worker_lifecycle.get("state")
        or worker_lifecycle.get("lifecycle_state")
        or ""
    )
    return state in {"active", "healthy", "assigned", "ready"}


def reconcile_attestation_metadata(
    *,
    lineage: dict[str, Any],
    authorities: list[dict[str, Any]],
    reference_values: list[dict[str, Any]],
    endorsements: list[dict[str, Any]],
    appraisal_policy: dict[str, Any],
    attestation_result: dict[str, Any],
    worker_attestation: dict[str, Any] | None = None,
    worker_lifecycle: dict[str, Any] | None = None,
    worker_heartbeat: dict[str, Any] | None = None,
    device_trust: dict[str, Any] | None = None,
    model_routes: list[dict[str, Any]] | None = None,
    update_rollback: dict[str, Any] | None = None,
    transaction_boundaries: list[dict[str, Any]] | None = None,
    coordinator_events: list[dict[str, Any]] | None = None,
    ledger_entries: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Reconcile attestation metadata relationships with fail-closed posture."""

    if not isinstance(lineage, dict):
        raise PolicyDenyError("lineage payload must be an object")
    validate_taxonomy_version(str(lineage.get("taxonomy_version") or ""))
    validate_taxonomy_version(str(attestation_result.get("taxonomy_version") or ""))
    validate_taxonomy_version(str(appraisal_policy.get("taxonomy_version") or ""))
    for payload in authorities + reference_values + endorsements:
        if isinstance(payload, dict):
            validate_taxonomy_version(str(payload.get("taxonomy_version") or ""))

    current = now or datetime.now(UTC)
    model_routes = list(model_routes or [])
    transaction_boundaries = list(transaction_boundaries or [])
    coordinator_events = list(coordinator_events or [])
    ledger_entries = list(ledger_entries or [])

    drift_classes: list[str] = []

    tenant_id = str(lineage.get("tenant_id") or "")
    all_payloads: list[dict[str, Any]] = [lineage, attestation_result, appraisal_policy]
    all_payloads.extend([a for a in authorities if isinstance(a, dict)])
    all_payloads.extend([r for r in reference_values if isinstance(r, dict)])
    all_payloads.extend([e for e in endorsements if isinstance(e, dict)])
    all_payloads.extend([r for r in model_routes if isinstance(r, dict)])
    all_payloads.extend([t for t in transaction_boundaries if isinstance(t, dict)])
    all_payloads.extend([c for c in coordinator_events if isinstance(c, dict)])
    all_payloads.extend([l for l in ledger_entries if isinstance(l, dict)])
    for optional_payload in (worker_attestation, worker_lifecycle, worker_heartbeat, device_trust, update_rollback):
        if isinstance(optional_payload, dict):
            all_payloads.append(optional_payload)

    if any(str(payload.get("tenant_id") or "") != tenant_id for payload in all_payloads):
        drift_classes.append("cross_tenant_attestation_linkage")

    lineage_status = str(lineage.get("lineage_status") or "")
    lineage_trust_effect = str(lineage.get("trust_effect") or "")
    revocation_status = str(lineage.get("revocation_propagation_status") or "")
    result_trust_effect = str(attestation_result.get("trust_effect") or "")

    if lineage_status == "current":
        if any(str(ref.get("reference_status") or "") == "revoked" for ref in reference_values):
            drift_classes.append("reference_value_revoked_but_lineage_current")

    if result_trust_effect == "trusted_metadata_only" and any(
        str(endorsement.get("endorsement_status") or "") == "revoked" for endorsement in endorsements
    ):
        drift_classes.append("endorsement_revoked_but_result_trusted")

    appraisal_status = str(appraisal_policy.get("policy_status") or "")
    if appraisal_status in {"revoked", "blocked_mvp"} and any(
        isinstance(route, dict) and route.get("route_status") == "selected"
        for route in model_routes
    ):
        drift_classes.append("appraisal_policy_revoked_but_route_selected")

    result_expired = False
    result_expires_at = _parse_ts(attestation_result.get("expires_at"))
    if str(attestation_result.get("appraisal_result") or "") == "expired":
        result_expired = True
    elif result_expires_at is not None and result_expires_at < current:
        result_expired = True
    if result_expired and _worker_looks_active(worker_lifecycle):
        drift_classes.append("attestation_result_expired_but_worker_active")

    if revocation_status == "pending" and any(_route_is_privileged_selected(route) for route in model_routes):
        drift_classes.append("revocation_pending_but_privileged_route_selected")

    quarantine_required = lineage_status == "quarantine_required" or result_trust_effect == "quarantine_required"
    if quarantine_required and _worker_looks_active(worker_lifecycle):
        drift_classes.append("quarantine_required_but_worker_active")

    untrusted_lineage = (
        lineage_status != "current"
        or lineage_trust_effect != "trusted_metadata_only"
        or revocation_status in {"pending", "failed_closed", "blocked_mvp"}
    )
    if untrusted_lineage and any(isinstance(route, dict) and route.get("route_status") == "selected" for route in model_routes):
        drift_classes.append("model_route_selected_with_untrusted_lineage")

    revoked_attestation = lineage_status in {"revoked", "conflicted", "stale"} or result_trust_effect in {
        "revoked",
        "quarantine_required",
        "blocked_mvp",
    }
    if revoked_attestation and any(
        isinstance(txn, dict) and txn.get("transaction_status") == "committed"
        for txn in transaction_boundaries
    ):
        drift_classes.append("transaction_committed_with_revoked_attestation")

    has_revocation_signal = (
        revoked_attestation
        or revocation_status in {"pending", "failed_closed"}
        or any(str(ref.get("reference_status") or "") == "revoked" for ref in reference_values)
        or any(str(endorsement.get("endorsement_status") or "") == "revoked" for endorsement in endorsements)
    )
    revocation_evidence_refs = sorted(
        _collect_revocation_evidence_refs(
            lineage,
            attestation_result,
            model_routes,
            transaction_boundaries,
            coordinator_events,
        )
    )
    evidence_refs = sorted(
        _collect_evidence_refs(
            lineage,
            attestation_result,
            worker_attestation,
            worker_lifecycle,
            worker_heartbeat,
            device_trust,
            model_routes,
            transaction_boundaries,
            coordinator_events,
            ledger_entries,
            update_rollback,
        )
    )
    if has_revocation_signal and not revocation_evidence_refs:
        drift_classes.append("evidence_missing_for_revocation")

    verifier_authority = next(
        (
            authority for authority in authorities
            if isinstance(authority, dict)
            and str(authority.get("authority_type") or "") == "verifier_owner"
            and str(authority.get("tenant_id") or "") == tenant_id
        ),
        None,
    )
    if verifier_authority is None or str(verifier_authority.get("authority_status") or "") in {
        "revoked",
        "expired",
        "suspended",
        "blocked_mvp",
    }:
        if appraisal_status in {"active", "approved"}:
            drift_classes.append("verifier_authority_revoked_but_appraisal_active")

    drift_classes = sorted(set(drift_classes))
    reason_codes = ["attestation_reconciliation_drift"] if drift_classes else ["approved"]
    for drift in drift_classes:
        mapped = DRIFT_REASON_MAP.get(drift)
        if mapped is not None:
            reason_codes.append(mapped)
    if revocation_status == "pending":
        reason_codes.append("attestation_revocation_pending")
    if revocation_status in {"pending", "failed_closed"} and any(_route_is_privileged_selected(r) for r in model_routes):
        reason_codes.append("attestation_revocation_not_propagated")
    reason_codes = sorted(set(validate_reason_codes(reason_codes)))

    if lineage_status == "blocked_mvp" or str((verifier_authority or {}).get("authority_status") or "") == "blocked_mvp":
        reconciliation_status = "blocked_mvp"
    elif "cross_tenant_attestation_linkage" in drift_classes or "evidence_missing_for_revocation" in drift_classes:
        reconciliation_status = "failed_closed"
    elif "quarantine_required_but_worker_active" in drift_classes:
        reconciliation_status = "quarantine_required"
    elif revocation_status == "pending":
        reconciliation_status = "revocation_pending"
    elif drift_classes:
        reconciliation_status = "drift_detected"
    else:
        reconciliation_status = "reconciled"

    return {
        "reconciliation_id": str(lineage.get("lineage_id") or ""),
        "lineage_id": str(lineage.get("lineage_id") or ""),
        "tenant_id": tenant_id,
        "reconciliation_status": reconciliation_status,
        "drift_classes": drift_classes,
        "reason_codes": reason_codes,
        "evidence_refs": evidence_refs,
        "fail_closed": reconciliation_status != "reconciled",
        "can_authorize": False,
    }
