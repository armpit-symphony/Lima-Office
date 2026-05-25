"""Mock-only taxonomy helpers for reason-code registry and compatibility checks."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.errors import PolicyDenyError


TAXONOMY_VERSION = "taxonomy-reason-v1"
SUPPORTED_TAXONOMY_VERSIONS = frozenset(
    {
        "taxonomy-reason-v1",
        "taxonomy-reason-v2",
        "taxonomy-reason-v3",
        "taxonomy-recon-v1",
    }
)

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

CONTRACT_FAMILIES = frozenset(
    {
        "approval",
        "guardian",
        "replay",
        "reconciliation",
        "linkage",
        "evidence",
        "export_delete",
        "governance",
        "transaction",
        "health",
        "console",
        "supervisor",
        "worker",
        "blocked_mvp",
        "tenant_isolation",
    }
)

CONTRACT_FAMILY_BY_SCHEMA_KEY: dict[str, str] = {
    "approval.binding": "approval",
    "approval.chain": "approval",
    "approval.result": "approval",
    "token.verification": "approval",
    "guardian.decision": "guardian",
    "guardian.replay": "replay",
    "replay.store.record": "replay",
    "evidence.artifact": "evidence",
    "evidence.failure": "evidence",
    "evidence.ledger.entry": "evidence",
    "evidence.export_manifest": "export_delete",
    "governance.audit_export": "export_delete",
    "governance.export_delete_review": "governance",
    "governance.breakglass": "governance",
    "transaction.boundary": "transaction",
    "transaction.coordinator.event": "transaction",
    "console.alert": "console",
    "console.view": "console",
    "supervisor.health": "supervisor",
    "worker.lifecycle": "worker",
    "task.execution": "linkage",
    "tool.invocation": "linkage",
    "memory.access": "linkage",
    "lima_it.handoff": "governance",
    "reason.code.registry": "governance",
    "reason.code.compatibility": "governance",
}

CONTRACT_FAMILY_ALLOWED_CATEGORIES: dict[str, frozenset[str]] = {
    "approval": frozenset(
        {
            "approval_binding",
            "guardian",
            "replay",
            "linkage",
            "evidence",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "guardian": frozenset(
        {
            "guardian",
            "replay",
            "linkage",
            "approval_binding",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "replay": frozenset(
        {
            "replay",
            "guardian",
            "linkage",
            "approval_binding",
            "transaction",
            "evidence",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "reconciliation": frozenset(
        {
            "reconciliation",
            "linkage",
            "evidence",
            "guardian",
            "replay",
            "approval_binding",
            "transaction",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "linkage": frozenset(
        {
            "linkage",
            "reconciliation",
            "approval_binding",
            "guardian",
            "replay",
            "evidence",
            "governance",
            "health",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "evidence": frozenset(
        {
            "evidence",
            "linkage",
            "reconciliation",
            "replay",
            "transaction",
            "export_delete",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "export_delete": frozenset(
        {
            "export_delete",
            "evidence",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "governance": frozenset(
        {
            "governance",
            "export_delete",
            "evidence",
            "reconciliation",
            "linkage",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "transaction": frozenset(
        {
            "transaction",
            "linkage",
            "reconciliation",
            "evidence",
            "replay",
            "approval_binding",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "health": frozenset(
        {
            "health",
            "evidence",
            "guardian",
            "approval_binding",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "console": frozenset(
        {
            "health",
            "evidence",
            "governance",
            "export_delete",
            "reconciliation",
            "linkage",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "supervisor": frozenset(
        {
            "health",
            "evidence",
            "guardian",
            "approval_binding",
            "reconciliation",
            "linkage",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "worker": frozenset(
        {
            "health",
            "evidence",
            "governance",
            "guardian",
            "linkage",
            "blocked_mvp",
            "tenant_isolation",
        }
    ),
    "blocked_mvp": frozenset({"blocked_mvp"}),
    "tenant_isolation": frozenset({"tenant_isolation"}),
}

# Cross-family allowances are explicit and metadata-only.
CONTRACT_FAMILY_CROSS_CATEGORY_EXCEPTIONS: dict[str, frozenset[str]] = {
    family: frozenset({"blocked_mvp", "tenant_isolation"})
    for family in CONTRACT_FAMILIES
    if family not in {"blocked_mvp", "tenant_isolation"}
}

CONTRACT_FAMILY_TO_TAXONOMY_FAMILY: dict[str, str] = {
    "approval": "recon",
    "guardian": "recon",
    "replay": "recon",
    "reconciliation": "recon",
    "linkage": "recon",
    "evidence": "recon",
    "export_delete": "recon",
    "governance": "recon",
    "transaction": "recon",
    "health": "recon",
    "console": "recon",
    "supervisor": "recon",
    "worker": "recon",
    "blocked_mvp": "recon",
    "tenant_isolation": "recon",
}

SCHEMA_KEY_TO_TAXONOMY_FAMILY: dict[str, str] = {
    "reason.code.registry": "reason",
    "reason.code.compatibility": "reason",
}

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
    "evidence_raw_content_blocked": {
        "category": "evidence",
        "status": "blocked",
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
    "worker_stale": {
        "category": "health",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": False,
        "fail_closed_required": False,
        "aliases": [],
    },
    "worker_quarantined": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "worker_revoked": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "evidence_writer_degraded": {
        "category": "health",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": False,
        "aliases": [],
    },
    "guardian_denied": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_expired": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_revoked": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "token_mismatch": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "connector_revoked": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "attestation_failed": {
        "category": "health",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "update_rollback_required": {
        "category": "health",
        "status": "active",
        "severity": "degraded",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": False,
        "aliases": [],
    },
    "lima_it_remediation_blocked": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "retention_policy_missing": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "export_delete_policy_missing": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "idp_mfa_missing": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "task_blocked": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "tenant_mismatch": {
        "category": "tenant_isolation",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "customer_context_mismatch": {
        "category": "tenant_isolation",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "task_mismatch": {
        "category": "linkage",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "worker_mismatch": {
        "category": "linkage",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "action_type_mismatch": {
        "category": "linkage",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "tool_scope_mismatch": {
        "category": "linkage",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "resource_scope_widened": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "operation_scope_widened": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "guardian_decision_mismatch": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_request_mismatch": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_result_mismatch": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_token_mismatch": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "token_verification_mismatch": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "nonce_replayed": {
        "category": "replay",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "token_expired": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "token_revoked": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "blocked_mvp": {
        "category": "blocked_mvp",
        "status": "blocked",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "tainted_input": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "missing_evidence": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": ["evidence_missing"],
    },
    "identity_provider_outage": {
        "category": "governance",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": False,
        "aliases": [],
    },
    "security_containment": {
        "category": "governance",
        "status": "active",
        "severity": "warning",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": False,
        "aliases": [],
    },
    "evidence_preservation": {
        "category": "governance",
        "status": "active",
        "severity": "warning",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": False,
        "aliases": [],
    },
    "worker_revoke": {
        "category": "governance",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": False,
        "aliases": [],
    },
    "decision_scope_hash_mismatch": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_binding_mismatch": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "decision_expired": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "decision_stale": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "decision_revoked": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "missing_expiry": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "ambiguous_timestamp": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "nonce_replay_denied": {
        "category": "replay",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "blocked_action_class_file_delete": {
        "category": "blocked_mvp",
        "status": "blocked",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "delete_export_conflict_active": {
        "category": "export_delete",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "export_manifest_conflict_evidence_required": {
        "category": "export_delete",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "rollback_after_partial_commit": {
        "category": "transaction",
        "status": "active",
        "severity": "degraded",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "replay_store_unavailable": {
        "category": "replay",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "nonce_already_consumed": {
        "category": "replay",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "token_atomicity_ambiguous": {
        "category": "transaction",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "failed_closed_terminal_state": {
        "category": "transaction",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "evidence_writer_failure": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "ledger_unavailable": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approved": {
        "category": "approval_binding",
        "status": "active",
        "severity": "info",
        "visibility": "operator_visible",
        "evidence_required": False,
        "fail_closed_required": False,
        "aliases": [],
    },
    "denied_by_approver": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "expired": {
        "category": "approval_binding",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "cancelled": {
        "category": "approval_binding",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "superseded": {
        "category": "approval_binding",
        "status": "active",
        "severity": "warning",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "partial_scope_requires_new_request": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_missing": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "approval_denied": {
        "category": "approval_binding",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "sensitive_access_denied": {
        "category": "governance",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "evidence_unavailable": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "evidence_writer_unavailable": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "scope_mismatch": {
        "category": "linkage",
        "status": "active",
        "severity": "blocked",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "identity_verification_failed": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "capability_mismatch": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "heartbeat_missed": {
        "category": "health",
        "status": "active",
        "severity": "degraded",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": False,
        "aliases": [],
    },
    "suspicious_tool_request": {
        "category": "guardian",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "prompt_injection_suspected": {
        "category": "guardian",
        "status": "active",
        "severity": "critical",
        "visibility": "auditor_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "evidence_writer_failed": {
        "category": "evidence",
        "status": "active",
        "severity": "critical",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "operator_containment": {
        "category": "governance",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
        "aliases": [],
    },
    "update_verification_failed": {
        "category": "health",
        "status": "active",
        "severity": "blocked",
        "visibility": "operator_visible",
        "evidence_required": True,
        "fail_closed_required": True,
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


def normalize_contract_family(contract_family: str) -> str:
    """Validate and normalize contract family identifiers."""

    if not isinstance(contract_family, str) or not contract_family:
        raise PolicyDenyError("contract_family must be a non-empty string")
    if contract_family not in CONTRACT_FAMILIES:
        raise PolicyDenyError(f"unsupported contract family: {contract_family}")
    return contract_family


def get_contract_family_for_schema_key(schema_key: str) -> str | None:
    """Resolve contract family by schema key or contract-name-like identifier."""

    if not isinstance(schema_key, str) or not schema_key:
        return None
    if schema_key in CONTRACT_FAMILY_BY_SCHEMA_KEY:
        return CONTRACT_FAMILY_BY_SCHEMA_KEY[schema_key]

    prefix = schema_key.split(".", 1)[0]
    if prefix == "approval":
        return "approval"
    if prefix == "guardian":
        return "guardian"
    if prefix == "replay":
        return "replay"
    if prefix == "evidence":
        return "evidence"
    if prefix == "governance":
        return "governance"
    if prefix == "transaction":
        return "transaction"
    if prefix == "console":
        return "console"
    if prefix == "supervisor":
        return "supervisor"
    if prefix == "worker":
        return "worker"
    return None


def expected_taxonomy_family_for_schema_key(schema_key: str) -> str | None:
    """Resolve expected taxonomy version family for a schema key."""

    if not isinstance(schema_key, str) or not schema_key:
        return None
    if schema_key in SCHEMA_KEY_TO_TAXONOMY_FAMILY:
        return SCHEMA_KEY_TO_TAXONOMY_FAMILY[schema_key]
    family = get_contract_family_for_schema_key(schema_key)
    if family is None:
        return None
    return CONTRACT_FAMILY_TO_TAXONOMY_FAMILY.get(family)


def _taxonomy_family_from_version(version: str) -> str:
    if version.startswith("taxonomy-recon-"):
        return "recon"
    if version.startswith("taxonomy-reason-"):
        return "reason"
    return "unknown"


def validate_taxonomy_version(version: str, *, expected_family: str | None = None) -> str:
    """Validate taxonomy_version against supported in-repo versions."""

    if not isinstance(version, str) or not version:
        raise PolicyDenyError("taxonomy_version must be a non-empty string")
    if version not in SUPPORTED_TAXONOMY_VERSIONS:
        raise PolicyDenyError(f"unsupported taxonomy_version: {version}")
    if expected_family is not None:
        if expected_family not in {"reason", "recon"}:
            raise PolicyDenyError(f"unsupported taxonomy family expectation: {expected_family}")
        actual_family = _taxonomy_family_from_version(version)
        if actual_family != expected_family:
            raise PolicyDenyError(
                f"taxonomy_version family mismatch: expected {expected_family}, found {actual_family}"
            )
    return version


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


def validate_reason_code_for_family(
    reason_code: str,
    contract_family: str,
    *,
    allow_alias: bool = True,
) -> dict[str, Any]:
    """Validate reason-code category against contract-family constraints."""

    family = normalize_contract_family(contract_family)
    metadata = get_reason_code_metadata(reason_code, allow_alias=allow_alias)
    canonical = str(metadata["canonical_reason_code"])
    canonical_meta = validate_registry_entry_metadata(canonical)
    category = str(canonical_meta["category"])

    allowed_categories = set(CONTRACT_FAMILY_ALLOWED_CATEGORIES[family])
    allowed_categories.update(CONTRACT_FAMILY_CROSS_CATEGORY_EXCEPTIONS.get(family, frozenset()))
    if category not in allowed_categories:
        raise PolicyDenyError(
            f"wrong-family reason code: {canonical} ({category}) is not allowed for {family}"
        )

    result = dict(canonical_meta)
    result["canonical_reason_code"] = canonical
    result["contract_family"] = family
    result["category_allowed_for_family"] = True
    return result


def classify_family_reason_codes(
    reason_codes: list[str],
    *,
    contract_family: str,
    allow_deprecated: bool = True,
    unknown_reason_code_policy: str = "fail_closed",
) -> dict[str, Any]:
    """Classify reason codes against contract-family constraints (metadata only)."""

    if not isinstance(reason_codes, list):
        raise PolicyDenyError("reason_codes must be a list")

    family = normalize_contract_family(contract_family)
    raw_codes = sorted({code for code in reason_codes if isinstance(code, str)})
    normalized = validate_reason_codes(
        raw_codes,
        allow_deprecated=allow_deprecated,
        unknown_reason_code_policy=unknown_reason_code_policy,
    )
    wrong_family: list[str] = []
    for code in normalized:
        try:
            validate_reason_code_for_family(code, family, allow_alias=False)
        except PolicyDenyError:
            wrong_family.append(code)

    return {
        "contract_family": family,
        "raw_reason_codes": raw_codes,
        "reason_codes": normalized,
        "wrong_family_reason_codes": sorted(wrong_family),
        "fail_closed": bool(wrong_family),
        "blocked": bool(wrong_family),
        "can_authorize": False,
    }


def runtime_registry_snapshot() -> dict[str, dict[str, Any]]:
    """Return normalized runtime reason-code metadata for parity checks."""

    snapshot: dict[str, dict[str, Any]] = {}
    for code in sorted(REASON_CODE_REGISTRY):
        meta = REASON_CODE_REGISTRY[code]
        snapshot[code] = {
            "category": meta.get("category"),
            "status": meta.get("status"),
            "severity": meta.get("severity"),
            "evidence_required": bool(meta.get("evidence_required")),
            "fail_closed_required": bool(meta.get("fail_closed_required")),
            "replaced_by": meta.get("replaced_by"),
            "aliases": sorted(meta.get("aliases", [])),
        }
    return snapshot


def detect_registry_runtime_parity(
    registry_rows: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Detect drift between provided registry rows and runtime registry."""

    if not isinstance(registry_rows, dict):
        raise PolicyDenyError("registry_rows must be a dict keyed by reason_code")

    runtime_rows = runtime_registry_snapshot()
    registry_codes = set(registry_rows)
    runtime_codes = set(runtime_rows)

    missing_in_runtime = sorted(registry_codes - runtime_codes)
    missing_in_registry = sorted(runtime_codes - registry_codes)

    mismatched: list[str] = []
    for code in sorted(registry_codes & runtime_codes):
        provided = registry_rows[code]
        runtime = runtime_rows[code]
        provided_aliases = sorted(
            [alias for alias in provided.get("aliases", []) if isinstance(alias, str)]
        )
        if (
            provided.get("category") != runtime.get("category")
            or provided.get("status") != runtime.get("status")
            or provided.get("severity") != runtime.get("severity")
            or bool(provided.get("evidence_required")) != bool(runtime.get("evidence_required"))
            or bool(provided.get("fail_closed_required"))
            != bool(runtime.get("fail_closed_required"))
            or provided.get("replaced_by") != runtime.get("replaced_by")
            or provided_aliases != runtime.get("aliases")
        ):
            mismatched.append(code)

    return {
        "missing_in_runtime": missing_in_runtime,
        "missing_in_registry": missing_in_registry,
        "metadata_mismatches": mismatched,
    }


def list_registry_runtime_drift(parity_report: dict[str, Any]) -> list[str]:
    """Return deterministic human-readable drift lines."""

    lines: list[str] = []
    for code in parity_report.get("missing_in_runtime", []):
        lines.append(f"missing_in_runtime:{code}")
    for code in parity_report.get("missing_in_registry", []):
        lines.append(f"missing_in_registry:{code}")
    for code in parity_report.get("metadata_mismatches", []):
        lines.append(f"metadata_mismatch:{code}")
    return sorted(lines)


def validate_registry_runtime_parity(registry_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Fail closed when runtime and registry rows drift."""

    report = detect_registry_runtime_parity(registry_rows)
    if report["missing_in_runtime"] or report["missing_in_registry"] or report["metadata_mismatches"]:
        raise PolicyDenyError(
            "registry/runtime parity mismatch: " + ", ".join(list_registry_runtime_drift(report))
        )
    return report


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
