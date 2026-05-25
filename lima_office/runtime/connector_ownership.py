"""Mock-only connector ownership and escalation classifiers."""

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


def classify_connector_ownership(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify connector ownership metadata only. Always non-authorizing."""

    payload = _ensure_object("connector.ownership", payload)
    ownership_status = str(payload.get("ownership_status") or "")
    source_status = str(payload.get("source_of_truth_status") or "")
    sod_status = str(payload.get("separation_of_duties_status") or "")
    reason_codes = set(validate_reason_codes(list(payload.get("reason_codes") or [])))

    derived: set[str] = set()
    blocked = False
    fail_closed = False

    if ownership_status == "active":
        if not _has_values(payload.get("owner_refs")):
            derived.add("connector_owner_missing")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("reviewer_refs")):
            derived.add("connector_owner_missing")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("evidence_refs")):
            derived.add("evidence_ref_missing")
            blocked = True
            fail_closed = True

    if ownership_status in {"stale", "failed_closed"}:
        derived.add("connector_owner_stale")
        blocked = True
        fail_closed = True
    if ownership_status in {"transferred", "revoked"} and not _has_values(payload.get("evidence_refs")):
        derived.add("connector_accountability_failed_closed")
        blocked = True
        fail_closed = True
    if ownership_status == "blocked_mvp":
        derived.add("connector_acceptance_blocked_mvp")
        blocked = True
        fail_closed = True

    if source_status in {"missing", "stale"}:
        derived.add("connector_source_of_truth_missing")
        blocked = True
        fail_closed = True
    if source_status in {"conflicted", "failed_closed"}:
        derived.add("connector_source_of_truth_conflict")
        blocked = True
        fail_closed = True

    if sod_status in {"violated", "failed_closed"}:
        derived.add("connector_sod_violation")
        blocked = True
        fail_closed = True

    if (blocked or fail_closed) and not _has_values(payload.get("evidence_refs")):
        derived.add("connector_accountability_failed_closed")
        blocked = True
        fail_closed = True

    merged = sorted(validate_reason_codes(sorted(reason_codes | derived)))
    normalized_status = ownership_status
    if normalized_status == "active" and (blocked or fail_closed):
        normalized_status = "failed_closed"

    return {
        "connector_ownership_id": str(payload.get("connector_ownership_id") or ""),
        "ownership_status": normalized_status,
        "source_of_truth_status": source_status,
        "separation_of_duties_status": sod_status,
        "reason_codes": merged,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }


def classify_connector_escalation(
    payload: dict[str, Any], *, ownership: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Classify connector escalation metadata only. Always non-authorizing."""

    payload = _ensure_object("connector.escalation", payload)
    escalation_type = str(payload.get("escalation_type") or "")
    escalation_status = str(payload.get("escalation_status") or "")
    reason_codes = set(validate_reason_codes(list(payload.get("reason_codes") or [])))

    derived: set[str] = set()
    blocked = False
    fail_closed = False

    if escalation_type == "missing_owner":
        derived.add("connector_owner_missing")
        blocked = True
        fail_closed = True
    if escalation_type == "stale_owner":
        derived.add("connector_owner_stale")
        blocked = True
        fail_closed = True
    if escalation_type == "source_of_truth_conflict":
        derived.add("connector_source_of_truth_conflict")
        blocked = True
        fail_closed = True
    if escalation_type == "sod_violation":
        derived.add("connector_sod_violation")
        blocked = True
        fail_closed = True
    if escalation_type == "revocation_overdue":
        derived.add("connector_escalation_overdue")
        blocked = True
        fail_closed = True
        if not str(payload.get("escalation_owner_ref") or ""):
            derived.add("connector_revocation_owner_missing")
            blocked = True
            fail_closed = True
    if escalation_type == "disable_switch_failed":
        derived.add("connector_disable_owner_missing")
        blocked = True
        fail_closed = True
    if escalation_type == "blocked_mvp":
        derived.add("connector_acceptance_blocked_mvp")
        blocked = True
        fail_closed = True

    if escalation_status in {"failed_closed", "blocked_mvp"}:
        blocked = True
        fail_closed = True
    if escalation_status == "resolved":
        if not str(payload.get("resolved_at") or ""):
            derived.add("connector_accountability_failed_closed")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("evidence_refs")):
            derived.add("connector_accountability_failed_closed")
            blocked = True
            fail_closed = True

    if escalation_type in {"missing_owner", "stale_owner", "revocation_overdue"} and not _has_values(
        payload.get("evidence_refs")
    ):
        derived.add("connector_accountability_failed_closed")
        blocked = True
        fail_closed = True

    if ownership is not None:
        ownership = _ensure_object("connector.ownership", ownership)
        if str(ownership.get("tenant_id") or "") != str(payload.get("tenant_id") or ""):
            derived.add("connector_cross_tenant_linkage")
            blocked = True
            fail_closed = True
        if str(ownership.get("connector_id") or "") != str(payload.get("connector_id") or ""):
            derived.add("connector_owner_conflict")
            blocked = True
            fail_closed = True
        if str(ownership.get("ownership_status") or "") in {"stale", "failed_closed", "revoked"}:
            derived.add("connector_owner_stale")
            blocked = True
            fail_closed = True

    merged = sorted(validate_reason_codes(sorted(reason_codes | derived)))
    normalized_status = escalation_status
    if normalized_status == "resolved" and (blocked or fail_closed):
        normalized_status = "failed_closed"

    return {
        "connector_escalation_id": str(payload.get("connector_escalation_id") or ""),
        "escalation_type": escalation_type,
        "escalation_status": normalized_status,
        "reason_codes": merged,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }
