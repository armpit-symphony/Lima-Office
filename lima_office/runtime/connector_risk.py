"""Mock-only connector provider-risk and revocation-drill classifiers."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


SECRET_FIELD_TOKENS = (
    "api_key",
    "oauth_token",
    "refresh_token",
    "access_token",
    "private_key",
    "password",
    "secret_value",
)

BLOCKED_CONNECTOR_TYPES = frozenset(
    {"browser", "rmm_it", "cloud_provider", "payment", "legal_regulated", "blocked_mvp"}
)


def _walk_secret_like_keys(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(token in lowered for token in SECRET_FIELD_TOKENS):
                return True
            if _walk_secret_like_keys(child):
                return True
    elif isinstance(value, list):
        for child in value:
            if _walk_secret_like_keys(child):
                return True
    return False


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _has_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def classify_provider_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Classify connector provider-profile metadata. Always non-authorizing."""

    if not isinstance(profile, dict):
        raise PolicyDenyError("provider profile payload must be an object")
    validate_taxonomy_version(str(profile.get("taxonomy_version") or ""))
    if _walk_secret_like_keys(profile):
        raise PolicyDenyError("secret/token/key material fields are not allowed in provider profile")

    provider_status = str(profile.get("provider_status") or "")
    risk_level = str(profile.get("risk_level") or "")
    connector_type = str(profile.get("connector_type") or "")
    reason_codes = set(validate_reason_codes(list(profile.get("reason_codes") or [])))

    blocked = False
    fail_closed = False
    derived_reasons: set[str] = set()

    if connector_type in BLOCKED_CONNECTOR_TYPES or provider_status == "blocked_mvp":
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_live_blocked_mvp")

    if provider_status == "approved_for_lab":
        if str(profile.get("revocation_method_status") or "") not in {
            "documented",
            "verified_placeholder",
        }:
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_revocation_unverified")
        if str(profile.get("disable_switch_status") or "") not in {
            "documented",
            "verified_placeholder",
        }:
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_disable_switch_missing")
        if not _has_non_empty_list(profile.get("evidence_refs")):
            blocked = True
            fail_closed = True
            derived_reasons.add("evidence_ref_missing")
        if not _has_non_empty_list(profile.get("policy_refs")):
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_revocation_unverified")

    if risk_level == "high":
        derived_reasons.add("connector_provider_high_risk")
        if provider_status not in {"review_required", "approved_for_lab", "blocked_mvp"}:
            blocked = True
            fail_closed = True
    if risk_level == "critical":
        derived_reasons.add("connector_provider_critical_risk")
        if provider_status not in {"review_required", "blocked_mvp"} and not (
            provider_status == "approved_for_lab"
            and _has_non_empty_list(profile.get("policy_refs"))
            and _has_non_empty_list(profile.get("evidence_refs"))
        ):
            blocked = True
            fail_closed = True

    if provider_status in {"disabled", "revoked"}:
        if not _has_non_empty_list(profile.get("reason_codes")):
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_revocation_unverified")
        if not _has_non_empty_list(profile.get("evidence_refs")):
            blocked = True
            fail_closed = True
            derived_reasons.add("evidence_ref_missing")

    revocation_status = str(profile.get("revocation_method_status") or "")
    if revocation_status in {"missing", "failed_closed"}:
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_revocation_unverified")
    if revocation_status == "failed_closed":
        derived_reasons.add("connector_revocation_drill_failed")

    disable_status = str(profile.get("disable_switch_status") or "")
    if disable_status in {"missing", "failed_closed"}:
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_disable_switch_missing")
    if disable_status == "failed_closed":
        derived_reasons.add("connector_disable_switch_failed")

    if str(profile.get("rate_limit_status") or "") in {"missing", "failed_closed"}:
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_rate_limit_missing")

    if str(profile.get("export_delete_impact_status") or "") in {"unknown", "failed_closed"}:
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_export_delete_impact_unknown")

    merged_reasons = sorted(validate_reason_codes(sorted(reason_codes | derived_reasons)))
    normalized_status = provider_status
    if blocked and normalized_status not in {"disabled", "revoked", "blocked_mvp"}:
        normalized_status = "review_required" if risk_level in {"high", "critical"} else "disabled"

    return {
        "provider_profile_id": str(profile.get("provider_profile_id") or ""),
        "connector_type": connector_type,
        "provider_status": normalized_status,
        "risk_level": risk_level,
        "reason_codes": merged_reasons,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }


def classify_revocation_drill(
    drill: dict[str, Any],
    *,
    readiness: dict[str, Any] | None = None,
    provider_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify connector revocation-drill metadata. Always non-authorizing."""

    if not isinstance(drill, dict):
        raise PolicyDenyError("revocation drill payload must be an object")
    validate_taxonomy_version(str(drill.get("taxonomy_version") or ""))
    if _walk_secret_like_keys(drill):
        raise PolicyDenyError("secret/token/key material fields are not allowed in revocation drill")

    drill_status = str(drill.get("drill_status") or "")
    drill_type = str(drill.get("drill_type") or "")
    expected_outcome = str(drill.get("expected_outcome") or "")
    actual_outcome = str(drill.get("actual_outcome") or "")
    reason_codes = set(validate_reason_codes(list(drill.get("reason_codes") or [])))

    blocked = False
    fail_closed = False
    derived_reasons: set[str] = set()

    if drill_status == "passed":
        if not _is_non_empty_string(drill.get("completed_at")):
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_revocation_unverified")
        if not _has_non_empty_list(drill.get("evidence_refs")):
            blocked = True
            fail_closed = True
            derived_reasons.add("evidence_ref_missing")

    if drill_status in {"failed", "failed_closed"}:
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_revocation_drill_failed")
        if not _has_non_empty_list(drill.get("reason_codes")):
            derived_reasons.add("connector_revocation_unverified")
        if not _has_non_empty_list(drill.get("evidence_refs")):
            derived_reasons.add("evidence_ref_missing")

    if drill_status == "blocked_mvp":
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_live_blocked_mvp")

    if drill_type == "cross_tenant_block":
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_cross_tenant_blocked")
        if expected_outcome != "action_blocked":
            derived_reasons.add("connector_revocation_drill_failed")

    if drill_type == "prompt_injection_block":
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_prompt_injection_blocked")

    if expected_outcome in {"failed_closed", "blocked_mvp"}:
        blocked = True
        fail_closed = True

    if actual_outcome in {"connector_usable", "action_allowed"}:
        blocked = True
        fail_closed = True
        derived_reasons.add("connector_revocation_unverified")

    if readiness is not None:
        if not isinstance(readiness, dict):
            raise PolicyDenyError("readiness payload must be an object")
        validate_taxonomy_version(str(readiness.get("taxonomy_version") or ""))
        if str(readiness.get("tenant_id") or "") != str(drill.get("tenant_id") or ""):
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_cross_tenant_blocked")

    if provider_profile is not None:
        if not isinstance(provider_profile, dict):
            raise PolicyDenyError("provider_profile payload must be an object")
        validate_taxonomy_version(str(provider_profile.get("taxonomy_version") or ""))
        if str(provider_profile.get("tenant_id") or "") != str(drill.get("tenant_id") or ""):
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_cross_tenant_blocked")
        if str(provider_profile.get("provider_status") or "") in {"revoked", "disabled", "blocked_mvp"}:
            blocked = True
            fail_closed = True
            derived_reasons.add("connector_revoked")

    merged_reasons = sorted(validate_reason_codes(sorted(reason_codes | derived_reasons)))
    normalized_status = drill_status
    if blocked and normalized_status == "passed":
        normalized_status = "failed_closed"

    return {
        "revocation_drill_id": str(drill.get("revocation_drill_id") or ""),
        "connector_id": str(drill.get("connector_id") or ""),
        "drill_type": drill_type,
        "drill_status": normalized_status,
        "reason_codes": merged_reasons,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }
