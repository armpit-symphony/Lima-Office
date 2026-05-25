"""Mock-only model-routing posture classifier."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import classify_reason_code_set, validate_reason_codes, validate_taxonomy_version


ROUTE_MODES = frozenset({"mock_only", "local_planned", "subscription_planned", "blocked_mvp"})
ROUTE_STATUSES = frozenset({"selected", "degraded", "denied", "blocked_mvp", "unavailable"})
MODEL_ROLES = frozenset(
    {
        "supervisor_reasoning",
        "worker_draft",
        "worker_classification",
        "it_diagnostic_summary",
        "file_memory_helper",
        "governance_review",
    }
)
RISK_TIERS = frozenset({"low", "medium", "high", "blocked"})
TAINT_STATUSES = frozenset({"clean", "tainted", "suspected"})
BLOCKED_PRIVILEGED_CODES = frozenset(
    {
        "model_route_device_untrusted",
        "model_route_rbac_blocked",
    }
)


def classify_model_route(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate model-route metadata and return fail-closed posture."""

    if not isinstance(payload, dict):
        raise PolicyDenyError("model route payload must be an object")
    validate_taxonomy_version(str(payload.get("taxonomy_version") or ""))

    route_mode = payload.get("route_mode")
    route_status = payload.get("route_status")
    model_role = payload.get("model_role")
    risk_tier = payload.get("risk_tier")
    taint_status = payload.get("taint_status")
    approval_required = payload.get("approval_required")
    fallback_allowed = payload.get("fallback_allowed")

    if route_mode not in ROUTE_MODES:
        raise PolicyDenyError(f"unsupported route_mode: {route_mode}")
    if route_status not in ROUTE_STATUSES:
        raise PolicyDenyError(f"unsupported route_status: {route_status}")
    if model_role not in MODEL_ROLES:
        raise PolicyDenyError(f"unsupported model_role: {model_role}")
    if risk_tier not in RISK_TIERS:
        raise PolicyDenyError(f"unsupported risk_tier: {risk_tier}")
    if taint_status not in TAINT_STATUSES:
        raise PolicyDenyError(f"unsupported taint_status: {taint_status}")
    if not isinstance(approval_required, bool):
        raise PolicyDenyError("approval_required must be a boolean")
    if not isinstance(fallback_allowed, bool):
        raise PolicyDenyError("fallback_allowed must be a boolean")

    if route_mode == "blocked_mvp" and route_status == "selected":
        raise PolicyDenyError("blocked_mvp route_mode cannot be selected")

    route_reason_codes = validate_reason_codes(payload.get("route_reason_codes") or [])
    fallback_reason_codes = validate_reason_codes(payload.get("fallback_reason_codes") or [])

    if fallback_allowed:
        fallback_policy = payload.get("fallback_policy")
        if not isinstance(fallback_policy, str) or not fallback_policy.strip():
            raise PolicyDenyError("fallback_allowed requires fallback_policy")
        if not fallback_reason_codes:
            raise PolicyDenyError("fallback_allowed requires fallback_reason_codes")

    if risk_tier == "high":
        if not approval_required and route_status not in {"blocked_mvp", "denied"}:
            raise PolicyDenyError("high-risk route requires approval_required or blocked/denied status")
        if taint_status in {"tainted", "suspected"} and route_status not in {"blocked_mvp", "denied"}:
            raise PolicyDenyError("tainted privileged route must be denied or blocked")

    if risk_tier == "high" and BLOCKED_PRIVILEGED_CODES.intersection(route_reason_codes):
        if route_status not in {"blocked_mvp", "denied"}:
            raise PolicyDenyError("untrusted RBAC/device route reason must block privileged route")

    provider_ref = payload.get("provider_ref")
    if isinstance(provider_ref, dict) and provider_ref.get("live_call") is not False:
        raise PolicyDenyError("route metadata cannot imply live provider call")
    if route_mode == "subscription_planned":
        if not isinstance(provider_ref, dict):
            raise PolicyDenyError("subscription_planned requires provider_ref placeholder")
        if provider_ref.get("live_call") is not False:
            raise PolicyDenyError("subscription_planned cannot imply live provider call")

    local_ref = payload.get("local_model_bundle_ref")
    if isinstance(local_ref, dict) and local_ref.get("execution_enabled") is not False:
        raise PolicyDenyError("route metadata cannot imply local inference execution")
    if route_mode == "local_planned":
        if not isinstance(local_ref, dict):
            raise PolicyDenyError("local_planned requires local_model_bundle_ref placeholder")
        if local_ref.get("execution_enabled") is not False:
            raise PolicyDenyError("local_planned cannot imply local inference execution")

    if route_status == "selected":
        evidence_refs = payload.get("evidence_refs") or []
        policy_refs = payload.get("policy_refs") or []
        if not evidence_refs or not policy_refs:
            raise PolicyDenyError("selected route requires evidence_refs and policy_refs")

    reason_classification = classify_reason_code_set(
        route_reason_codes,
        unknown_reason_code_policy="fail_closed",
        deprecated_reason_code_policy="allow_with_warning",
        compatibility_status="compatible",
    )
    blocked = route_status in {"blocked_mvp", "denied", "unavailable"} or bool(reason_classification["blocked"])
    degraded = route_status == "degraded"
    return {
        "route_mode": route_mode,
        "route_status": route_status,
        "route_reason_codes": route_reason_codes,
        "fallback_reason_codes": fallback_reason_codes,
        "blocked": blocked,
        "degraded": degraded,
        "fail_closed": blocked or bool(reason_classification["fail_closed"]),
        "can_authorize": False,
    }
