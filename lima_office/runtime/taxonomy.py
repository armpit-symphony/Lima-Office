"""Mock-only taxonomy helpers for reason-code and export/delete conflict checks."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError


CANONICAL_REASON_CODES = frozenset(
    {
        "recon_missing_guardian_decision",
        "recon_stale_guardian_decision",
        "recon_mismatched_approval_binding",
        "recon_mismatched_token_verification",
        "recon_replay_record_missing",
        "recon_replay_record_mismatch",
        "recon_evidence_ref_missing",
        "recon_coordinator_event_mismatch",
        "recon_cross_tenant_linkage",
        "blocked_mvp_authorization_attempt",
        "export_delete_conflict_active",
        "export_delete_preservation_hold_active",
        "export_delete_retention_window_active",
        "export_delete_review_required",
        "export_delete_blocked_mvp",
        "evidence_ref_missing",
        "evidence_failed_closed_required",
        "export_manifest_redaction_required",
    }
)

CONFLICT_DELETE_STATUSES = frozenset({"conflict_detected", "denied", "blocked_mvp"})
BLOCKING_HOLD_STATUSES = frozenset({"active", "conflict_with_delete", "blocked_mvp"})


def validate_reason_codes(reason_codes: list[str]) -> list[str]:
    """Validate reason codes against the canonical in-repo taxonomy."""

    unknown = sorted({code for code in reason_codes if code not in CANONICAL_REASON_CODES})
    if unknown:
        raise PolicyDenyError(f"unknown reason code(s): {', '.join(unknown)}")
    return sorted(set(reason_codes))


def classify_export_delete_conflict(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify export/delete conflict metadata in memory only."""

    reason_codes = payload.get("reason_codes") or []
    if not isinstance(reason_codes, list):
        raise PolicyDenyError("reason_codes must be a list")
    normalized_reasons = validate_reason_codes(reason_codes)

    preservation_hold_status = payload.get("preservation_hold_status")
    delete_review_status = payload.get("delete_review_status")
    export_review_status = payload.get("export_review_status")
    evidence_refs = payload.get("evidence_refs") or []
    conflict_evidence_refs = payload.get("conflict_evidence_refs") or []

    if preservation_hold_status in BLOCKING_HOLD_STATUSES and delete_review_status == "approved":
        raise PolicyDenyError("preservation hold conflict blocks delete approval")
    if delete_review_status in CONFLICT_DELETE_STATUSES and not conflict_evidence_refs:
        raise PolicyDenyError("conflict-detected delete review requires conflict evidence refs")
    if export_review_status in {"denied", "failed_closed", "blocked_mvp"} and not evidence_refs:
        raise PolicyDenyError("denied/failed/blocked export review requires evidence refs")

    return {
        "reason_codes": normalized_reasons,
        "delete_blocked_by_hold": preservation_hold_status in BLOCKING_HOLD_STATUSES,
        "conflict_detected": delete_review_status in CONFLICT_DELETE_STATUSES,
        "export_denied_or_blocked": export_review_status in {"denied", "failed_closed", "blocked_mvp"},
        "can_authorize": False,
    }

