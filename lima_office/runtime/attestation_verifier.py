"""Mock-only attestation verifier for metadata classification."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


BLOCKING_ATTESTATION_STATUSES = frozenset({"failed", "expired", "revoked", "blocked_mvp"})
BLOCKING_ENDORSEMENT_STATUSES = frozenset({"revoked", "expired", "untrusted", "blocked_mvp"})
BLOCKING_POLICY_STATUSES = frozenset({"revoked", "blocked_mvp"})
REFERENCE_ACTIVE_STATES = frozenset({"active"})


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _now_utc(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(UTC)
    if now.tzinfo is None:
        raise PolicyDenyError("reference time must be timezone-aware")
    return now


def _taxonomy(payload: dict[str, Any]) -> None:
    validate_taxonomy_version(str(payload.get("taxonomy_version") or ""))
    validate_reason_codes(list(payload.get("reason_codes") or []))


def evaluate_attestation_metadata(
    *,
    attestation: dict[str, Any],
    appraisal_policy: dict[str, Any] | None,
    reference_values: list[dict[str, Any]],
    endorsements: list[dict[str, Any]],
    update_record: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate metadata-only attestation posture and fail closed on ambiguity."""

    _taxonomy(attestation)
    current = _now_utc(now)

    reasons: set[str] = set(validate_reason_codes(list(attestation.get("reason_codes") or [])))
    attestation_status = str(attestation.get("attestation_status") or "")
    trust_root_status = str(attestation.get("trust_root_status") or "")
    worker_id = str(attestation.get("worker_id") or "")
    deployment_id = str(attestation.get("deployment_id") or "")

    if attestation_status in BLOCKING_ATTESTATION_STATUSES:
        if attestation_status == "expired":
            reasons.add("attestation_result_expired")
        else:
            reasons.add("attestation_quarantine_required")
        return _result(
            attestation=attestation,
            appraisal_policy_id=str((appraisal_policy or {}).get("appraisal_policy_id") or ""),
            appraisal_result="fail",
            trust_effect="quarantine_required",
            reasons=reasons,
            now=current,
            expires_at=attestation.get("expires_at"),
        )

    if trust_root_status in {"unknown", "failed", "blocked_mvp"}:
        reasons.add("trust_root_failed" if trust_root_status == "failed" else "trust_root_unknown")

    if appraisal_policy is None:
        reasons.add("appraisal_policy_missing")
        return _result(
            attestation=attestation,
            appraisal_policy_id="",
            appraisal_result="fail",
            trust_effect="quarantine_required",
            reasons=reasons,
            now=current,
            expires_at=attestation.get("expires_at"),
        )

    _taxonomy(appraisal_policy)
    policy_status = str(appraisal_policy.get("policy_status") or "")
    policy_id = str(appraisal_policy.get("appraisal_policy_id") or "")
    if policy_status in BLOCKING_POLICY_STATUSES:
        reasons.add("appraisal_policy_revoked")
        return _result(
            attestation=attestation,
            appraisal_policy_id=policy_id,
            appraisal_result="fail",
            trust_effect="quarantine_required",
            reasons=reasons,
            now=current,
            expires_at=attestation.get("expires_at"),
        )
    if policy_status not in {"approved", "active"}:
        reasons.add("appraisal_policy_missing")
        return _result(
            attestation=attestation,
            appraisal_policy_id=policy_id,
            appraisal_result="inconclusive",
            trust_effect="degraded",
            reasons=reasons,
            now=current,
            expires_at=attestation.get("expires_at"),
        )

    ref_by_type: dict[str, list[dict[str, Any]]] = {}
    for ref in reference_values:
        _taxonomy(ref)
        if str(ref.get("tenant_id") or "") != str(attestation.get("tenant_id") or ""):
            reasons.add("attestation_reference_mismatch")
            continue
        ref_type = str(ref.get("reference_value_type") or "")
        ref_by_type.setdefault(ref_type, []).append(ref)

    required_ref_types = [str(v) for v in appraisal_policy.get("required_reference_value_types") or []]
    for ref_type in required_ref_types:
        candidates = ref_by_type.get(ref_type, [])
        if not candidates:
            reasons.add("reference_value_missing")
            continue

        active_candidates = [
            candidate
            for candidate in candidates
            if str(candidate.get("reference_status") or "") in REFERENCE_ACTIVE_STATES
        ]
        if not active_candidates:
            reasons.add("reference_value_missing")
            if any(str(candidate.get("reference_status") or "") == "revoked" for candidate in candidates):
                reasons.add("reference_value_revoked")
            continue

        stale = True
        for candidate in active_candidates:
            expires_at = _parse_timestamp(candidate.get("expires_at"))
            if expires_at is None or expires_at >= current:
                stale = False
                break
        if stale:
            reasons.add("reference_value_stale")

    endorsements_by_type: dict[str, list[dict[str, Any]]] = {}
    for endorsement in endorsements:
        _taxonomy(endorsement)
        if str(endorsement.get("tenant_id") or "") != str(attestation.get("tenant_id") or ""):
            reasons.add("attestation_reference_mismatch")
            continue
        endorsements_by_type.setdefault(str(endorsement.get("endorsement_type") or ""), []).append(
            endorsement
        )

    required_endorsement_types = [str(v) for v in appraisal_policy.get("required_endorsement_types") or []]
    for end_type in required_endorsement_types:
        candidates = endorsements_by_type.get(end_type, [])
        if not candidates:
            reasons.add("endorsement_missing")
            continue
        trusted = False
        for candidate in candidates:
            status = str(candidate.get("endorsement_status") or "")
            if status in BLOCKING_ENDORSEMENT_STATUSES:
                if status == "revoked":
                    reasons.add("endorsement_revoked")
                if status == "expired":
                    reasons.add("endorsement_expired")
                continue
            if status != "trusted_placeholder":
                continue
            valid_until = _parse_timestamp(candidate.get("valid_until"))
            if valid_until is not None and valid_until < current:
                reasons.add("endorsement_expired")
                continue
            trusted = True
            break
        if not trusted:
            reasons.add("endorsement_missing")

    if update_record is not None:
        _taxonomy(update_record)
        status = str(update_record.get("update_status") or "")
        update_reasons = validate_reason_codes(
            list(update_record.get("verification_reason_codes") or [])
            + list(update_record.get("rollback_reason_codes") or [])
        )
        reasons.update(update_reasons)
        if status in {"failed", "rolled_back", "blocked_mvp"}:
            reasons.add("attestation_quarantine_required")

    appraisal_fail_reasons = {
        "reference_value_missing",
        "reference_value_stale",
        "reference_value_revoked",
        "endorsement_missing",
        "endorsement_revoked",
        "endorsement_expired",
        "appraisal_policy_missing",
        "appraisal_policy_revoked",
        "attestation_reference_mismatch",
        "trust_root_failed",
    }
    if appraisal_fail_reasons.intersection(reasons):
        reasons.add("appraisal_failed")
        trust_effect = "quarantine_required"
        if reasons.intersection({"reference_value_stale", "endorsement_expired"}):
            trust_effect = "degraded"
        return _result(
            attestation=attestation,
            appraisal_policy_id=policy_id,
            appraisal_result="fail" if trust_effect == "quarantine_required" else "inconclusive",
            trust_effect=trust_effect,
            reasons=reasons,
            now=current,
            expires_at=attestation.get("expires_at"),
        )

    reasons.add("approved")
    return _result(
        attestation=attestation,
        appraisal_policy_id=policy_id,
        appraisal_result="pass",
        trust_effect="trusted_metadata_only",
        reasons=reasons,
        now=current,
        expires_at=attestation.get("expires_at"),
    )


def _result(
    *,
    attestation: dict[str, Any],
    appraisal_policy_id: str,
    appraisal_result: str,
    trust_effect: str,
    reasons: set[str],
    now: datetime,
    expires_at: Any,
) -> dict[str, Any]:
    reason_codes = sorted(set(validate_reason_codes(sorted(reasons))))
    expires = _parse_timestamp(expires_at)
    if appraisal_result == "pass" and expires is None:
        expires = now
    return {
        "contract_name": "attestation.result",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "taxonomy_version": str(attestation.get("taxonomy_version") or ""),
        "tenant_id": str(attestation.get("tenant_id") or ""),
        "customer_context_id": str(attestation.get("customer_context_id") or ""),
        "environment": str(attestation.get("environment") or "mock"),
        "correlation_id": str(attestation.get("correlation_id") or ""),
        "causation_id": str(attestation.get("attestation_id") or ""),
        "idempotency_key": str(attestation.get("idempotency_key") or ""),
        "producer": {
            "component": "supervisor",
            "produced_at": now.isoformat()
        },
        "attestation_result_id": f"attres-{attestation.get('attestation_id')}",
        "worker_id": str(attestation.get("worker_id") or ""),
        "deployment_id": str(attestation.get("deployment_id") or ""),
        "appraisal_policy_id": appraisal_policy_id,
        "reference_value_refs": list(attestation.get("reference_value_refs") or []),
        "endorsement_refs": list(attestation.get("endorsement_refs") or []),
        "attestation_evidence_refs": list(attestation.get("evidence_refs") or []),
        "appraisal_result": appraisal_result,
        "trust_effect": trust_effect,
        "reason_codes": reason_codes,
        "evidence_refs": list(attestation.get("evidence_refs") or []),
        "policy_version": str(attestation.get("policy_version") or ""),
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat() if expires is not None else None,
        "can_authorize": False
    }
