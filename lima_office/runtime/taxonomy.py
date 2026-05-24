"""Mock-only taxonomy helpers for reason-code registry and compatibility checks."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError


TAXONOMY_VERSION = "taxonomy-reason-v1"

REASON_CODE_CATEGORIES = frozenset(
    {
        "reconciliation",
        "linkage",
        "evidence",
        "export_delete",
        "governance",
        "guardian",
        "replay",
        "approval_binding",
        "transaction",
        "health",
        "blocked_mvp",
        "tenant_isolation",
    }
)

REASON_CODE_STATUSES = frozenset({"active", "deprecated", "blocked", "reserved"})
REASON_CODE_SEVERITIES = frozenset({"info", "warning", "degraded", "blocked", "critical"})

UNKNOWN_REASON_CODE_POLICIES = frozenset({"fail_closed", "display_unknown", "blocked_mvp"})
DEPRECATED_REASON_CODE_POLICIES = frozenset({"allow_with_warning", "fail_closed", "blocked_mvp"})

REASON_CODE_REGISTRY: dict[str, dict[str, Any]] = {
    "recon_missing_guardian_decision": {
        "category": "reconciliation",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_stale_guardian_decision": {
        "category": "reconciliation",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_mismatched_approval_binding": {
        "category": "reconciliation",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_mismatched_token_verification": {
        "category": "reconciliation",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_replay_record_missing": {
        "category": "reconciliation",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_replay_record_mismatch": {
        "category": "reconciliation",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_evidence_ref_missing": {
        "category": "reconciliation",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_coordinator_event_mismatch": {
        "category": "reconciliation",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "recon_cross_tenant_linkage": {
        "category": "tenant_isolation",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "blocked_mvp_authorization_attempt": {
        "category": "blocked_mvp",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "export_delete_conflict_active": {
        "category": "export_delete",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "export_delete_preservation_hold_active": {
        "category": "export_delete",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "export_delete_retention_window_active": {
        "category": "export_delete",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "export_delete_review_required": {
        "category": "export_delete",
        "status": "deprecated",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": False,
        "fail_closed_required": False,
        "replaced_by": "export_delete_conflict_active",
        "aliases": ["export_delete_review_required_legacy"],
    },
    "export_delete_blocked_mvp": {
        "category": "export_delete",
        "status": "blocked",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "evidence_ref_missing": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "evidence_failed_closed_required": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "export_manifest_redaction_required": {
        "category": "evidence",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "blocked_mvp_export_delete_execution": {
        "category": "blocked_mvp",
        "status": "blocked",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "health_guardian_replay_denied": {
        "category": "health",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": False,
        "fail_closed_required": False,
        "aliases": [],
    },
}

CANONICAL_REASON_CODES = frozenset(REASON_CODE_REGISTRY)

ALIAS_TO_CANONICAL: dict[str, str] = {}
for _code, _meta in REASON_CODE_REGISTRY.items():
    for _alias in _meta.get("aliases", []):
        existing = ALIAS_TO_CANONICAL.get(_alias)
        if existing is not None and existing != _code:
            raise ValueError(f"duplicate alias mapping for {_alias}: {existing} vs {_code}")
        ALIAS_TO_CANONICAL[_alias] = _code

CONFLICT_DELETE_STATUSES = frozenset({"conflict_detected", "denied", "blocked_mvp"})
BLOCKING_HOLD_STATUSES = frozenset({"active", "conflict_with_delete", "blocked_mvp"})


def get_reason_code_metadata(reason_code: str, *, allow_alias: bool = True) -> dict[str, Any]:
    """Resolve registry metadata for a reason code, optionally through alias mapping."""

    if reason_code in REASON_CODE_REGISTRY:
        metadata = dict(REASON_CODE_REGISTRY[reason_code])
        metadata["canonical_reason_code"] = reason_code
        metadata["is_alias"] = False
        return metadata
    if allow_alias and reason_code in ALIAS_TO_CANONICAL:
        canonical = ALIAS_TO_CANONICAL[reason_code]
        metadata = dict(REASON_CODE_REGISTRY[canonical])
        metadata["canonical_reason_code"] = canonical
        metadata["is_alias"] = True
        metadata["input_reason_code"] = reason_code
        return metadata
    raise PolicyDenyError(f"unknown reason code(s): {reason_code}")


def validate_registry_entry_metadata(reason_code: str) -> dict[str, Any]:
    """Validate category/status/severity for a registry entry."""

    metadata = get_reason_code_metadata(reason_code, allow_alias=False)
    category = metadata.get("category")
    status = metadata.get("status")
    severity = metadata.get("severity")
    if category not in REASON_CODE_CATEGORIES:
        raise PolicyDenyError(f"invalid reason category for {reason_code}: {category}")
    if status not in REASON_CODE_STATUSES:
        raise PolicyDenyError(f"invalid reason status for {reason_code}: {status}")
    if severity not in REASON_CODE_SEVERITIES:
        raise PolicyDenyError(f"invalid reason severity for {reason_code}: {severity}")
    return metadata


def normalize_reason_code(
    reason_code: str,
    *,
    allow_deprecated: bool = True,
    unknown_reason_code_policy: str = "fail_closed",
) -> str:
    """Return canonical reason code, honoring alias mapping and policy guards."""

    if unknown_reason_code_policy not in UNKNOWN_REASON_CODE_POLICIES:
        raise PolicyDenyError(f"unknown_reason_code_policy is invalid: {unknown_reason_code_policy}")

    try:
        metadata = get_reason_code_metadata(reason_code, allow_alias=True)
    except PolicyDenyError:
        if unknown_reason_code_policy in {"fail_closed", "blocked_mvp"}:
            raise
        return reason_code

    status = metadata.get("status")
    if status == "reserved":
        raise PolicyDenyError(f"reserved reason code cannot be used: {reason_code}")
    if status == "deprecated" and not allow_deprecated:
        raise PolicyDenyError(f"deprecated reason code not allowed: {reason_code}")
    if status == "deprecated" and isinstance(metadata.get("replaced_by"), str):
        return str(metadata["replaced_by"])
    return str(metadata["canonical_reason_code"])


def validate_reason_codes(
    reason_codes: list[str],
    *,
    allow_deprecated: bool = True,
    unknown_reason_code_policy: str = "fail_closed",
) -> list[str]:
    """Validate and normalize reason codes against the canonical in-repo registry."""

    if not isinstance(reason_codes, list):
        raise PolicyDenyError("reason_codes must be a list")
    normalized = {
        normalize_reason_code(
            code,
            allow_deprecated=allow_deprecated,
            unknown_reason_code_policy=unknown_reason_code_policy,
        )
        for code in reason_codes
    }
    return sorted(normalized)


def classify_reason_code_set(
    reason_codes: list[str],
    *,
    unknown_reason_code_policy: str = "fail_closed",
    deprecated_reason_code_policy: str = "allow_with_warning",
    compatibility_status: str = "compatible",
) -> dict[str, Any]:
    """Classify reason-code set for fail-closed metadata posture."""

    if unknown_reason_code_policy not in UNKNOWN_REASON_CODE_POLICIES:
        raise PolicyDenyError(f"unknown_reason_code_policy is invalid: {unknown_reason_code_policy}")
    if deprecated_reason_code_policy not in DEPRECATED_REASON_CODE_POLICIES:
        raise PolicyDenyError(
            f"deprecated_reason_code_policy is invalid: {deprecated_reason_code_policy}"
        )

    try:
        normalized = validate_reason_codes(
            reason_codes,
            allow_deprecated=True,
            unknown_reason_code_policy=unknown_reason_code_policy,
        )
    except PolicyDenyError:
        return {
            "raw_reason_codes": sorted(set(reason_codes)),
            "reason_codes": [],
            "deprecated_present": False,
            "fail_closed": True,
            "blocked": True,
            "can_authorize": False,
        }

    deprecated_present = False
    blocked_or_critical_present = False
    fail_closed_required = compatibility_status in {"breaking_change", "blocked_mvp"}
    for code in normalized:
        metadata = validate_registry_entry_metadata(code)
        if metadata["status"] == "deprecated":
            deprecated_present = True
        if metadata["status"] == "blocked" or metadata["severity"] in {"blocked", "critical"}:
            blocked_or_critical_present = True
        if metadata.get("fail_closed_required"):
            fail_closed_required = True

    if compatibility_status in {"breaking_change", "blocked_mvp"}:
        return {
            "raw_reason_codes": sorted(set(reason_codes)),
            "reason_codes": normalized,
            "deprecated_present": deprecated_present,
            "fail_closed": True,
            "blocked": True,
            "can_authorize": False,
        }

    if deprecated_present and deprecated_reason_code_policy in {"fail_closed", "blocked_mvp"}:
        return {
            "raw_reason_codes": sorted(set(reason_codes)),
            "reason_codes": normalized,
            "deprecated_present": True,
            "fail_closed": True,
            "blocked": True,
            "can_authorize": False,
        }

    return {
        "raw_reason_codes": sorted(set(reason_codes)),
        "reason_codes": normalized,
        "deprecated_present": deprecated_present,
        "fail_closed": fail_closed_required or blocked_or_critical_present,
        "blocked": blocked_or_critical_present,
        "can_authorize": False,
    }


def classify_export_delete_conflict(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify export/delete conflict metadata in memory only."""

    reason_codes = payload.get("reason_codes") or []
    normalized_reasons = validate_reason_codes(reason_codes)
    reason_classification = classify_reason_code_set(
        normalized_reasons,
        unknown_reason_code_policy=str(payload.get("unknown_reason_code_policy") or "fail_closed"),
        deprecated_reason_code_policy=str(
            payload.get("deprecated_reason_code_policy") or "allow_with_warning"
        ),
        compatibility_status=str(payload.get("compatibility_status") or "compatible"),
    )

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
        "raw_reason_codes": sorted(set(reason_codes)),
        "reason_codes": normalized_reasons,
        "delete_blocked_by_hold": preservation_hold_status in BLOCKING_HOLD_STATUSES,
        "conflict_detected": delete_review_status in CONFLICT_DELETE_STATUSES,
        "export_denied_or_blocked": export_review_status in {"denied", "failed_closed", "blocked_mvp"},
        "reason_fail_closed": bool(reason_classification["fail_closed"]),
        "deprecated_reason_present": bool(reason_classification["deprecated_present"]),
        "can_authorize": False,
    }
