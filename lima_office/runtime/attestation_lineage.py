"""Mock-only attestation lineage and authority posture classifier."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


BLOCKING_LINEAGE_STATUSES = frozenset(
    {"stale", "revoked", "conflicted", "quarantine_required", "blocked_mvp"}
)
BLOCKING_PROPAGATION_STATUSES = frozenset({"pending", "failed_closed", "blocked_mvp"})
BLOCKING_AUTHORITY_STATUSES = frozenset({"revoked", "expired", "suspended", "blocked_mvp"})


def evaluate_attestation_lineage(
    *,
    lineage: dict[str, Any],
    authorities: list[dict[str, Any]],
    privileged_context: bool = True,
) -> dict[str, Any]:
    """Classify lineage + authority metadata. Always non-authorizing."""

    if not isinstance(lineage, dict):
        raise PolicyDenyError("lineage payload must be an object")

    validate_taxonomy_version(str(lineage.get("taxonomy_version") or ""))
    reasons: set[str] = set(validate_reason_codes(list(lineage.get("reason_codes") or [])))
    blocked = False

    lineage_status = str(lineage.get("lineage_status") or "")
    trust_effect = str(lineage.get("trust_effect") or "")
    revocation_status = str(lineage.get("revocation_propagation_status") or "")

    if lineage_status in BLOCKING_LINEAGE_STATUSES:
        blocked = True
    if revocation_status in BLOCKING_PROPAGATION_STATUSES:
        blocked = True
    if trust_effect == "trusted_metadata_only" and (
        lineage_status != "current" or revocation_status in BLOCKING_PROPAGATION_STATUSES
    ):
        reasons.add("attestation_result_trust_conflict")
        blocked = True

    tenant_id = str(lineage.get("tenant_id") or "")
    verifier_authority: dict[str, Any] | None = None
    for authority in authorities:
        if not isinstance(authority, dict):
            continue
        validate_taxonomy_version(str(authority.get("taxonomy_version") or ""))
        if str(authority.get("tenant_id") or "") != tenant_id:
            continue
        if str(authority.get("authority_type") or "") == "verifier_owner":
            verifier_authority = authority
            break

    if verifier_authority is None:
        reasons.add("verifier_authority_missing")
        blocked = True
    else:
        authority_status = str(verifier_authority.get("authority_status") or "")
        if authority_status in BLOCKING_AUTHORITY_STATUSES:
            reasons.add("verifier_authority_revoked")
            blocked = True

        if "clear_worker_quarantine" in list(verifier_authority.get("allowed_authority_actions") or []):
            if not bool(verifier_authority.get("separation_of_duties_required")):
                reasons.add("quarantine_clearance_sod_required")
                blocked = True

    if privileged_context and trust_effect != "trusted_metadata_only":
        blocked = True

    return {
        "lineage_id": str(lineage.get("lineage_id") or ""),
        "tenant_id": tenant_id,
        "lineage_status": lineage_status,
        "revocation_propagation_status": revocation_status,
        "trust_effect": trust_effect,
        "reason_codes": sorted(validate_reason_codes(sorted(reasons))),
        "blocked": blocked,
        "fail_closed": blocked,
        "can_authorize": False,
    }
