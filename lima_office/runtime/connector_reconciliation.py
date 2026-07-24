"""Mock-only connector trust-boundary reconciliation classifier."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import validate_reason_codes, validate_taxonomy_version


_TAINTED_INPUT_STATES = frozenset({"untrusted", "suspected", "confirmed"})
_CONNECTOR_REQUEST_STATES = frozenset(
    {"requested", "policy_checked", "approved_to_run", "in_progress", "completed"}
)
_GUARDIAN_ALLOW_STATES = frozenset({"allow", "allow_with_evidence", "requires_approval"})

_DRIFT_TO_REASON = {
    "consent_revoked_but_readiness_approved": "consent_revoked_but_ready",
    "scope_overbroad_but_invocation_requested": "scope_overbroad_but_invocation_requested",
    "provider_critical_but_ready": "provider_critical_but_ready",
    "revocation_drill_failed_but_connector_enabled": "revocation_drill_failed_but_enabled",
    "disable_switch_missing_but_ready": "disable_switch_missing_but_ready",
    "outbound_action_missing_approval": "outbound_missing_approval",
    "tainted_connector_payload_used_for_tool": "tainted_connector_payload_blocked",
    "connector_cross_tenant_linkage": "connector_cross_tenant_linkage",
    "connector_evidence_missing": "connector_evidence_missing",
    "connector_trust_revoked_but_guardian_allow": "connector_trust_revoked_but_allowed",
}


def _ensure_object(name: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PolicyDenyError(f"{name} must be an object")
    version = payload.get("taxonomy_version")
    validate_taxonomy_version(str(version or ""))
    return payload


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _has_values(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def classify_connector_reconciliation(
    *,
    provider_profile: dict[str, Any],
    readiness: dict[str, Any],
    scope_review: dict[str, Any],
    connector_trust: dict[str, Any],
    consent: dict[str, Any],
    revocation_drill: dict[str, Any],
    tool_invocation: dict[str, Any],
    approval_binding: dict[str, Any] | None = None,
    guardian_decision: dict[str, Any] | None = None,
    evidence_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify connector reconciliation metadata only. Always non-authorizing."""

    provider_profile = _ensure_object("provider_profile", provider_profile)
    readiness = _ensure_object("readiness", readiness)
    scope_review = _ensure_object("scope_review", scope_review)
    connector_trust = _ensure_object("connector_trust", connector_trust)
    consent = _ensure_object("consent", consent)
    revocation_drill = _ensure_object("revocation_drill", revocation_drill)
    tool_invocation = _ensure_object("tool_invocation", tool_invocation)

    drift_classes: set[str] = set()

    tenant_ids = {
        str(provider_profile.get("tenant_id") or ""),
        str(readiness.get("tenant_id") or ""),
        str(scope_review.get("tenant_id") or ""),
        str(connector_trust.get("tenant_id") or ""),
        str(consent.get("tenant_id") or ""),
        str(revocation_drill.get("tenant_id") or ""),
        str(tool_invocation.get("tenant_id") or ""),
    }
    if approval_binding is not None:
        approval_binding = _ensure_object("approval_binding", approval_binding)
        tenant_ids.add(str(approval_binding.get("tenant_id") or ""))
    if guardian_decision is not None:
        guardian_decision = _ensure_object("guardian_decision", guardian_decision)
        tenant_ids.add(str(guardian_decision.get("tenant_id") or ""))
    if evidence_artifact is not None:
        evidence_artifact = _ensure_object("evidence_artifact", evidence_artifact)
        tenant_ids.add(str(evidence_artifact.get("tenant_id") or ""))

    if len(tenant_ids) != 1:
        drift_classes.add("connector_cross_tenant_linkage")

    consent_status = str(consent.get("consent_status") or "")
    readiness_status = str(readiness.get("readiness_status") or "")
    if consent_status == "revoked" and readiness_status == "approved_for_lab":
        drift_classes.add("consent_revoked_but_readiness_approved")

    least_privilege_status = str(scope_review.get("least_privilege_status") or "")
    invocation_status = str(tool_invocation.get("status") or "")
    if least_privilege_status == "overbroad" and invocation_status in _CONNECTOR_REQUEST_STATES:
        drift_classes.add("scope_overbroad_but_invocation_requested")

    provider_status = str(provider_profile.get("provider_status") or "")
    risk_level = str(provider_profile.get("risk_level") or "")
    if risk_level == "critical" and readiness_status == "approved_for_lab":
        if provider_status not in {"review_required", "blocked_mvp"} or not _has_values(
            provider_profile.get("evidence_refs")
        ):
            drift_classes.add("provider_critical_but_ready")

    drill_status = str(revocation_drill.get("drill_status") or "")
    if drill_status in {"failed", "failed_closed"} and readiness_status == "approved_for_lab":
        drift_classes.add("revocation_drill_failed_but_connector_enabled")

    disable_switch_status = str(provider_profile.get("disable_switch_status") or "")
    if disable_switch_status in {"missing", "failed_closed"} and readiness_status == "approved_for_lab":
        drift_classes.add("disable_switch_missing_but_ready")

    requested_tool = tool_invocation.get("requested_tool")
    is_connector_tool = isinstance(requested_tool, dict) and (
        str(requested_tool.get("tool_type") or "") == "connector"
    )
    if is_connector_tool and invocation_status in _CONNECTOR_REQUEST_STATES:
        outbound_requested = False
        tool_scope = tool_invocation.get("tool_scope")
        if isinstance(tool_scope, dict):
            allowed_operations = tool_scope.get("allowed_operations")
            if isinstance(allowed_operations, list):
                outbound_requested = any(
                    op in {"external_send", "form_submit", "record_mutation"} for op in allowed_operations
                )
        if outbound_requested:
            has_approval = approval_binding is not None and _is_non_empty_str(
                approval_binding.get("binding_id")
            )
            has_guardian = guardian_decision is not None and _is_non_empty_str(
                guardian_decision.get("guardian_decision_id")
            )
            has_evidence = evidence_artifact is not None and _is_non_empty_str(
                evidence_artifact.get("artifact_id")
            )
            if not (has_approval and has_guardian and has_evidence):
                drift_classes.add("outbound_action_missing_approval")

    input_taint_status = str(tool_invocation.get("input_taint_status") or "")
    risk_tier = str(tool_invocation.get("risk_tier") or "")
    if input_taint_status in _TAINTED_INPUT_STATES and risk_tier in {"high", "blocked"}:
        drift_classes.add("tainted_connector_payload_used_for_tool")

    if str(connector_trust.get("revocation_status") or "") == "revoked":
        decision = str((guardian_decision or {}).get("decision") or "")
        if decision in _GUARDIAN_ALLOW_STATES:
            drift_classes.add("connector_trust_revoked_but_guardian_allow")

    evidence_refs: list[str] = []
    for payload in (
        readiness,
        scope_review,
        consent,
        revocation_drill,
        tool_invocation,
        provider_profile,
        connector_trust,
    ):
        refs = payload.get("evidence_refs")
        if isinstance(refs, list):
            evidence_refs.extend(str(ref) for ref in refs if isinstance(ref, str) and ref)
    if not evidence_refs:
        drift_classes.add("connector_evidence_missing")

    status = "reconciled"
    if "connector_cross_tenant_linkage" in drift_classes:
        status = "failed_closed"
    elif any(
        drift in drift_classes
        for drift in (
            "consent_revoked_but_readiness_approved",
            "provider_critical_but_ready",
            "revocation_drill_failed_but_connector_enabled",
            "disable_switch_missing_but_ready",
            "connector_trust_revoked_but_guardian_allow",
            "connector_evidence_missing",
        )
    ):
        status = "failed_closed"
    elif "scope_overbroad_but_invocation_requested" in drift_classes or "outbound_action_missing_approval" in drift_classes:
        status = "action_blocked"
    elif "tainted_connector_payload_used_for_tool" in drift_classes:
        status = "action_blocked"

    reason_codes = {"approved"} if status == "reconciled" else {"connector_reconciliation_drift"}
    for drift in drift_classes:
        mapped = _DRIFT_TO_REASON.get(drift)
        if mapped is not None:
            reason_codes.add(mapped)

    normalized_reason_codes = validate_reason_codes(sorted(reason_codes))
    return {
        "reconciliation_status": status,
        "drift_classes": sorted(drift_classes),
        "reason_codes": normalized_reason_codes,
        "fail_closed": status in {"failed_closed", "blocked_mvp"},
        "blocked": status in {"action_blocked", "failed_closed", "blocked_mvp"},
        "can_authorize": False,
    }
