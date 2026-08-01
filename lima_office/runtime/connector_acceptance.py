"""Mock-only connector acceptance-score and reconciliation-SLO classifiers."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


def _ensure_object(name: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PolicyDenyError(f"{name} must be an object")
    validate_taxonomy_version(str(payload.get("taxonomy_version") or ""))
    return payload


def _has_values(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def classify_reconciliation_slo(slo: dict[str, Any]) -> dict[str, Any]:
    """Classify reconciliation-SLO metadata only. Always non-authorizing."""

    slo = _ensure_object("connector.reconciliation_slo", slo)
    cadence_status = str(slo.get("cadence_status") or "")
    revocation_status = str(slo.get("revocation_propagation_status") or "")
    disable_status = str(slo.get("disable_switch_verification_status") or "")
    reason_codes = set(validate_reason_codes(list(slo.get("reason_codes") or [])))

    derived: set[str] = set()
    blocked = False
    fail_closed = False

    if cadence_status in {"stale", "missed"}:
        derived.add("connector_slo_stale" if cadence_status == "stale" else "connector_slo_missed")
        blocked = True
        fail_closed = True
    if cadence_status == "failed_closed":
        derived.add("connector_score_failed_closed")
        blocked = True
        fail_closed = True
    if cadence_status == "blocked_mvp":
        derived.add("connector_acceptance_blocked_mvp")
        blocked = True
        fail_closed = True

    if revocation_status == "pending":
        derived.add("connector_revocation_propagation_pending")
        blocked = True
        fail_closed = True
    elif revocation_status == "missed":
        derived.add("connector_revocation_propagation_missed")
        blocked = True
        fail_closed = True
    elif revocation_status == "failed_closed":
        derived.add("connector_score_failed_closed")
        blocked = True
        fail_closed = True

    if disable_status == "missed":
        derived.add("connector_disable_verification_missed")
        blocked = True
        fail_closed = True
    elif disable_status == "failed_closed":
        derived.add("connector_score_failed_closed")
        blocked = True
        fail_closed = True

    if (blocked or fail_closed) and not _has_values(slo.get("evidence_refs")):
        derived.add("connector_source_of_truth_missing")
        fail_closed = True
        blocked = True

    merged_codes = sorted(validate_reason_codes(sorted(reason_codes | derived)))
    return {
        "reconciliation_slo_id": str(slo.get("reconciliation_slo_id") or ""),
        "cadence_status": cadence_status,
        "revocation_propagation_status": revocation_status,
        "disable_switch_verification_status": disable_status,
        "reason_codes": merged_codes,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }


def classify_acceptance_score(
    score: dict[str, Any],
    *,
    provider_profile: dict[str, Any] | None = None,
    reconciliation_slo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify acceptance-score metadata only. Always non-authorizing."""

    score = _ensure_object("connector.acceptance_score", score)
    score_status = str(score.get("score_status") or "")
    reason_codes = set(validate_reason_codes(list(score.get("reason_codes") or [])))

    derived: set[str] = set()
    blocked = False
    fail_closed = False

    if score_status in {"failed_closed", "blocked_mvp", "revoked"}:
        blocked = True
        fail_closed = True
    if score_status == "failed_closed":
        derived.add("connector_score_failed_closed")
    if score_status == "degraded":
        derived.add("connector_score_degraded")
        blocked = True
    if score_status == "blocked_mvp":
        derived.add("connector_acceptance_blocked_mvp")
    if score_status == "review_required":
        derived.add("connector_score_below_threshold")
        blocked = True

    if score_status == "approved_for_lab":
        if _has_values(score.get("failed_dimensions")):
            blocked = True
            fail_closed = True
            derived.add("connector_score_below_threshold")
        if not _has_values(score.get("evidence_refs")):
            blocked = True
            fail_closed = True
            derived.add("evidence_ref_missing")

    if score_status in {"degraded", "revoked", "failed_closed"}:
        if not _has_values(score.get("reason_codes")):
            blocked = True
            fail_closed = True
            derived.add("connector_score_failed_closed")
        if not _has_values(score.get("evidence_refs")):
            blocked = True
            fail_closed = True
            derived.add("evidence_ref_missing")

    if provider_profile is not None:
        provider_profile = _ensure_object("connector.provider_profile", provider_profile)
        risk_level = str(provider_profile.get("risk_level") or "")
        provider_status = str(provider_profile.get("provider_status") or "")
        if risk_level == "critical":
            if provider_status != "review_required" and not _has_values(provider_profile.get("evidence_refs")):
                blocked = True
                fail_closed = True
                derived.add("connector_provider_critical_risk")
                derived.add("connector_score_below_threshold")

    if reconciliation_slo is not None:
        slo_result = classify_reconciliation_slo(reconciliation_slo)
        if slo_result["revocation_propagation_status"] in {"pending", "missed", "failed_closed"}:
            if score_status == "approved_for_lab":
                blocked = True
                fail_closed = True
            derived.add("connector_revocation_propagation_pending")
        if slo_result["cadence_status"] in {"stale", "missed", "failed_closed"}:
            blocked = True
            fail_closed = True
            derived.add("connector_reconciliation_stale")

    merged_codes = sorted(validate_reason_codes(sorted(reason_codes | derived)))
    normalized_status = score_status
    if normalized_status == "approved_for_lab" and (blocked or fail_closed):
        normalized_status = "failed_closed"

    return {
        "acceptance_score_id": str(score.get("acceptance_score_id") or ""),
        "score_status": normalized_status,
        "reason_codes": merged_codes,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }
