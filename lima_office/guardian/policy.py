"""Default-deny Guardian policy stub for Phase 1A mock runtime."""

from __future__ import annotations

from typing import Any

from .decision import build_guardian_decision


DENIED_ACTIONS = {
    "connector_live_access": "Live connector access is blocked in Phase 1A.",
    "cross_tenant_access": "Cross-tenant access is blocked.",
    "external_send": "External sends are blocked in Phase 1A.",
    "external_message_send": "External sends are blocked in Phase 1A.",
    "file_delete": "File delete is blocked by default.",
    "missing_approval_token": "Approval-required action is missing a valid token verification.",
    "remediation": "Remediation execution is blocked in Phase 1A.",
    "tainted_input_privileged_action": "Tainted input cannot authorize privileged action.",
    "unrestricted_tool": "Unrestricted tool execution is blocked.",
}

ALLOWED_MOCK_ACTIONS = {
    "internal_note",
    "mock_diagnostic",
    "read_only_diagnostic",
}

BAD_TOKEN_STATES = {"expired", "revoked", "used", "replayed", "missing", "mismatched", "wrong_scope", "ambiguous"}
BLOCKED_SCHEMA_ACTION_CLASSES = {
    "connector_access",
    "file_delete",
    "file_write",
    "lima_it_remediation",
    "network_access",
    "outbound_message",
    "privileged_operation",
    "scheduled_action",
}


class GuardianPolicy:
    """Small policy stub that returns Guardian-decision-shaped metadata."""

    def decide(self, action: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        action = action or "unknown"

        denial_reason = self._deny_reason(action, context)
        if denial_reason is not None:
            return build_guardian_decision(
                action=action,
                decision="deny",
                reason=denial_reason,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )

        if action in ALLOWED_MOCK_ACTIONS and self._is_mock_read_only_context(context):
            return build_guardian_decision(
                action=action,
                decision="allow_with_evidence",
                reason=None,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )

        return build_guardian_decision(
            action=action,
            decision="deny",
            reason="No explicit allow rule matched; policy fails closed.",
            tenant_id=context.get("tenant_id", "tenant-lab-001"),
            customer_context_id=context.get("customer_context_id", "customer-context-main"),
            context=context,
        )

    def require_allowed(self, action: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        decision = self.decide(action, context)
        if decision["decision"] not in {"allow", "allow_with_evidence"}:
            from lima_office.runtime.errors import PolicyDenyError

            raise PolicyDenyError(decision["denial_reason"] or "Guardian policy denied the action")
        return decision

    def _deny_reason(self, action: str, context: dict[str, Any]) -> str | None:
        schema_action_class = context.get("schema_action_class")
        if schema_action_class in BLOCKED_SCHEMA_ACTION_CLASSES:
            return f"Schema action class {schema_action_class} is blocked in Phase 1A."
        if action in DENIED_ACTIONS:
            return DENIED_ACTIONS[action]
        if context.get("connector_live_access") or context.get("live_connector_enabled"):
            return DENIED_ACTIONS["connector_live_access"]
        if context.get("cross_tenant_access"):
            return DENIED_ACTIONS["cross_tenant_access"]
        if context.get("tainted_input_privileged_action"):
            return DENIED_ACTIONS["tainted_input_privileged_action"]
        if context.get("unrestricted_tool"):
            return DENIED_ACTIONS["unrestricted_tool"]
        if context.get("evidence_required") and not context.get("evidence_artifact_ids"):
            return "Evidence-required action has no evidence reference."
        if context.get("approval_required") and not self._token_verification_allows(context):
            return DENIED_ACTIONS["missing_approval_token"]
        return None

    @staticmethod
    def _is_mock_read_only_context(context: dict[str, Any]) -> bool:
        if not context.get("tenant_id") or not context.get("customer_context_id"):
            return False
        mode = context.get("execution_mode")
        if mode not in {"plan_only", "read_only", "draft_only", "mock_only"}:
            return False
        if context.get("external_effect") not in {"none", "draft_only"}:
            return False
        if context.get("evidence_required") is False:
            return False
        return not any(
            context.get(flag)
            for flag in (
                "connector_live_access",
                "cross_tenant_access",
                "tainted_input_privileged_action",
                "unrestricted_tool",
            )
        )

    @staticmethod
    def _token_verification_allows(context: dict[str, Any]) -> bool:
        verification = context.get("token_verification")
        if not isinstance(verification, dict):
            return False
        if verification.get("verification_result") != "valid":
            return False
        if verification.get("can_proceed") is not True:
            return False
        observed = verification.get("token_status_observed")
        return isinstance(observed, str) and observed not in BAD_TOKEN_STATES
