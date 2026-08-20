"""Mandatory Guardian Core authority boundary for the Supervisor control plane."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import PolicyDenyError

from .decision import build_guardian_decision


class GuardianAuthority(Protocol):
    """Authority contract required by the governed Supervisor path."""

    def evaluate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Return a request-bound Guardian decision or fail closed."""


class GuardianCoreAuthority:
    """Call Guardian Core without a fallback policy."""

    def __init__(
        self,
        validator: ContractValidator,
        decider: Callable[..., Any] | None = None,
    ) -> None:
        self.validator = validator
        self._decider = decider

    def evaluate(self, request: dict[str, Any]) -> dict[str, Any]:
        request = self.validator.validate(request, "guardian.evaluation.request")
        decider = self._decider or self._load_decider()
        tool_name, extra_policies = self._policy_input(request)
        args = {
            "request_id": request["request_id"],
            "action": request["action"],
            "action_category": request["server_derived_category"],
            "resource": dict(request["resource"]),
            "request_hash": request["request_hash"],
            "payload_hash": request["payload_hash"],
        }
        try:
            raw_decision = decider(
                tool_name,
                args,
                room_execution_allowed=False,
                is_operator=request["actor_role"] in {"operator", "supervisor"},
                is_privileged=request["actor_role"] in {"field_it", "security_reviewer"},
                extra_policies=extra_policies,
            )
        except Exception as exc:
            raise PolicyDenyError("Guardian authority evaluation failed closed") from exc

        semantic = str(getattr(raw_decision, "action", "") or "deny").strip().lower()
        mapped = {
            "allow": "allow_with_evidence",
            "confirm": "requires_approval",
            "privileged_reveal": "requires_approval",
            "deny": "deny",
        }.get(semantic, "deny")
        denied = mapped == "deny"
        evidence_refs = list(request["evidence_refs"])
        if not evidence_refs:
            raise PolicyDenyError("Guardian evaluation requires pre-action evidence")
        policy_snapshot_hash = self._policy_snapshot_hash(
            policy_version=request["policy_version"],
            tool_name=tool_name,
            extra_policies=extra_policies,
        )
        decision = build_guardian_decision(
            action=request["action"],
            decision=mapped,
            reason="Guardian denied the structured control-plane request." if denied else None,
            tenant_id=request["tenant_id"],
            customer_context_id=request["customer_context_id"],
            context={
                "request_id": request["request_id"],
                "correlation_id": request["correlation_id"],
                "idempotency_key": request["idempotency_key"],
                "requested_by": {
                    "actor_type": (
                        request["actor_role"]
                        if request["actor_role"] in {"operator", "supervisor"}
                        else "supervisor"
                    ),
                    "actor_id": request["actor_id"],
                },
                "resource_ref": {
                    "resource_type": request["resource"]["resource_type"],
                    "resource_id": request["resource"]["resource_id"],
                    "resource_scope": "task_scoped",
                },
                "valid_for_action_ref": request["request_hash"],
                "decision_scope_hash": request["payload_hash"],
                "bound_tenant_id": request["tenant_id"],
                "bound_worker_id": request["worker_id"],
                "bound_action_type": request["action"],
                "schema_action_class": self._action_class(request["action"]),
                "approval_request_id": (
                    f"approval:{request['request_id']}"
                    if mapped == "requires_approval"
                    else None
                ),
                "policy_version": request["policy_version"],
                "policy_snapshot_hash": policy_snapshot_hash,
                "created_at": request["issued_at"],
                "issued_at": request["issued_at"],
                "effective_at": request["issued_at"],
                "expires_at": request["expires_at"],
                "evidence_artifact_ids": evidence_refs,
                "evidence_artifact_id": evidence_refs[0],
                "pre_action_evidence_refs": evidence_refs,
                "post_action_evidence_refs": [],
            },
        )
        return self.validator.validate(decision, "guardian.decision")

    @staticmethod
    def _policy_snapshot_hash(
        *,
        policy_version: str,
        tool_name: str,
        extra_policies: Mapping[str, Mapping[str, Any]],
    ) -> str:
        """Bind evidence to the server-owned Guardian policy input."""

        snapshot = {
            "authority": "guardian_core.policy.decide_tool_use",
            "policy_version": policy_version,
            "tool_name": tool_name,
            "policy": extra_policies[tool_name],
            "room_execution_allowed": False,
        }
        canonical = json.dumps(
            snapshot,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    @staticmethod
    def _load_decider() -> Callable[..., Any]:
        try:
            from guardian_core.policy import decide_tool_use
        except (ImportError, ModuleNotFoundError) as exc:
            raise PolicyDenyError("Guardian authority is unavailable") from exc
        return decide_tool_use

    @staticmethod
    def _action_class(action: str) -> str:
        return {
            "safe_read": "lima_it_diagnostic",
            "safe_list": "lima_it_diagnostic",
            "status": "lima_it_diagnostic",
            "external_write": "tool_invocation",
            "file_mutation": "tool_invocation",
            "credential_access": "tool_invocation",
            "shell": "tool_invocation",
            "unknown": "privileged_operation",
        }.get(action, "privileged_operation")

    @staticmethod
    def _policy_input(
        request: Mapping[str, Any],
    ) -> tuple[str, dict[str, dict[str, Any]]]:
        action = str(request["action"])
        policy_by_action: dict[str, tuple[str, str, str, str, str, bool]] = {
            "safe_read": ("arc_status_preview", "read", "arc_status", "allow", "read", False),
            "safe_list": ("arc_document_list", "read", "file", "allow", "read", False),
            "status": ("arc_status_preview", "read", "arc_status", "allow", "read", False),
            "external_write": (
                "arc_external_write_preview",
                "write",
                "external_write",
                "confirm",
                "write_external",
                True,
            ),
            "file_mutation": (
                "arc_file_mutation_preview",
                "write",
                "file_mutation",
                "confirm",
                "write_external",
                True,
            ),
            "credential_access": (
                "arc_credential_access_preview",
                "admin",
                "credential",
                "privileged_reveal",
                "credential_reveal",
                True,
            ),
            "shell": ("arc_shell_preview", "admin", "shell", "deny", "deny", True),
            "unknown": ("arc_unknown_preview", "admin", "unknown", "deny", "deny", True),
        }
        tool_name, scope, resource, default_action, action_type, high_risk = policy_by_action[
            action if action in policy_by_action else "unknown"
        ]
        return tool_name, {
            tool_name: {
                "scope": scope,
                "resource": resource,
                "default_action": default_action,
                "action_type": action_type,
                "high_risk": high_risk,
            }
        }
