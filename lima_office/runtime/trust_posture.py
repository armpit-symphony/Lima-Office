"""Mock-only trust-posture classifier for attestation and update metadata."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


BLOCKING_ATTESTATION_STATUSES = frozenset({"failed", "expired", "revoked", "blocked_mvp"})
BLOCKING_TRUST_ROOT_STATUSES = frozenset({"unknown", "failed", "blocked_mvp"})
BLOCKING_UPDATE_STATUSES = frozenset({"failed", "rolled_back", "blocked_mvp"})
BLOCKING_VERIFICATION_CODES = frozenset(
    {
        "update_signature_missing",
        "update_signature_invalid",
        "update_provenance_missing",
        "update_blocked_mvp",
        "model_bundle_untrusted",
        "policy_bundle_untrusted",
        "runtime_bundle_untrusted",
    }
)


def classify_trust_posture(
    *,
    attestation: dict[str, Any] | None,
    update_record: dict[str, Any] | None,
    privileged_route: bool,
) -> dict[str, Any]:
    """Classify trust posture metadata and fail closed for unsafe states."""

    reasons: set[str] = set()
    blocked = False

    if attestation is not None:
        validate_taxonomy_version(str(attestation.get("taxonomy_version") or ""))
        attestation_status = str(attestation.get("attestation_status") or "")
        trust_root_status = str(attestation.get("trust_root_status") or "")
        reasons.update(validate_reason_codes(list(attestation.get("reason_codes") or [])))

        if attestation_status in BLOCKING_ATTESTATION_STATUSES:
            blocked = True
        if trust_root_status in BLOCKING_TRUST_ROOT_STATUSES:
            blocked = True

        if privileged_route and attestation_status not in {"attested", "verified"}:
            blocked = True
            reasons.add("attestation_required")

    if update_record is not None:
        validate_taxonomy_version(str(update_record.get("taxonomy_version") or ""))
        update_status = str(update_record.get("update_status") or update_record.get("status") or "")
        verification_reasons = validate_reason_codes(
            list(update_record.get("verification_reason_codes") or [])
        )
        rollback_reasons = validate_reason_codes(list(update_record.get("rollback_reason_codes") or []))
        reasons.update(verification_reasons)
        reasons.update(rollback_reasons)

        if update_status in BLOCKING_UPDATE_STATUSES:
            blocked = True
        if BLOCKING_VERIFICATION_CODES.intersection(verification_reasons):
            blocked = True

    if not attestation and privileged_route:
        raise PolicyDenyError("missing attestation metadata for privileged route")
    if not update_record and privileged_route:
        raise PolicyDenyError("missing update metadata for privileged route")

    return {
        "blocked": blocked,
        "fail_closed": blocked,
        "reason_codes": sorted(reasons),
        "can_authorize": False,
    }
