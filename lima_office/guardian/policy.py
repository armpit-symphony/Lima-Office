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
    "lab_support",
    "internal_note",
    "mock_diagnostic",
    "mock_form_submission",
    "read_only_diagnostic",
}
ALLOWED_ATTENDED_LAB_ACTIONS = {
    "helper_synthetic_review",
    "model_subscription_readonly",
    "office_task_proposal_manage",
    "office_approval_preview_manage",
    "operator_session_bind",
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
        if action in ALLOWED_ATTENDED_LAB_ACTIONS and self._is_attended_model_context(context):
            return build_guardian_decision(
                action=action,
                decision="allow_with_evidence",
                reason=None,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )
        if action == "helper_synthetic_review" and self._is_attended_helper_context(context):
            return build_guardian_decision(
                action=action,
                decision="allow_with_evidence",
                reason=None,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )
        if action == "office_task_proposal_manage" and self._is_attended_proposal_context(context):
            return build_guardian_decision(
                action=action,
                decision="allow_with_evidence",
                reason=None,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )
        if action == "office_approval_preview_manage" and self._is_attended_approval_preview_context(context):
            return build_guardian_decision(
                action=action,
                decision="allow_with_evidence",
                reason=None,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )
        if action == "operator_session_bind" and self._is_attended_operator_session_context(context):
            return build_guardian_decision(
                action=action, decision="allow_with_evidence", reason=None,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )
        if action == "office_pending_approval_request_create" and self._is_pending_approval_request_context(context):
            return build_guardian_decision(
                action=action, decision="requires_approval", reason=None,
                tenant_id=context.get("tenant_id", "tenant-lab-001"),
                customer_context_id=context.get("customer_context_id", "customer-context-main"),
                context=context,
            )
        if (action == "office_non_authorizing_approval_decision"
                and self._is_non_authorizing_approval_decision_context(context)):
            return build_guardian_decision(
                action=action, decision="allow_with_evidence", reason=None,
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
        if action == "model_subscription_readonly":
            if not self._is_attended_model_context(context):
                return "Read-only subscription model use did not satisfy the attended lab policy."
        if action == "helper_synthetic_review":
            if not self._is_attended_helper_context(context):
                return "Office helper review did not satisfy the synthetic attended lab policy."
        if action == "office_task_proposal_manage":
            if not self._is_attended_proposal_context(context):
                return "Task proposal change did not satisfy the synthetic attended lab policy."
        if action == "office_approval_preview_manage":
            if not self._is_attended_approval_preview_context(context):
                return "Approval preview change did not satisfy the tokenless attended lab policy."
        if action == "operator_session_bind":
            if not self._is_attended_operator_session_context(context):
                return "Operator session binding did not satisfy the attended localhost lab policy."
        if action == "office_pending_approval_request_create":
            if not self._is_pending_approval_request_context(context):
                return "Pending approval request did not satisfy the attended request-only policy."
        if action == "office_non_authorizing_approval_decision":
            if not self._is_non_authorizing_approval_decision_context(context):
                return "Approval decision did not satisfy the non-authorizing lab policy."
        if action == "lab_support":
            if context.get("scope") != "synthetic_registration_history" or context.get("preserve_sops") is not True:
                return "Lab support requires a bounded scope and preserved SOPs."
            operation = context.get("operation")
            if operation not in {"diagnostic_export", "synthetic_history_reset", "service_stop"}:
                return "Unknown lab support operation."
            if operation == "synthetic_history_reset" and context.get("confirmed") is not True:
                return "Synthetic history reset requires explicit confirmation."
        schema_action_class = context.get("schema_action_class")
        if schema_action_class in BLOCKED_SCHEMA_ACTION_CLASSES:
            return f"Schema action class {schema_action_class} is blocked in Phase 1A."
        if action == "mock_form_submission":
            if context.get("synthetic_data_only") is not True:
                return "Mock form submission requires fixed synthetic data."
            if context.get("operator_review_decision") != "approved":
                return "Mock form submission requires explicit human approval."
            if context.get("unresolved_issue_count") != 0:
                return "Mock form submission has unresolved fields."
            if context.get("mock_target") != "localhost_test_range":
                return "Mock form submission target is outside the localhost test range."
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
        if (
            action != "office_pending_approval_request_create"
            and context.get("approval_required")
            and not self._token_verification_allows(context)
        ):
            return DENIED_ACTIONS["missing_approval_token"]
        return None

    @staticmethod
    def _is_attended_operator_session_context(context: dict[str, Any]) -> bool:
        return all((
            bool(context.get("tenant_id")), bool(context.get("customer_context_id")),
            context.get("execution_mode") == "identity_metadata_only",
            context.get("external_effect") == "none", context.get("evidence_required") is True,
            bool(context.get("evidence_artifact_ids")), context.get("attended") is True,
            context.get("operator_confirmation") is True,
            context.get("local_loopback_only") is True, context.get("process_bound") is True,
            context.get("raw_os_username_stored") is False,
            context.get("credentials_collected") is False,
            context.get("production_identity_verified") is False,
            context.get("approval_authority") is False,
            context.get("approval_result_allowed") is False,
            context.get("approval_token_access_allowed") is False,
            context.get("arc_dispatch_allowed") is False,
            context.get("connector_access_allowed") is False,
            context.get("submission_allowed") is False,
            context.get("approval_required") is False,
        ))

    @staticmethod
    def _is_non_authorizing_approval_decision_context(context: dict[str, Any]) -> bool:
        operation = context.get("operation")
        session_ok = (
            operation in {"deny", "cancel"}
            and context.get("attended") is True
            and context.get("operator_session_active") is True
            and bool(context.get("operator_session_binding_id"))
            and context.get("request_expired") is False
        ) or (
            operation == "expire"
            and context.get("attended") is False
            and context.get("operator_session_active") is False
            and context.get("operator_session_binding_id") is None
            and context.get("request_expired") is True
        )
        return all((
            bool(context.get("tenant_id")), bool(context.get("customer_context_id")),
            bool(context.get("approval_request_id")),
            context.get("execution_mode") == "decision_metadata_only",
            context.get("external_effect") == "none",
            context.get("evidence_required") is True,
            bool(context.get("evidence_artifact_ids")),
            context.get("operator_confirmation") is True,
            context.get("fresh_intent") is True,
            operation in {"deny", "cancel", "expire"},
            context.get("result") in {"denied", "cancelled", "expired"},
            context.get("non_authorizing") is True,
            context.get("request_pending") is True,
            context.get("synthetic_data_only") is True,
            context.get("approval_result_created") is True,
            context.get("approval_token_access_allowed") is False,
            context.get("approval_binding_allowed") is False,
            context.get("token_verification_allowed") is False,
            context.get("replay_record_allowed") is False,
            context.get("model_call_allowed") is False,
            context.get("tool_execution_allowed") is False,
            context.get("arc_dispatch_allowed") is False,
            context.get("connector_access_allowed") is False,
            context.get("submission_allowed") is False,
            context.get("external_side_effects") is False,
            context.get("approval_required") is False,
            session_ok,
            not context.get("connector_live_access"),
            not context.get("cross_tenant_access"),
            not context.get("unrestricted_tool"),
        ))

    @staticmethod
    def _is_pending_approval_request_context(context: dict[str, Any]) -> bool:
        return all((
            bool(context.get("tenant_id")), bool(context.get("customer_context_id")),
            bool(context.get("approval_request_id")),
            context.get("execution_mode") == "request_metadata_only",
            context.get("external_effect") == "none", context.get("evidence_required") is True,
            bool(context.get("evidence_artifact_ids")), context.get("attended") is True,
            context.get("operator_confirmation") is True,
            context.get("operator_session_active") is True,
            bool(context.get("operator_session_binding_id")),
            context.get("production_identity_verified") is False,
            context.get("fresh_intent") is True,
            context.get("preview_reviewed_no_authority") is True,
            context.get("source_current") is True,
            context.get("synthetic_data_only") is True,
            context.get("free_form_content_allowed") is False,
            context.get("request_only") is True,
            context.get("approval_result_allowed") is False,
            context.get("approval_token_access_allowed") is False,
            context.get("approval_binding_allowed") is False,
            context.get("token_verification_allowed") is False,
            context.get("replay_record_allowed") is False,
            context.get("model_call_allowed") is False,
            context.get("tool_execution_allowed") is False,
            context.get("arc_dispatch_allowed") is False,
            context.get("connector_access_allowed") is False,
            context.get("submission_allowed") is False,
            context.get("external_side_effects") is False,
            context.get("approval_required") is True,
            not context.get("connector_live_access"), not context.get("cross_tenant_access"),
            not context.get("unrestricted_tool"),
        ))

    @staticmethod
    def _is_attended_approval_preview_context(context: dict[str, Any]) -> bool:
        return all(
            (
                bool(context.get("tenant_id")),
                bool(context.get("customer_context_id")),
                context.get("execution_mode") == "plan_only",
                context.get("external_effect") == "none",
                context.get("evidence_required") is True,
                bool(context.get("evidence_artifact_ids")),
                context.get("attended") is True,
                context.get("operator_confirmation") is True,
                context.get("operation") in {"create", "review", "deny", "withdraw"},
                context.get("data_classification") == "synthetic_fixture_only",
                context.get("synthetic_data_only") is True,
                context.get("free_form_content_allowed") is False,
                context.get("preview_only") is True,
                context.get("real_approval_request_allowed") is False,
                context.get("approval_result_allowed") is False,
                context.get("approval_token_access_allowed") is False,
                context.get("approval_binding_allowed") is False,
                context.get("token_verification_allowed") is False,
                context.get("replay_record_allowed") is False,
                context.get("model_call_allowed") is False,
                context.get("tool_execution_allowed") is False,
                context.get("arc_dispatch_allowed") is False,
                context.get("connector_access_allowed") is False,
                context.get("submission_allowed") is False,
                context.get("approval_required") is False,
                not context.get("connector_live_access"),
                not context.get("cross_tenant_access"),
                not context.get("unrestricted_tool"),
            )
        )

    @staticmethod
    def _is_attended_proposal_context(context: dict[str, Any]) -> bool:
        return all(
            (
                bool(context.get("tenant_id")),
                bool(context.get("customer_context_id")),
                context.get("execution_mode") == "plan_only",
                context.get("external_effect") == "none",
                context.get("evidence_required") is True,
                bool(context.get("evidence_artifact_ids")),
                context.get("attended") is True,
                context.get("operator_confirmation") is True,
                context.get("operation") in {"create", "edit", "propose", "accept", "deny", "cancel"},
                context.get("data_classification") == "synthetic_fixture_only",
                context.get("synthetic_data_only") is True,
                context.get("free_form_content_allowed") is False,
                context.get("model_call_allowed") is False,
                context.get("tool_execution_allowed") is False,
                context.get("approval_token_access_allowed") is False,
                context.get("arc_dispatch_allowed") is False,
                context.get("connector_access_allowed") is False,
                context.get("submission_allowed") is False,
                context.get("approval_required") is False,
                not context.get("connector_live_access"),
                not context.get("cross_tenant_access"),
                not context.get("unrestricted_tool"),
            )
        )

    @staticmethod
    def _is_attended_helper_context(context: dict[str, Any]) -> bool:
        return all(
            (
                bool(context.get("tenant_id")),
                bool(context.get("customer_context_id")),
                context.get("execution_mode") == "plan_only",
                context.get("external_effect") == "none",
                context.get("evidence_required") is True,
                bool(context.get("evidence_artifact_ids")),
                context.get("attended") is True,
                context.get("operator_confirmation") is True,
                context.get("helper_role") == "office_operations_helper",
                context.get("review_type") == "registration_sop_review",
                context.get("data_classification") == "synthetic_fixture_only",
                context.get("synthetic_data_only") is True,
                context.get("deterministic_review") is True,
                context.get("model_call_allowed") is False,
                context.get("tool_execution_allowed") is False,
                context.get("memory_access_allowed") is False,
                context.get("approval_token_access_allowed") is False,
                context.get("arc_dispatch_allowed") is False,
                context.get("connector_access_allowed") is False,
                context.get("submission_allowed") is False,
                context.get("approval_required") is False,
                not context.get("connector_live_access"),
                not context.get("cross_tenant_access"),
                not context.get("unrestricted_tool"),
            )
        )

    @staticmethod
    def _is_attended_model_context(context: dict[str, Any]) -> bool:
        return all(
            (
                bool(context.get("tenant_id")),
                bool(context.get("customer_context_id")),
                context.get("execution_mode") == "read_only",
                context.get("external_effect") == "none",
                context.get("evidence_required") is True,
                bool(context.get("evidence_artifact_ids")),
                context.get("attended") is True,
                context.get("operator_confirmation") is True,
                context.get("provider") == "openai_codex_subscription",
                context.get("auth_method") == "saved_chatgpt_cli_session",
                context.get("sandbox_mode") == "read_only",
                context.get("session_persistence") == "ephemeral",
                context.get("tools_enabled") is False,
                context.get("web_search_enabled") is False,
                context.get("user_config_loaded") is False,
                context.get("rules_loaded") is False,
                context.get("fallback_allowed") is False,
                context.get("data_classification") in {"public", "internal"},
                context.get("taint_status") == "clean",
                context.get("approval_required") is False,
                not context.get("connector_live_access"),
                not context.get("cross_tenant_access"),
                not context.get("unrestricted_tool"),
            )
        )

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
