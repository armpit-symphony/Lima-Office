"""Mock-only Guardian decision replay verifier for Phase 1A tests."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.invariants import DEFAULT_REFERENCE_TIME, assert_guardian_decision_replay_safe


class GuardianDecisionReplayVerifier:
    """Validate and consume Guardian decision nonces in memory only."""

    def __init__(
        self,
        validator: ContractValidator,
        *,
        reference_time: str | None = DEFAULT_REFERENCE_TIME,
    ) -> None:
        self.validator = validator
        self.reference_time = reference_time
        self._consumed_nonces: set[str] = set()

    @property
    def consumed_nonces(self) -> frozenset[str]:
        return frozenset(self._consumed_nonces)

    def verify_once(self, decision: dict[str, Any], requested_action: dict[str, Any]) -> dict[str, Any]:
        """Validate a decision and mark its nonce consumed for this in-memory verifier."""

        validated = self.validator.validate(copy.deepcopy(decision), "guardian.decision")
        checked = assert_guardian_decision_replay_safe(
            validated,
            requested_action,
            reference_time=self.reference_time,
            consumed_nonces=self._consumed_nonces,
            consume_nonce=True,
        )
        replay = self._build_replay_record(checked, requested_action, "valid_first_use", [])
        return self.validator.validate(replay, "guardian.replay")

    def check(self, decision: dict[str, Any], requested_action: dict[str, Any]) -> dict[str, Any]:
        """Validate a decision without consuming nonce state."""

        validated = self.validator.validate(copy.deepcopy(decision), "guardian.decision")
        checked = assert_guardian_decision_replay_safe(
            validated,
            requested_action,
            reference_time=self.reference_time,
            consumed_nonces=self._consumed_nonces,
            consume_nonce=False,
        )
        replay = self._build_replay_record(checked, requested_action, "valid_first_use", [])
        return self.validator.validate(replay, "guardian.replay")

    def _build_replay_record(
        self,
        decision: dict[str, Any],
        requested_action: dict[str, Any],
        result: str,
        mismatch_reasons: list[str],
    ) -> dict[str, Any]:
        return {
            "contract_name": "guardian.replay",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "tenant_id": decision["tenant_id"],
            "customer_context_id": decision["customer_context_id"],
            "environment": "dry_run",
            "correlation_id": decision["correlation_id"],
            "causation_id": decision["decision_id"],
            "idempotency_key": f"idem-replay-{decision['decision_id']}",
            "producer": {
                "component": "guardian",
                "produced_at": self.reference_time or decision["issued_at"],
            },
            "policy_version": decision["policy_version"],
            "replay_check_id": f"gr-{decision['decision_id']}",
            "guardian_decision_id": decision["decision_id"],
            "decision_nonce": decision["decision_nonce"],
            "approval_binding_id": decision.get("approval_binding_id"),
            "token_verification_id": decision.get("token_verification_id"),
            "task_id": requested_action.get("task_id") or decision.get("bound_task_id"),
            "worker_id": requested_action.get("worker_id") or decision.get("bound_worker_id"),
            "action_type": requested_action.get("action_type") or decision.get("bound_action_type"),
            "tool_scope": requested_action.get("tool_scope") or decision.get("bound_tool_scope"),
            "decision_scope_hash": decision.get("decision_scope_hash"),
            "policy_snapshot_hash": decision.get("policy_snapshot_hash"),
            "expires_at": decision.get("expires_at"),
            "replay_check_result": result,
            "checked_at": self.reference_time or decision["issued_at"],
            "evidence_refs": decision.get("evidence_refs", decision.get("evidence_artifact_ids", [])),
            "mismatch_reasons": mismatch_reasons,
            "data_classification": decision.get("data_classification", "internal"),
            "redaction_level": decision.get("redaction_level", "metadata_only"),
            "retention_class": "evidence_retained_placeholder",
            "export_eligible": True,
            "delete_policy_ref": "policy.audit_export_customer_exit.placeholder",
        }
