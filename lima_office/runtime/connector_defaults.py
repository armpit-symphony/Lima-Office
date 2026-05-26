"""Mock-only connector defaults/SLO/threshold classifiers."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


_SECRET_FIELD_TOKENS = (
    "api_key",
    "oauth_token",
    "refresh_token",
    "access_token",
    "private_key",
    "password",
    "secret_value",
)

_BLOCKED_MVP_CATEGORIES = frozenset(
    {"browser", "rmm_it", "cloud_provider", "payment", "legal_regulated", "blocked_mvp"}
)
_BLOCKED_ACTIONS = frozenset(
    {
        "external_send",
        "form_submit",
        "record_mutation",
        "live_api_call",
        "oauth_token_exchange",
        "browser_automation",
        "remediation_execution",
        "provider_admin",
    }
)


def _walk_secret_like_keys(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(token in lowered for token in _SECRET_FIELD_TOKENS):
                return True
            if _walk_secret_like_keys(child):
                return True
    elif isinstance(value, list):
        for child in value:
            if _walk_secret_like_keys(child):
                return True
    return False


def _ensure_object(name: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PolicyDenyError(f"{name} must be an object")
    validate_taxonomy_version(str(payload.get("taxonomy_version") or ""))
    if _walk_secret_like_keys(payload):
        raise PolicyDenyError(f"{name} contains forbidden secret-like fields")
    return payload


def _has_values(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def classify_connector_defaults(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify connector defaults metadata only. Always non-authorizing."""

    payload = _ensure_object("connector.defaults", payload)
    reason_codes = set(validate_reason_codes(list(payload.get("reason_codes") or [])))
    provider_category = str(payload.get("provider_category") or "")
    risk = str(payload.get("default_risk_level") or "")
    lifecycle_state = str(payload.get("default_lifecycle_state") or "")
    override_status = str(payload.get("tenant_override_status") or "")
    allowed_actions = payload.get("default_allowed_actions")
    outbound_policy = str(payload.get("default_outbound_action_policy") or "")

    derived: set[str] = set()
    blocked = False
    fail_closed = False

    if not bool(payload.get("default_owner_required")) or not bool(payload.get("default_reviewer_required")):
        derived.add("connector_defaults_missing")
        blocked = True
        fail_closed = True

    if provider_category in _BLOCKED_MVP_CATEGORIES or lifecycle_state == "blocked_mvp":
        derived.add("connector_provider_category_blocked_mvp")
        blocked = True
        fail_closed = True
        if isinstance(allowed_actions, list) and allowed_actions:
            derived.add("connector_default_outbound_blocked")
            blocked = True
            fail_closed = True

    if risk in {"high", "critical"}:
        if not bool(payload.get("default_reviewer_required")):
            derived.add("connector_defaults_missing")
            blocked = True
            fail_closed = True
        if not bool(payload.get("default_approver_required")):
            derived.add("connector_defaults_missing")
            blocked = True
            fail_closed = True
        if not bool(payload.get("default_revocation_required")):
            derived.add("connector_defaults_missing")
            blocked = True
            fail_closed = True
        if not bool(payload.get("default_disable_switch_required")):
            derived.add("connector_defaults_missing")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("evidence_refs")):
            derived.add("connector_defaults_missing")
            blocked = True
            fail_closed = True

    if override_status == "approved_placeholder":
        if not _has_values(payload.get("evidence_refs")):
            derived.add("connector_defaults_override_review_required")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("reason_codes")):
            derived.add("connector_defaults_override_review_required")
            blocked = True
            fail_closed = True

    if outbound_policy in {"blocked_without_approval", "blocked_mvp"}:
        derived.add("connector_default_outbound_blocked")
    if isinstance(allowed_actions, list):
        if any(action in _BLOCKED_ACTIONS for action in allowed_actions):
            derived.add("connector_default_outbound_blocked")
            blocked = True
            fail_closed = True

    merged = sorted(validate_reason_codes(sorted(reason_codes | derived)))
    return {
        "connector_defaults_id": str(payload.get("connector_defaults_id") or ""),
        "provider_category": provider_category,
        "tenant_override_status": override_status,
        "reason_codes": merged,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }


def classify_connector_slo_target(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify connector SLO target metadata only. Always non-authorizing."""

    payload = _ensure_object("connector.slo_target", payload)
    reason_codes = set(validate_reason_codes(list(payload.get("reason_codes") or [])))
    provider_category = str(payload.get("provider_category") or "")
    target_status = str(payload.get("target_status") or "")

    derived: set[str] = set()
    blocked = False
    fail_closed = False

    if provider_category in _BLOCKED_MVP_CATEGORIES:
        derived.add("connector_provider_category_blocked_mvp")
        blocked = True
        fail_closed = True

    if target_status in {"stale", "missed", "failed_closed"}:
        if target_status == "missed":
            derived.add("connector_slo_target_missed")
        if not _has_values(payload.get("reason_codes")):
            derived.add("connector_slo_target_missing")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("evidence_refs")):
            derived.add("connector_slo_target_missing")
            blocked = True
            fail_closed = True
        blocked = True
        fail_closed = True

    if target_status == "active_placeholder":
        if not str(payload.get("owner_ref") or ""):
            derived.add("connector_slo_target_missing")
            blocked = True
            fail_closed = True
        if not str(payload.get("reviewer_ref") or ""):
            derived.add("connector_slo_target_missing")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("evidence_refs")):
            derived.add("connector_slo_target_missing")
            blocked = True
            fail_closed = True

    merged = sorted(validate_reason_codes(sorted(reason_codes | derived)))
    return {
        "connector_slo_target_id": str(payload.get("connector_slo_target_id") or ""),
        "target_status": target_status,
        "provider_category": provider_category,
        "reason_codes": merged,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }


def classify_connector_score_threshold(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify connector score-threshold metadata only. Always non-authorizing."""

    payload = _ensure_object("connector.score_threshold", payload)
    reason_codes = set(validate_reason_codes(list(payload.get("reason_codes") or [])))
    threshold_status = str(payload.get("threshold_status") or "")
    provider_category = str(payload.get("provider_category") or "")
    required_dimensions = payload.get("required_dimensions")

    derived: set[str] = set()
    blocked = False
    fail_closed = False

    if not isinstance(required_dimensions, list) or not required_dimensions:
        derived.add("connector_score_threshold_missing")
        blocked = True
        fail_closed = True

    if provider_category in _BLOCKED_MVP_CATEGORIES or threshold_status == "blocked_mvp":
        derived.add("connector_threshold_blocked_mvp")
        blocked = True
        fail_closed = True

    if threshold_status == "active_placeholder" and not _has_values(payload.get("evidence_refs")):
        derived.add("connector_score_threshold_missing")
        blocked = True
        fail_closed = True

    if threshold_status in {"stale", "failed_closed"}:
        if not _has_values(payload.get("reason_codes")):
            derived.add("connector_score_threshold_stale")
            blocked = True
            fail_closed = True
        if not _has_values(payload.get("evidence_refs")):
            derived.add("connector_score_threshold_stale")
            blocked = True
            fail_closed = True
        blocked = True
        fail_closed = True

    merged = sorted(validate_reason_codes(sorted(reason_codes | derived)))
    return {
        "score_threshold_id": str(payload.get("score_threshold_id") or ""),
        "threshold_status": threshold_status,
        "provider_category": provider_category,
        "reason_codes": merged,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }


def classify_connector_defaults_bundle(
    *,
    defaults: dict[str, Any] | None,
    slo_target: dict[str, Any] | None,
    score_threshold: dict[str, Any] | None,
) -> dict[str, Any]:
    """Classify defaults/SLO/threshold bundle metadata only. Always non-authorizing."""

    missing_reasons: set[str] = set()
    blocked = False
    fail_closed = False

    if defaults is None:
        missing_reasons.add("connector_defaults_missing")
        blocked = True
        fail_closed = True
        defaults_result = None
    else:
        defaults_result = classify_connector_defaults(defaults)
        blocked = blocked or bool(defaults_result["blocked"])
        fail_closed = fail_closed or bool(defaults_result["fail_closed"])
        missing_reasons.update(defaults_result["reason_codes"])

    if slo_target is None:
        missing_reasons.add("connector_slo_target_missing")
        blocked = True
        fail_closed = True
        slo_result = None
    else:
        slo_result = classify_connector_slo_target(slo_target)
        blocked = blocked or bool(slo_result["blocked"])
        fail_closed = fail_closed or bool(slo_result["fail_closed"])
        missing_reasons.update(slo_result["reason_codes"])

    if score_threshold is None:
        missing_reasons.add("connector_score_threshold_missing")
        blocked = True
        fail_closed = True
        threshold_result = None
    else:
        threshold_result = classify_connector_score_threshold(score_threshold)
        blocked = blocked or bool(threshold_result["blocked"])
        fail_closed = fail_closed or bool(threshold_result["fail_closed"])
        missing_reasons.update(threshold_result["reason_codes"])

    merged = sorted(validate_reason_codes(sorted(missing_reasons)))
    return {
        "defaults": defaults_result,
        "slo_target": slo_result,
        "score_threshold": threshold_result,
        "reason_codes": merged,
        "blocked": blocked,
        "fail_closed": fail_closed or blocked,
        "can_authorize": False,
    }
