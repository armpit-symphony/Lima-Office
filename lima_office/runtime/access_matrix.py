"""Mock-only RBAC/session/device trust matrix classifier for Phase 1A tests."""

from __future__ import annotations

from typing import Any

from lima_office.runtime.taxonomy import validate_reason_codes


PRIVILEGED_ACTIONS = frozenset(
    {
        "approve_privileged_task",
        "approve_lima_it_remediation",
        "update_rollback_approval",
        "connector_consent_review",
        "request_customer_delete",
        "receive_privileged_task_metadata",
    }
)

MUTATING_LEVELS = frozenset({"request", "approve", "deny", "administer"})
BLOCKING_DEVICE_STATUSES = frozenset({"untrusted", "attestation_failed", "blocked_mvp"})

KNOWN_ROLES = frozenset(
    {
        "sparkpit_operator",
        "customer_admin",
        "approver",
        "field_it",
        "auditor_readonly",
        "security_reviewer",
        "worker_owner",
        "arc_worker_node",
        "supervisor_service",
        "helper_agent",
    }
)


class AccessMatrixEvaluator:
    """Evaluates metadata-only role/session/device posture without authorization."""

    def evaluate(
        self,
        *,
        rbac_matrix: dict[str, Any],
        action: str,
        session_policy: dict[str, Any] | None = None,
        device_trust: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reasons: list[str] = []

        role = rbac_matrix.get("role")
        if role not in KNOWN_ROLES:
            reasons.append("role_not_permitted")
            return self._blocked_result(reasons, "blocked", role=role, action=action)

        permission = self._permission_for_action(rbac_matrix, action)
        if permission is None:
            reasons.append("role_not_permitted")
            return self._blocked_result(reasons, "blocked", role=role, action=action)
        level = permission.get("level")
        if not isinstance(level, str):
            reasons.append("role_not_permitted")
            return self._blocked_result(reasons, "blocked", role=role, action=action)

        # Breakglass remains blocked in MVP by policy.
        if action == "breakglass_request_review":
            reasons.append("breakglass_blocked_mvp")
            return self._blocked_result(reasons, "blocked_mvp", role=role, action=action)

        if role == "auditor_readonly" and level in MUTATING_LEVELS:
            reasons.append("role_not_permitted")
            return self._blocked_result(reasons, "blocked", role=role, action=action)

        if action == "approve_lima_it_remediation" and level in {"approve", "administer"}:
            if rbac_matrix.get("separation_of_duties_required") is not True:
                reasons.append("sod_required")
            reasons.append("privileged_action_blocked")
            return self._blocked_result(reasons, "blocked_mvp", role=role, action=action)

        if level in {"none", "blocked_mvp"}:
            reasons.append("privileged_action_blocked")
            return self._blocked_result(
                reasons,
                "blocked_mvp" if level == "blocked_mvp" else "blocked",
                role=role,
                action=action,
            )

        if action in PRIVILEGED_ACTIONS and level in {"approve", "administer"}:
            if rbac_matrix.get("mfa_requirement") not in {
                "phishing_resistant_preferred",
                "step_up_required_for_privileged",
            }:
                reasons.append("mfa_required")

            if session_policy is None:
                reasons.append("session_revoked")
            else:
                if session_policy.get("role") not in {role, None}:
                    reasons.append("role_not_permitted")
                if session_policy.get("mfa_requirement") != "step_up_required_for_privileged":
                    reasons.append("mfa_required")
                if action not in (session_policy.get("step_up_required_actions") or []):
                    reasons.append("mfa_required")
                if "session_revoked" in (session_policy.get("reason_codes") or []):
                    reasons.append("session_revoked")

            if device_trust is None:
                reasons.append("device_untrusted")
            else:
                status = device_trust.get("trust_status")
                if status in BLOCKING_DEVICE_STATUSES:
                    if status == "attestation_failed":
                        reasons.append("attestation_failed")
                    else:
                        reasons.append("device_untrusted")

        if device_trust is not None:
            if device_trust.get("actor_type") == "arc_worker_node" and action == "receive_privileged_task_metadata":
                if device_trust.get("trust_status") in {"attestation_failed", "attestation_required"}:
                    reasons.append(
                        "attestation_failed"
                        if device_trust.get("trust_status") == "attestation_failed"
                        else "attestation_required"
                    )
                    reasons.append("privileged_action_blocked")

        if reasons:
            return self._blocked_result(reasons, "blocked", role=role, action=action)

        normalized_codes = validate_reason_codes([])
        return {
            "role": role,
            "action": action,
            "matrix_outcome": level,
            "reason_codes": normalized_codes,
            "fail_closed": False,
            "can_authorize": False,
        }

    @staticmethod
    def _permission_for_action(rbac_matrix: dict[str, Any], action: str) -> dict[str, Any] | None:
        permissions = rbac_matrix.get("permissions")
        if not isinstance(permissions, list):
            return None
        for permission in permissions:
            if isinstance(permission, dict) and permission.get("action") == action:
                return permission
        return None

    @staticmethod
    def _blocked_result(
        reason_codes: list[str],
        matrix_outcome: str,
        *,
        role: Any,
        action: Any,
    ) -> dict[str, Any]:
        normalized_codes = validate_reason_codes(sorted(set(reason_codes)))
        return {
            "role": role,
            "action": action,
            "matrix_outcome": matrix_outcome,
            "reason_codes": normalized_codes,
            "fail_closed": True,
            "can_authorize": False,
        }
