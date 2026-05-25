"""Mock-only model-routing posture classifier."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import classify_reason_code_set, validate_reason_codes, validate_taxonomy_version


ROUTE_MODES = frozenset({"mock_only", "local_planned", "subscription_planned", "blocked_mvp"})
ROUTE_STATUSES = frozenset({"selected", "degraded", "denied", "blocked_mvp", "unavailable"})
BLOCKED_PRIVILEGED_CODES = frozenset(
    {
        "model_route_device_untrusted",
        "model_route_rbac_blocked",
    }
)
TRUST_BLOCK_CODES = frozenset(
    {
        "attestation_failed",
        "attestation_expired",
        "trust_root_unknown",
        "trust_root_failed",
        "reference_value_missing",
        "reference_value_stale",
        "reference_value_revoked",
        "endorsement_missing",
        "endorsement_revoked",
        "endorsement_expired",
        "appraisal_policy_missing",
        "appraisal_policy_revoked",
        "appraisal_failed",
        "appraisal_inconclusive",
        "attestation_result_expired",
        "attestation_quarantine_required",
        "attestation_reference_mismatch",
        "attestation_lineage_stale",
        "attestation_lineage_revoked",
        "attestation_lineage_conflicted",
        "attestation_result_trust_conflict",
        "revocation_propagation_pending",
        "revocation_propagation_failed",
        "verifier_authority_missing",
        "verifier_authority_revoked",
        "reference_authority_missing",
        "endorsement_authority_missing",
        "quarantine_clearance_sod_required",
        "update_signature_missing",
        "update_signature_invalid",
        "update_provenance_missing",
        "model_bundle_untrusted",
        "policy_bundle_untrusted",
        "runtime_bundle_untrusted",
    }
)


def classify_model_route(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate model-route metadata and return fail-closed posture."""

    if not isinstance(payload, dict):
        raise PolicyDenyError("model route payload must be an object")
    validate_taxonomy_version(str(payload.get("taxonomy_version") or ""))

    route_mode = payload.get("route_mode")
    route_status = payload.get("route_status")
    if route_mode not in ROUTE_MODES:
        raise PolicyDenyError(f"unsupported route_mode: {route_mode}")
    if route_status not in ROUTE_STATUSES:
        raise PolicyDenyError(f"unsupported route_status: {route_status}")

    if route_mode == "blocked_mvp" and route_status == "selected":
        raise PolicyDenyError("blocked_mvp route_mode cannot be selected")

    route_reason_codes = validate_reason_codes(payload.get("route_reason_codes") or [])
    fallback_reason_codes = validate_reason_codes(payload.get("fallback_reason_codes") or [])

    fallback_allowed = bool(payload.get("fallback_allowed"))
    if fallback_allowed:
        fallback_policy = payload.get("fallback_policy")
        if not isinstance(fallback_policy, str) or not fallback_policy.strip():
            raise PolicyDenyError("fallback_allowed requires fallback_policy")
        if not fallback_reason_codes:
            raise PolicyDenyError("fallback_allowed requires fallback_reason_codes")

    risk_tier = payload.get("risk_tier")
    approval_required = bool(payload.get("approval_required"))
    taint_status = payload.get("taint_status")
    if risk_tier == "high":
        if not approval_required and route_status not in {"blocked_mvp", "denied"}:
            raise PolicyDenyError("high-risk route requires approval_required or blocked/denied status")
        if taint_status in {"tainted", "suspected"} and route_status not in {"blocked_mvp", "denied"}:
            raise PolicyDenyError("tainted privileged route must be denied or blocked")
        for ref_field in (
            "rbac_context_ref",
            "session_policy_ref",
            "device_trust_ref",
            "worker_attestation_ref",
            "attestation_result_ref",
            "appraisal_policy_ref",
            "update_rollback_ref",
        ):
            ref_value = payload.get(ref_field)
            if route_status == "selected" and (not isinstance(ref_value, str) or not ref_value.strip()):
                raise PolicyDenyError(
                    f"high-risk selected route requires {ref_field}"
                )

    if risk_tier == "high" and BLOCKED_PRIVILEGED_CODES.intersection(route_reason_codes):
        if route_status not in {"blocked_mvp", "denied"}:
            raise PolicyDenyError("untrusted RBAC/device route reason must block privileged route")
    if "model_route_device_untrusted" in route_reason_codes:
        device_trust_ref = payload.get("device_trust_ref")
        if not isinstance(device_trust_ref, str) or not device_trust_ref.strip():
            raise PolicyDenyError("model_route_device_untrusted requires device_trust_ref")
    if TRUST_BLOCK_CODES.intersection(route_reason_codes):
        if route_status not in {"denied", "blocked_mvp", "unavailable"}:
            raise PolicyDenyError("trust failure reason codes require denied/blocked/unavailable status")

    provider_ref = payload.get("provider_ref")
    if route_mode == "subscription_planned":
        if not isinstance(provider_ref, dict):
            raise PolicyDenyError("subscription_planned requires provider_ref placeholder")
        if provider_ref.get("live_call") is not False:
            raise PolicyDenyError("subscription_planned cannot imply live provider call")

    local_ref = payload.get("local_model_bundle_ref")
    if route_mode == "local_planned":
        if not isinstance(local_ref, dict):
            raise PolicyDenyError("local_planned requires local_model_bundle_ref placeholder")
        if local_ref.get("execution_enabled") is not False:
            raise PolicyDenyError("local_planned cannot imply local inference execution")
        if route_status == "selected":
            attestation_ref = payload.get("worker_attestation_ref")
            if not isinstance(attestation_ref, str) or not attestation_ref.strip():
                raise PolicyDenyError("local_planned selected route requires worker_attestation_ref")

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
