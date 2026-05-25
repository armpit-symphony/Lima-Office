"""Mock-only connector readiness classifier."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


BLOCKED_CONNECTOR_TYPES = frozenset(
    {"browser", "rmm_it", "cloud_provider", "payment", "legal_regulated", "blocked_mvp"}
)
BLOCKED_ACTIONS = frozenset(
    {
        "external_send",
        "form_submit",
        "customer_record_mutation",
        "connector_admin",
        "production_remediation",
        "live_execution",
    }
)
SECRET_FIELD_TOKENS = (
    "api_key",
    "oauth_token",
    "refresh_token",
    "access_token",
    "private_key",
    "password",
    "secret_value",
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


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise PolicyDenyError(f"{key} is required and must be a non-empty string")
    return value


def classify_connector_readiness(
    readiness: dict[str, Any],
    *,
    scope_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify connector readiness metadata. Always non-authorizing."""

    if not isinstance(readiness, dict):
        raise PolicyDenyError("readiness payload must be an object")
    validate_taxonomy_version(str(readiness.get("taxonomy_version") or ""))

    if _walk_secret_like_keys(readiness):
        raise PolicyDenyError("secret/token/key material fields are not allowed in readiness payloads")

    reason_codes = set(validate_reason_codes(list(readiness.get("reason_codes") or [])))
    lifecycle_state = str(readiness.get("lifecycle_state") or "")
    readiness_status = str(readiness.get("readiness_status") or "")
    connector_type = str(readiness.get("connector_type") or "")

    blocked = False
    failure_reasons: set[str] = set()

    if connector_type in BLOCKED_CONNECTOR_TYPES:
        blocked = True
        failure_reasons.add("connector_live_blocked_mvp")

    if lifecycle_state == "live_blocked_mvp" or readiness_status == "blocked_mvp":
        blocked = True
        failure_reasons.add("connector_live_blocked_mvp")

    consent_ref = readiness.get("consent_ref")
    if readiness_status in {"approved_for_lab", "review_required"} and (
        not isinstance(consent_ref, str) or not consent_ref
    ):
        blocked = True
        failure_reasons.add("connector_consent_missing")

    scope_refs = readiness.get("scope_refs")
    if readiness_status in {"approved_for_lab", "review_required"} and (
        not isinstance(scope_refs, list) or not scope_refs
    ):
        blocked = True
        failure_reasons.add("connector_scope_denied")

    revocation_refs = readiness.get("revocation_refs")
    if not isinstance(revocation_refs, list) or not revocation_refs:
        blocked = True
        failure_reasons.add("connector_revocation_missing")

    evidence_refs = readiness.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        blocked = True
        failure_reasons.add("evidence_ref_missing")

    rate_limit_ref = readiness.get("rate_limit_policy_ref")
    if readiness_status in {"approved_for_lab", "review_required"} and (
        not isinstance(rate_limit_ref, str) or not rate_limit_ref
    ):
        blocked = True
        failure_reasons.add("connector_rate_limit_missing")

    export_delete_refs = readiness.get("export_delete_impact_refs")
    if readiness_status in {"approved_for_lab", "review_required"} and (
        not isinstance(export_delete_refs, list) or not export_delete_refs
    ):
        blocked = True
        failure_reasons.add("connector_export_delete_impact_unknown")

    approval_policy_refs = readiness.get("approval_policy_refs")
    if not isinstance(approval_policy_refs, list) or not approval_policy_refs:
        blocked = True
        failure_reasons.add("connector_outbound_action_blocked")

    prompt_injection_policy_refs = readiness.get("prompt_injection_policy_refs")
    if not isinstance(prompt_injection_policy_refs, list) or not prompt_injection_policy_refs:
        blocked = True
        failure_reasons.add("connector_prompt_injection_risk")

    outbound_policy_ref = readiness.get("outbound_action_policy_ref")
    if not isinstance(outbound_policy_ref, str) or not outbound_policy_ref:
        blocked = True
        failure_reasons.add("connector_outbound_action_blocked")

    allowed_actions = readiness.get("allowed_actions")
    if isinstance(allowed_actions, list) and any(action in BLOCKED_ACTIONS for action in allowed_actions):
        blocked = True
        failure_reasons.add("connector_outbound_action_blocked")

    secrets_ref = readiness.get("secrets_ref")
    if secrets_ref is None or (isinstance(secrets_ref, str) and secrets_ref):
        pass
    else:
        blocked = True
        failure_reasons.add("connector_secret_policy_missing")

    if scope_review is not None:
        if not isinstance(scope_review, dict):
            raise PolicyDenyError("scope_review payload must be an object")
        validate_taxonomy_version(str(scope_review.get("taxonomy_version") or ""))
        if _walk_secret_like_keys(scope_review):
            raise PolicyDenyError(
                "secret/token/key material fields are not allowed in scope_review payloads"
            )
        if str(scope_review.get("tenant_id") or "") != str(readiness.get("tenant_id") or ""):
            blocked = True
            failure_reasons.add("recon_cross_tenant_linkage")

        least_privilege_status = str(scope_review.get("least_privilege_status") or "")
        if least_privilege_status in {"overbroad", "denied", "blocked_mvp"}:
            blocked = True
            if least_privilege_status == "overbroad":
                failure_reasons.add("connector_scope_overbroad")
            else:
                failure_reasons.add("connector_scope_denied")

        if str(scope_review.get("object_authorization_status") or "") in {"missing", "failed_closed"}:
            blocked = True
            failure_reasons.add("connector_object_auth_missing")
        if str(scope_review.get("property_authorization_status") or "") in {"missing", "failed_closed"}:
            blocked = True
            failure_reasons.add("connector_property_auth_missing")

    combined_reason_codes = sorted(validate_reason_codes(sorted(reason_codes | failure_reasons)))
    normalized_status = readiness_status
    if blocked and normalized_status == "approved_for_lab":
        normalized_status = "failed_closed"
    elif blocked and normalized_status not in {"blocked_mvp", "revoked", "failed_closed"}:
        normalized_status = "failed_closed"

    return {
        "connector_readiness_id": _require_string(readiness, "connector_readiness_id"),
        "connector_id": _require_string(readiness, "connector_id"),
        "connector_type": connector_type,
        "lifecycle_state": lifecycle_state,
        "readiness_status": normalized_status,
        "reason_codes": combined_reason_codes,
        "blocked": blocked,
        "fail_closed": blocked,
        "can_authorize": False,
    }
