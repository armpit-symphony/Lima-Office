"""Guardian decision payload helpers for mock runtime flows."""

from __future__ import annotations

from typing import Any


FIXED_CREATED_AT = "2026-05-20T00:00:00Z"
FIXED_EXPIRES_AT = "2026-05-20T00:05:00Z"

ACTION_CLASS_MAP = {
    "connector_live_access": "connector_access",
    "cross_tenant_access": "memory_access",
    "external_send": "outbound_message",
    "external_message_send": "outbound_message",
    "file_delete": "file_delete",
    "internal_note": "tool_invocation",
    "missing_approval_token": "privileged_operation",
    "mock_diagnostic": "lima_it_diagnostic",
    "read_only_diagnostic": "lima_it_diagnostic",
    "remediation": "lima_it_remediation",
    "tainted_input_privileged_action": "privileged_operation",
    "unrestricted_tool": "tool_invocation",
}


def normalize_action_class(action: str, context: dict[str, Any] | None = None) -> str:
    context = context or {}
    explicit = context.get("schema_action_class")
    if isinstance(explicit, str):
        return explicit
    return ACTION_CLASS_MAP.get(action, "privileged_operation")


def build_guardian_decision(
    *,
    action: str,
    decision: str,
    tenant_id: str = "tenant-lab-001",
    customer_context_id: str = "customer-context-main",
    reason: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Guardian-decision-shaped mock payload.

    The payload is intentionally deterministic for tests and evidence linking.
    It represents policy metadata only; it does not execute an action.
    """

    context = context or {}
    action_class = normalize_action_class(action, context)
    safe_action = action.replace("_", "-") or "unknown"
    decision_id = context.get("decision_id", f"gd-{safe_action}-{decision}")
    evidence_id = context.get("evidence_artifact_id", f"ev-{safe_action}-{decision}")
    denied = decision in {"deny", "block_mvp", "quarantine_subject"}

    return {
        "contract_name": "guardian.decision",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "customer_context_id": customer_context_id,
        "environment": "blocked_mvp" if denied else "phase0_lab",
        "correlation_id": context.get("correlation_id", f"corr-{safe_action}"),
        "causation_id": context.get("causation_id"),
        "idempotency_key": context.get("idempotency_key", f"idem-{safe_action}-{decision}"),
        "decision_id": decision_id,
        "request_id": context.get("request_id", f"req-{safe_action}"),
        "producer": {
            "component": "guardian",
            "produced_at": context.get("produced_at", FIXED_CREATED_AT),
        },
        "requested_by": context.get(
            "requested_by",
            {"actor_type": "supervisor", "actor_id": "supervisor-lab-001"},
        ),
        "subject": context.get("subject", {"subject_type": "task", "subject_id": f"subject-{safe_action}"}),
        "action_class": action_class,
        "resource_ref": context.get(
            "resource_ref",
            {"resource_type": "unknown", "resource_id": f"resource-{safe_action}", "resource_scope": "task_scoped"},
        ),
        "data_classification": context.get("data_classification", "internal"),
        "risk_tier": "blocked" if denied else context.get("risk_tier", "low"),
        "policy_refs": context.get("policy_refs", [f"phase1a-mock:{action}"]),
        "policy_version": context.get("policy_version", "policy-phase1a-mock-v1"),
        "policy_snapshot_hash": context.get("policy_snapshot_hash", "hash-ref-phase1a-policy"),
        "valid_for_action_ref": context.get("valid_for_action_ref", f"action-ref-{safe_action}"),
        "decision": decision,
        "approval_required": decision == "requires_approval",
        "approval_request_id": context.get("approval_request_id") if decision == "requires_approval" else None,
        "approval_token_id": None,
        "denial_reason": reason if denied else None,
        "redaction_level": context.get("redaction_level", "metadata_only"),
        "evidence_required": True,
        "evidence_artifact_id": evidence_id,
        "evidence_artifact_ids": [evidence_id],
        "prompt_injection": context.get(
            "prompt_injection",
            {
                "untrusted_input_refs": [],
                "content_origin": "operator",
                "instruction_boundary": "operator_instruction",
                "injection_suspected": False,
                "injection_signals": [],
                "containment_action": "none",
            },
        ),
        "created_at": context.get("created_at", FIXED_CREATED_AT),
        "expires_at": context.get("expires_at", FIXED_EXPIRES_AT),
    }
