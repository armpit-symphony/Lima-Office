"""In-memory Guardian replay drill simulator for the narrow Phase 1C slice."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import (
    EvidenceRequiredError,
    GuardianReplayDrillTransitionError,
    GuardianReplayDrillValidationError,
    PolicyDenyError,
    UnsafeRuntimeActionError,
)
from lima_office.runtime.invariants import (
    DEFAULT_REFERENCE_TIME,
    DEFAULT_GUARDIAN_CLOCK_SKEW_SECONDS,
    MAX_GUARDIAN_DECISION_AGE_SECONDS,
    assert_guardian_decision_replay_safe,
)


DRILL_STATES = frozenset(
    {
        "planned",
        "decision_registered",
        "nonce_reserved",
        "first_use_validated",
        "nonce_consumed",
        "replay_denied",
        "expired_denied",
        "stale_denied",
        "mismatch_denied",
        "blocked_mvp_denied",
        "failed_closed_recorded",
    }
)

REGISTER_ALLOWED_INITIAL_STATE = "planned"

ALLOWED_TRANSITIONS = {
    "planned": frozenset({"decision_registered"}),
    "decision_registered": frozenset({"nonce_reserved"}),
    "nonce_reserved": frozenset(
        {"first_use_validated", "expired_denied", "stale_denied", "mismatch_denied", "blocked_mvp_denied", "failed_closed_recorded"}
    ),
    "first_use_validated": frozenset({"nonce_consumed"}),
    "nonce_consumed": frozenset({"replay_denied"}),
    "replay_denied": frozenset(),
    "expired_denied": frozenset(),
    "stale_denied": frozenset(),
    "mismatch_denied": frozenset(),
    "blocked_mvp_denied": frozenset(),
    "failed_closed_recorded": frozenset(),
}

STATE_CONTRACT_MAP = {
    "planned": frozenset({"guardian.decision"}),
    "decision_registered": frozenset({"guardian.decision"}),
    "nonce_reserved": frozenset({"replay.store.record"}),
    "first_use_validated": frozenset({"guardian.replay"}),
    "nonce_consumed": frozenset({"replay.store.record"}),
    "replay_denied": frozenset({"guardian.replay"}),
    "expired_denied": frozenset({"guardian.replay"}),
    "stale_denied": frozenset({"guardian.replay"}),
    "mismatch_denied": frozenset({"guardian.replay"}),
    "blocked_mvp_denied": frozenset({"guardian.replay"}),
    "failed_closed_recorded": frozenset({"replay.store.record"}),
}

CONTRACT_TO_SCHEMA = {
    "guardian.decision": "guardian.decision",
    "guardian.replay": "guardian.replay",
    "replay.store.record": "replay.store.record",
}

DENIAL_RESULT_TO_STATE = {
    "replay_denied": "replay_denied",
    "expired": "expired_denied",
    "stale": "stale_denied",
    "scope_mismatch": "mismatch_denied",
    "tenant_mismatch": "mismatch_denied",
    "blocked_mvp": "blocked_mvp_denied",
}

NONCE_RESULT_FIELD_BY_CONTRACT = {
    "guardian.decision": "decision_nonce",
    "guardian.replay": "decision_nonce",
    "replay.store.record": "decision_nonce",
}

DECISION_ID_FIELD_BY_CONTRACT = {
    "guardian.decision": "guardian_decision_id",
    "guardian.replay": "guardian_decision_id",
    "replay.store.record": "guardian_decision_id",
}


@dataclass(frozen=True)
class GuardianReplayDrillTransition:
    guardian_decision_id: str
    tenant_id: str
    from_state: str | None
    to_state: str
    updated_at: str
    contract_name: str


class GuardianReplayDrillSimulator:
    """Validates and simulates Guardian replay drill metadata in memory only."""

    def __init__(self, validator: ContractValidator, *, reference_time: str | None = DEFAULT_REFERENCE_TIME) -> None:
        self.validator = validator
        self.reference_time = reference_time
        self._current: dict[str, dict[str, Any]] = {}
        self._history: dict[str, list[GuardianReplayDrillTransition]] = {}
        self._decision_by_id: dict[str, dict[str, Any]] = {}
        self._reserved_nonces_by_tenant: dict[str, set[str]] = {}
        self._consumed_nonces_by_tenant: dict[str, set[str]] = {}

    @property
    def consumed_nonces(self) -> frozenset[str]:
        aggregate: set[str] = set()
        for values in self._consumed_nonces_by_tenant.values():
            aggregate.update(values)
        return frozenset(aggregate)

    def register(
        self,
        payload: dict[str, Any],
        *,
        initial_state: str = REGISTER_ALLOWED_INITIAL_STATE,
        guardian_decision_id: str | None = None,
    ) -> dict[str, Any]:
        normalized = self._normalize_payload(payload, guardian_decision_id=guardian_decision_id)
        record_id = normalized["guardian_decision_id"]
        tenant_id = normalized["tenant_id"]
        validated = normalized["payload"]
        contract_name = normalized["contract_name"]
        decision_nonce = normalized["decision_nonce"]

        if record_id in self._current:
            raise GuardianReplayDrillTransitionError(f"guardian decision already registered in simulator: {record_id}")

        self._ensure_known_state(initial_state)
        if initial_state != REGISTER_ALLOWED_INITIAL_STATE:
            raise GuardianReplayDrillTransitionError("new Guardian replay drill registration must start from planned")
        self._assert_state_contract_compatibility(initial_state, contract_name=contract_name)
        self._enforce_common_fail_closed_rules(
            validated,
            contract_name=contract_name,
            tenant_id=tenant_id,
            to_state=initial_state,
            requested_action=None,
            approval_binding=None,
            token_verification=None,
        )
        self._assert_guardian_decision_payload_valid(validated)

        self._current[record_id] = {
            "tenant_id": tenant_id,
            "decision_nonce": decision_nonce,
            "state": initial_state,
            "contract_name": contract_name,
            "payload": copy.deepcopy(validated),
        }
        self._decision_by_id[record_id] = copy.deepcopy(validated)
        self._history[record_id] = [
            GuardianReplayDrillTransition(
                guardian_decision_id=record_id,
                tenant_id=tenant_id,
                from_state=None,
                to_state=initial_state,
                updated_at=self._updated_at(validated),
                contract_name=contract_name,
            )
        ]
        return self.snapshot(record_id)

    def transition(
        self,
        guardian_decision_id: str,
        to_state: str,
        payload: dict[str, Any],
        *,
        requested_action: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current = self._current.get(guardian_decision_id)
        if current is None:
            raise GuardianReplayDrillTransitionError(f"unknown guardian decision id: {guardian_decision_id}")

        normalized = self._normalize_payload(payload, guardian_decision_id=guardian_decision_id)
        tenant_id = normalized["tenant_id"]
        validated = normalized["payload"]
        contract_name = normalized["contract_name"]
        decision_nonce = normalized["decision_nonce"]

        if current["tenant_id"] != tenant_id:
            raise GuardianReplayDrillTransitionError("guardian replay drill tenant mismatch")
        if decision_nonce != current["decision_nonce"]:
            raise GuardianReplayDrillTransitionError("guardian replay drill nonce mismatch")

        from_state = current["state"]
        self._ensure_known_state(from_state)
        self._ensure_known_state(to_state)
        if from_state == to_state:
            raise GuardianReplayDrillTransitionError("same-state Guardian replay drill transitions are not allowed")
        if to_state not in ALLOWED_TRANSITIONS.get(from_state, frozenset()):
            raise GuardianReplayDrillTransitionError(f"invalid Guardian replay drill transition: {from_state} -> {to_state}")
        self._assert_state_contract_compatibility(to_state, contract_name=contract_name)

        self._enforce_common_fail_closed_rules(
            validated,
            contract_name=contract_name,
            tenant_id=tenant_id,
            to_state=to_state,
            requested_action=requested_action,
            approval_binding=approval_binding,
            token_verification=token_verification,
        )
        self._enforce_transition_specific_rules(
            from_state=from_state,
            to_state=to_state,
            payload=validated,
            contract_name=contract_name,
            decision_nonce=decision_nonce,
            requested_action=requested_action,
            approval_binding=approval_binding,
            token_verification=token_verification,
        )

        self._current[guardian_decision_id] = {
            "tenant_id": tenant_id,
            "decision_nonce": decision_nonce,
            "state": to_state,
            "contract_name": contract_name,
            "payload": copy.deepcopy(validated),
        }
        self._history.setdefault(guardian_decision_id, []).append(
            GuardianReplayDrillTransition(
                guardian_decision_id=guardian_decision_id,
                tenant_id=tenant_id,
                from_state=from_state,
                to_state=to_state,
                updated_at=self._updated_at(validated),
                contract_name=contract_name,
            )
        )
        return self.snapshot(guardian_decision_id)

    def snapshot(self, guardian_decision_id: str) -> dict[str, Any]:
        current = self._current.get(guardian_decision_id)
        if current is None:
            raise GuardianReplayDrillTransitionError(f"unknown guardian decision id: {guardian_decision_id}")
        result = copy.deepcopy(current["payload"])
        result["drill_state"] = current["state"]
        result["guardian_decision_id"] = guardian_decision_id
        result["authorization_allowed"] = False
        result["execution_allowed"] = False
        return result

    def history(self, guardian_decision_id: str) -> list[dict[str, Any]]:
        transitions = self._history.get(guardian_decision_id)
        if transitions is None:
            raise GuardianReplayDrillTransitionError(f"unknown guardian decision id: {guardian_decision_id}")
        return [
            {
                "guardian_decision_id": item.guardian_decision_id,
                "tenant_id": item.tenant_id,
                "from_state": item.from_state,
                "to_state": item.to_state,
                "updated_at": item.updated_at,
                "contract_name": item.contract_name,
            }
            for item in transitions
        ]

    def authorize_real_action(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("guardian replay drill simulator never authorizes real actions")

    def persist_nonce_state(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("guardian replay drill simulator never persists nonce state")

    def execute_tools(self, *_: Any, **__: Any) -> None:
        raise UnsafeRuntimeActionError("guardian replay drill simulator never executes tools")

    def _normalize_payload(
        self,
        payload: dict[str, Any],
        *,
        guardian_decision_id: str | None,
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise GuardianReplayDrillValidationError("guardian replay drill payload must be a JSON object")
        candidate = copy.deepcopy(payload)
        contract_name = candidate.get("contract_name")
        if contract_name not in CONTRACT_TO_SCHEMA:
            raise GuardianReplayDrillValidationError("unsupported Guardian replay drill contract")

        validated = self._validate_contract(candidate, CONTRACT_TO_SCHEMA[contract_name])
        tenant_id = validated.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id:
            raise GuardianReplayDrillValidationError("tenant_id is required")

        decision_id = self._extract_guardian_decision_id(validated, contract_name=contract_name)
        if guardian_decision_id and decision_id != guardian_decision_id:
            raise GuardianReplayDrillTransitionError("guardian decision id mismatch for transition payload")

        decision_nonce = self._extract_decision_nonce(validated, contract_name=contract_name)
        if not isinstance(decision_nonce, str) or not decision_nonce:
            raise GuardianReplayDrillTransitionError("decision nonce or nonce_ref is required")

        return {
            "payload": validated,
            "contract_name": contract_name,
            "guardian_decision_id": decision_id,
            "tenant_id": tenant_id,
            "decision_nonce": decision_nonce,
        }

    def _enforce_common_fail_closed_rules(
        self,
        payload: dict[str, Any],
        *,
        contract_name: str,
        tenant_id: str,
        to_state: str,
        requested_action: dict[str, Any] | None,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
    ) -> None:
        if payload.get("raw_content_included") is True:
            raise GuardianReplayDrillTransitionError("raw_content_included true is blocked")
        if payload.get("secret_material_included") is True:
            raise GuardianReplayDrillTransitionError("secret_material_included true is blocked")

        if contract_name == "guardian.decision":
            self._assert_guardian_decision_payload_valid(payload)
        elif contract_name == "guardian.replay":
            self._assert_guardian_replay_payload_valid(payload, expected_state=to_state)
        elif contract_name == "replay.store.record":
            self._assert_replay_store_payload_valid(payload, expected_state=to_state)

        self._assert_optional_binding_token_consistency(
            payload,
            contract_name=contract_name,
            tenant_id=tenant_id,
            approval_binding=approval_binding,
            token_verification=token_verification,
            requested_action=requested_action,
            allow_action_mismatch=(to_state == "mismatch_denied"),
        )

    def _enforce_transition_specific_rules(
        self,
        *,
        from_state: str,
        to_state: str,
        payload: dict[str, Any],
        contract_name: str,
        decision_nonce: str,
        requested_action: dict[str, Any] | None,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
    ) -> None:
        decision_id = self._extract_guardian_decision_id(payload, contract_name=contract_name)
        decision_payload = self._decision_by_id.get(decision_id)

        if to_state == "decision_registered":
            self._assert_guardian_decision_payload_valid(payload)
            self._decision_by_id[decision_id] = copy.deepcopy(payload)
            return

        if decision_payload is None:
            raise GuardianReplayDrillTransitionError("guardian decision must be registered before replay drill transitions")

        if to_state == "nonce_reserved":
            tenant_reserved = self._tenant_reserved_nonces(payload["tenant_id"])
            tenant_consumed = self._tenant_consumed_nonces(payload["tenant_id"])
            if payload.get("nonce_status") != "reserved":
                raise GuardianReplayDrillTransitionError("nonce_reserved requires replay.store.record nonce_status reserved")
            if payload.get("atomicity_status") != "pending":
                raise GuardianReplayDrillTransitionError("nonce_reserved requires replay.store.record atomicity_status pending")
            if decision_nonce in tenant_reserved:
                raise GuardianReplayDrillTransitionError("duplicate nonce reservation is blocked")
            if decision_nonce in tenant_consumed:
                raise GuardianReplayDrillTransitionError("duplicate nonce reservation is blocked")
            tenant_reserved.add(decision_nonce)
            return

        if to_state == "first_use_validated":
            self._require_bound_first_use_inputs(
                decision_payload,
                approval_binding=approval_binding,
                token_verification=token_verification,
            )
            requested = requested_action if requested_action is not None else self._requested_action_from_replay_payload(payload)
            self._assert_decision_is_usable(
                decision_payload,
                requested_action=requested,
                consume_nonce=False,
                tenant_id=payload["tenant_id"],
            )
            if payload.get("replay_check_result") != "valid_first_use":
                raise GuardianReplayDrillTransitionError("first_use_validated requires guardian.replay valid_first_use result")
            return

        if to_state == "nonce_consumed":
            tenant_reserved = self._tenant_reserved_nonces(payload["tenant_id"])
            tenant_consumed = self._tenant_consumed_nonces(payload["tenant_id"])
            if payload.get("nonce_status") != "consumed":
                raise GuardianReplayDrillTransitionError("nonce_consumed requires replay.store.record nonce_status consumed")
            if decision_nonce in tenant_consumed:
                raise GuardianReplayDrillTransitionError("duplicate nonce consumption is blocked")
            if decision_nonce not in tenant_reserved:
                raise GuardianReplayDrillTransitionError("nonce_consumed requires prior nonce reservation")
            tenant_reserved.remove(decision_nonce)
            tenant_consumed.add(decision_nonce)
            return

        if to_state == "replay_denied":
            if decision_nonce not in self._tenant_consumed_nonces(payload["tenant_id"]):
                raise GuardianReplayDrillTransitionError("replay_denied requires consumed nonce")
            self._require_denial_evidence(payload)
            return

        if to_state == "expired_denied":
            self._assert_decision_denial_condition(decision_payload, requested_action, expected="expired")
            self._require_denial_evidence(payload)
            return

        if to_state == "stale_denied":
            self._assert_decision_denial_condition(decision_payload, requested_action, expected="stale")
            self._require_denial_evidence(payload)
            return

        if to_state == "mismatch_denied":
            mismatch_categories = self._assert_decision_denial_condition(
                decision_payload,
                requested_action,
                expected="mismatch",
                approval_binding=approval_binding,
                token_verification=token_verification,
            )
            declared_reasons = payload.get("mismatch_reasons")
            if not isinstance(declared_reasons, list) or not declared_reasons:
                raise GuardianReplayDrillTransitionError("mismatch_denied requires mismatch_reasons")
            declared = {item for item in declared_reasons if isinstance(item, str) and item}
            if not declared:
                raise GuardianReplayDrillTransitionError("mismatch_denied requires non-empty mismatch_reasons")
            if declared.isdisjoint(mismatch_categories):
                expected = ", ".join(sorted(mismatch_categories))
                raise GuardianReplayDrillTransitionError(
                    f"mismatch_denied mismatch_reasons do not match structured mismatch categories: {expected}"
                )
            self._require_denial_evidence(payload)
            return

        if to_state == "blocked_mvp_denied":
            self._assert_decision_denial_condition(decision_payload, requested_action, expected="blocked_mvp")
            self._require_denial_evidence(payload)
            return

        if to_state == "failed_closed_recorded":
            if payload.get("atomicity_status") != "failed_closed":
                raise GuardianReplayDrillTransitionError("failed_closed_recorded requires replay.store.record atomicity_status failed_closed")
            if not payload.get("failure_reason"):
                raise GuardianReplayDrillTransitionError("failed_closed_recorded requires failure_reason")
            evidence_refs = payload.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs:
                raise EvidenceRequiredError("failed_closed_recorded requires evidence_refs")
            self._assert_evidence_ref_list(evidence_refs, field_name="evidence_refs")
            return

    def _assert_guardian_decision_payload_valid(self, payload: dict[str, Any]) -> None:
        if payload.get("decision_id") != payload.get("guardian_decision_id"):
            raise GuardianReplayDrillTransitionError("guardian decision id fields must match")
        decision_nonce = payload.get("decision_nonce")
        if not isinstance(decision_nonce, str) or not decision_nonce:
            raise GuardianReplayDrillTransitionError("guardian decision requires decision_nonce for replay drill simulation")
        if payload.get("replay_policy") != "one_time":
            raise GuardianReplayDrillTransitionError("guardian replay drill simulator requires replay_policy one_time")

    def _assert_guardian_replay_payload_valid(self, payload: dict[str, Any], *, expected_state: str) -> None:
        replay_result = payload.get("replay_check_result")
        expected = "valid_first_use" if expected_state == "first_use_validated" else None
        if expected_state == "replay_denied":
            expected = "replay_denied"
        elif expected_state == "expired_denied":
            expected = "expired"
        elif expected_state == "stale_denied":
            expected = "stale"
        elif expected_state == "mismatch_denied":
            expected = "scope_mismatch"
        elif expected_state == "blocked_mvp_denied":
            expected = "blocked_mvp"
        if expected and replay_result != expected:
            raise GuardianReplayDrillTransitionError(
                f"guardian.replay result mismatch for {expected_state}: expected {expected}, got {replay_result}"
            )
        if expected_state in {"replay_denied", "expired_denied", "stale_denied", "mismatch_denied", "blocked_mvp_denied"}:
            self._require_denial_evidence(payload)
        if expected_state == "first_use_validated" and payload.get("denial_evidence_ref") is not None:
            raise GuardianReplayDrillTransitionError("valid_first_use replay payload must not include denial_evidence_ref")

    def _assert_replay_store_payload_valid(self, payload: dict[str, Any], *, expected_state: str) -> None:
        if expected_state == "nonce_reserved":
            if payload.get("nonce_status") != "reserved":
                raise GuardianReplayDrillTransitionError("nonce_reserved requires nonce_status reserved")
            if payload.get("consumed_at") is not None:
                raise GuardianReplayDrillTransitionError("nonce_reserved cannot include consumed_at")
        if expected_state == "nonce_consumed":
            if payload.get("nonce_status") != "consumed":
                raise GuardianReplayDrillTransitionError("nonce_consumed requires nonce_status consumed")
            if not payload.get("consumed_at"):
                raise GuardianReplayDrillTransitionError("nonce_consumed requires consumed_at")
        if expected_state == "failed_closed_recorded":
            if payload.get("atomicity_status") != "failed_closed":
                raise GuardianReplayDrillTransitionError("failed_closed_recorded requires atomicity_status failed_closed")
            if not payload.get("failure_reason"):
                raise GuardianReplayDrillTransitionError("failed_closed_recorded requires failure_reason")
            if not payload.get("evidence_refs"):
                raise EvidenceRequiredError("failed_closed_recorded requires evidence refs")

    def _assert_decision_is_usable(
        self,
        decision: dict[str, Any],
        *,
        requested_action: dict[str, Any],
        consume_nonce: bool,
        tenant_id: str,
    ) -> None:
        try:
            assert_guardian_decision_replay_safe(
                copy.deepcopy(decision),
                copy.deepcopy(requested_action),
                reference_time=self.reference_time,
                consumed_nonces=self._tenant_consumed_nonces(tenant_id),
                consume_nonce=consume_nonce,
            )
        except (PolicyDenyError, EvidenceRequiredError) as exc:
            raise GuardianReplayDrillTransitionError(str(exc)) from exc

    def _assert_decision_denial_condition(
        self,
        decision: dict[str, Any],
        requested_action: dict[str, Any] | None,
        *,
        expected: str,
        approval_binding: dict[str, Any] | None = None,
        token_verification: dict[str, Any] | None = None,
    ) -> set[str]:
        if expected == "expired" and not self._is_decision_expired(decision):
            raise GuardianReplayDrillTransitionError("expired_denied requires expired guardian decision metadata")
        if expected == "expired":
            return {"expired"}
        if expected == "stale" and not self._is_decision_stale(decision):
            raise GuardianReplayDrillTransitionError("stale_denied requires stale guardian decision metadata")
        if expected == "stale":
            return {"stale"}
        if expected == "blocked_mvp" and not self._is_blocked_mvp_decision(decision):
            raise GuardianReplayDrillTransitionError("blocked_mvp_denied requires blocked-mvp guardian decision metadata")
        if expected == "blocked_mvp":
            return {"blocked_mvp"}
        if expected == "mismatch":
            action = requested_action
            if action is None:
                raise GuardianReplayDrillTransitionError("mismatch_denied requires requested_action mismatch metadata")
            mismatch_categories = self._collect_mismatch_categories(
                decision,
                action,
                approval_binding=approval_binding,
                token_verification=token_verification,
            )
            if not mismatch_categories:
                raise GuardianReplayDrillTransitionError("mismatch_denied requires structured mismatch metadata")
            return mismatch_categories
        return set()

    @staticmethod
    def _require_denial_evidence(payload: dict[str, Any]) -> None:
        denial_ref = payload.get("denial_evidence_ref")
        pre_action_refs = payload.get("pre_action_evidence_refs")
        evidence_refs = payload.get("evidence_refs")
        if not isinstance(denial_ref, str) or not denial_ref:
            raise EvidenceRequiredError("denial replay drill states require denial_evidence_ref")
        if not isinstance(pre_action_refs, list) or not pre_action_refs:
            raise EvidenceRequiredError("denial replay drill states require pre_action_evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            raise EvidenceRequiredError("denial replay drill states require evidence_refs")
        GuardianReplayDrillSimulator._assert_evidence_ref_format(denial_ref)
        GuardianReplayDrillSimulator._assert_evidence_ref_list(pre_action_refs, field_name="pre_action_evidence_refs")
        GuardianReplayDrillSimulator._assert_evidence_ref_list(evidence_refs, field_name="evidence_refs")
        if denial_ref not in pre_action_refs:
            raise EvidenceRequiredError("denial_evidence_ref must appear in pre_action_evidence_refs")
        if denial_ref not in evidence_refs:
            raise EvidenceRequiredError("denial_evidence_ref must appear in evidence_refs")

    def _assert_optional_binding_token_consistency(
        self,
        payload: dict[str, Any],
        *,
        contract_name: str,
        tenant_id: str,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
        requested_action: dict[str, Any] | None,
        allow_action_mismatch: bool = False,
    ) -> None:
        decision_id = self._extract_guardian_decision_id(payload, contract_name=contract_name)
        decision = self._decision_by_id.get(decision_id)

        validated_binding: dict[str, Any] | None = None
        validated_token: dict[str, Any] | None = None
        if approval_binding is not None:
            validated_binding = self._validate_contract(approval_binding, "approval.binding")
            if validated_binding.get("tenant_id") != tenant_id:
                raise GuardianReplayDrillTransitionError("approval binding tenant mismatch")
            if decision is not None:
                required_binding_id = decision.get("approval_binding_id")
                if isinstance(required_binding_id, str) and required_binding_id and validated_binding.get("binding_id") != required_binding_id:
                    raise GuardianReplayDrillTransitionError("approval binding mismatch for guardian decision")
                if validated_binding.get("guardian_decision_id") not in {decision.get("decision_id"), decision.get("guardian_decision_id")}:
                    raise GuardianReplayDrillTransitionError("approval binding guardian_decision_id mismatch")

        if token_verification is not None:
            validated_token = self._validate_contract(token_verification, "token.verification")
            if validated_token.get("tenant_id") != tenant_id:
                raise GuardianReplayDrillTransitionError("token verification tenant mismatch")
            if decision is not None:
                required_token_id = decision.get("token_verification_id")
                if isinstance(required_token_id, str) and required_token_id and validated_token.get("token_verification_id") != required_token_id:
                    raise GuardianReplayDrillTransitionError("token verification mismatch for guardian decision")
                if validated_token.get("guardian_decision_id") not in {decision.get("decision_id"), decision.get("guardian_decision_id")}:
                    raise GuardianReplayDrillTransitionError("token verification guardian_decision_id mismatch")

        if validated_binding is not None and validated_token is not None:
            if validated_binding.get("token_verification_id") != validated_token.get("token_verification_id"):
                raise GuardianReplayDrillTransitionError("approval binding/token verification mismatch")

        if requested_action is not None and decision is not None and not allow_action_mismatch:
            self._assert_requested_action_matches_decision(decision, requested_action)
            action_binding_id = requested_action.get("approval_binding_id") or requested_action.get("binding_id")
            if validated_binding is not None and action_binding_id is not None and validated_binding.get("binding_id") != action_binding_id:
                raise GuardianReplayDrillTransitionError("requested action approval binding mismatch")
            action_token_id = requested_action.get("token_verification_id")
            if validated_token is not None and action_token_id is not None and validated_token.get("token_verification_id") != action_token_id:
                raise GuardianReplayDrillTransitionError("requested action token verification mismatch")

    @staticmethod
    def _require_bound_first_use_inputs(
        decision: dict[str, Any],
        *,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
    ) -> None:
        required_binding_id = decision.get("approval_binding_id")
        if isinstance(required_binding_id, str) and required_binding_id and approval_binding is None:
            raise GuardianReplayDrillTransitionError("first_use_validated requires approval.binding payload for bound decision")
        required_token_id = decision.get("token_verification_id")
        if isinstance(required_token_id, str) and required_token_id and token_verification is None:
            raise GuardianReplayDrillTransitionError("first_use_validated requires token.verification payload for bound decision")

    @staticmethod
    def _assert_requested_action_matches_decision(decision: dict[str, Any], requested_action: dict[str, Any]) -> None:
        if not isinstance(requested_action, dict):
            raise GuardianReplayDrillTransitionError("requested_action must be a JSON object")
        comparisons = (
            ("tenant_id", "tenant_id", "requested action tenant mismatch"),
            ("customer_context_id", "customer_context_id", "requested action customer context mismatch"),
            ("task_id", "bound_task_id", "requested action task mismatch"),
            ("worker_id", "bound_worker_id", "requested action worker mismatch"),
            ("action_type", "bound_action_type", "requested action action_type mismatch"),
            ("decision_scope_hash", "decision_scope_hash", "requested action decision_scope_hash mismatch"),
        )
        for action_field, decision_field, message in comparisons:
            expected = decision.get(decision_field)
            actual = requested_action.get(action_field)
            if expected is None or actual is None:
                continue
            if expected != actual:
                raise GuardianReplayDrillTransitionError(message)
        decision_scope = decision.get("bound_tool_scope")
        action_scope = requested_action.get("tool_scope")
        if decision_scope is not None and action_scope is not None and decision_scope != action_scope:
            raise GuardianReplayDrillTransitionError("requested action tool_scope mismatch")

    @staticmethod
    def _collect_requested_action_mismatch_categories(
        decision: dict[str, Any], requested_action: dict[str, Any]
    ) -> set[str]:
        categories: set[str] = set()
        if decision.get("bound_tenant_id") is not None and requested_action.get("tenant_id") is not None:
            if decision.get("bound_tenant_id") != requested_action.get("tenant_id"):
                categories.add("tenant_mismatch")
        if decision.get("bound_task_id") is not None and requested_action.get("task_id") is not None:
            if decision.get("bound_task_id") != requested_action.get("task_id"):
                categories.add("task_mismatch")
        if decision.get("bound_worker_id") is not None and requested_action.get("worker_id") is not None:
            if decision.get("bound_worker_id") != requested_action.get("worker_id"):
                categories.add("worker_mismatch")
        if decision.get("bound_action_type") is not None and requested_action.get("action_type") is not None:
            if decision.get("bound_action_type") != requested_action.get("action_type"):
                categories.add("action_type_mismatch")
        if decision.get("decision_scope_hash") is not None and requested_action.get("decision_scope_hash") is not None:
            if decision.get("decision_scope_hash") != requested_action.get("decision_scope_hash"):
                categories.add("decision_scope_hash_mismatch")
        if decision.get("bound_tool_scope") is not None and requested_action.get("tool_scope") is not None:
            if decision.get("bound_tool_scope") != requested_action.get("tool_scope"):
                categories.add("tool_scope_mismatch")
        if decision.get("approval_binding_id") is not None:
            action_binding = requested_action.get("approval_binding_id") or requested_action.get("binding_id")
            if action_binding is not None and action_binding != decision.get("approval_binding_id"):
                categories.add("approval_binding_mismatch")
        if decision.get("token_verification_id") is not None and requested_action.get("token_verification_id") is not None:
            if requested_action.get("token_verification_id") != decision.get("token_verification_id"):
                categories.add("token_verification_mismatch")
        return categories

    def _collect_mismatch_categories(
        self,
        decision: dict[str, Any],
        requested_action: dict[str, Any],
        *,
        approval_binding: dict[str, Any] | None,
        token_verification: dict[str, Any] | None,
    ) -> set[str]:
        categories = self._collect_requested_action_mismatch_categories(decision, requested_action)
        if approval_binding is not None:
            validated_binding = self._validate_contract(approval_binding, "approval.binding")
            required_binding_id = decision.get("approval_binding_id")
            if isinstance(required_binding_id, str) and required_binding_id and validated_binding.get("binding_id") != required_binding_id:
                categories.add("approval_binding_mismatch")
        if token_verification is not None:
            validated_token = self._validate_contract(token_verification, "token.verification")
            required_token_id = decision.get("token_verification_id")
            if isinstance(required_token_id, str) and required_token_id and validated_token.get("token_verification_id") != required_token_id:
                categories.add("token_verification_mismatch")
        return categories

    @staticmethod
    def _extract_guardian_decision_id(payload: dict[str, Any], *, contract_name: str) -> str:
        field = DECISION_ID_FIELD_BY_CONTRACT[contract_name]
        decision_id = payload.get(field)
        if not isinstance(decision_id, str) or not decision_id:
            raise GuardianReplayDrillValidationError("guardian_decision_id is required")
        if contract_name == "guardian.decision":
            canonical_decision_id = payload.get("decision_id")
            if canonical_decision_id != decision_id:
                raise GuardianReplayDrillTransitionError("guardian decision id fields must match")
        return decision_id

    @staticmethod
    def _extract_decision_nonce(payload: dict[str, Any], *, contract_name: str) -> str | None:
        field = NONCE_RESULT_FIELD_BY_CONTRACT[contract_name]
        nonce = payload.get(field)
        if isinstance(nonce, str) and nonce:
            return nonce
        return None

    @staticmethod
    def _assert_evidence_ref_format(ref: str) -> None:
        if not ref.startswith("ev-"):
            raise EvidenceRequiredError("evidence refs must use ev- prefix in replay drill simulator")

    @classmethod
    def _assert_evidence_ref_list(cls, refs: list[Any], *, field_name: str) -> None:
        for value in refs:
            if not isinstance(value, str) or not value:
                raise EvidenceRequiredError(f"{field_name} contains invalid evidence ref")
            cls._assert_evidence_ref_format(value)

    def _tenant_reserved_nonces(self, tenant_id: str) -> set[str]:
        return self._reserved_nonces_by_tenant.setdefault(tenant_id, set())

    def _tenant_consumed_nonces(self, tenant_id: str) -> set[str]:
        return self._consumed_nonces_by_tenant.setdefault(tenant_id, set())

    def _is_decision_expired(self, decision: dict[str, Any]) -> bool:
        reference = self._reference_datetime()
        expires_at = decision.get("expires_at")
        if not isinstance(expires_at, str):
            return False
        try:
            expires = self._parse_datetime(expires_at)
        except GuardianReplayDrillTransitionError:
            return False
        return expires <= reference

    def _is_decision_stale(self, decision: dict[str, Any]) -> bool:
        reference = self._reference_datetime()
        issued_at = decision.get("issued_at")
        if not isinstance(issued_at, str):
            return False
        try:
            issued = self._parse_datetime(issued_at)
        except GuardianReplayDrillTransitionError:
            return False
        max_age = decision.get("max_age_seconds", MAX_GUARDIAN_DECISION_AGE_SECONDS)
        skew = decision.get("clock_skew_allowance_seconds", DEFAULT_GUARDIAN_CLOCK_SKEW_SECONDS)
        if not isinstance(max_age, int) or not isinstance(skew, int):
            return False
        age_seconds = (reference - issued).total_seconds()
        return age_seconds > max_age + skew

    @staticmethod
    def _is_blocked_mvp_decision(decision: dict[str, Any]) -> bool:
        if decision.get("decision") == "block_mvp":
            return True
        if decision.get("replay_policy") == "blocked_mvp":
            return True
        if decision.get("replay_status") == "blocked_mvp":
            return True
        if decision.get("environment") == "blocked_mvp":
            return True
        if decision.get("action_class") in {"connector_access", "outbound_message", "lima_it_remediation"}:
            return True
        if decision.get("bound_action_type") in {"live_connector_access", "external_send", "lima_it_remediation"}:
            return True
        return False

    def _requested_action_from_replay_payload(self, replay_payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "tenant_id": replay_payload.get("tenant_id"),
            "customer_context_id": replay_payload.get("customer_context_id"),
            "task_id": replay_payload.get("task_id"),
            "worker_id": replay_payload.get("worker_id"),
            "guardian_decision_id": replay_payload.get("guardian_decision_id"),
            "approval_binding_id": replay_payload.get("approval_binding_id"),
            "token_verification_id": replay_payload.get("token_verification_id"),
            "action_type": replay_payload.get("action_type"),
            "tool_scope": replay_payload.get("tool_scope"),
            "decision_scope_hash": replay_payload.get("decision_scope_hash"),
            "evidence_required": True,
            "evidence_refs": replay_payload.get("evidence_refs"),
        }

    def _validate_contract(self, payload: dict[str, Any], schema_ref: str) -> dict[str, Any]:
        try:
            return self.validator.validate(copy.deepcopy(payload), schema_ref)
        except Exception as exc:  # pragma: no cover - explicit fail-closed mapping
            raise GuardianReplayDrillValidationError(str(exc)) from exc

    @staticmethod
    def _ensure_known_state(state: str) -> None:
        if state not in DRILL_STATES:
            raise GuardianReplayDrillTransitionError(f"unknown Guardian replay drill state: {state}")

    @staticmethod
    def _assert_state_contract_compatibility(state: str, *, contract_name: str) -> None:
        allowed = STATE_CONTRACT_MAP.get(state)
        if allowed is None:
            raise GuardianReplayDrillTransitionError(f"unsupported Guardian replay drill state for contract mapping: {state}")
        if contract_name not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            raise GuardianReplayDrillTransitionError(
                f"state '{state}' requires contract intent in [{allowed_list}], got '{contract_name}'"
            )

    def _reference_datetime(self) -> datetime:
        if self.reference_time is None:
            raise GuardianReplayDrillTransitionError("reference_time is required for Guardian replay drill simulation")
        return self._parse_datetime(self.reference_time)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise GuardianReplayDrillTransitionError("ambiguous timestamp cannot authorize action") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise GuardianReplayDrillTransitionError("ambiguous timestamp cannot authorize action")
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _updated_at(payload: dict[str, Any]) -> str:
        for key in ("checked_at", "created_at", "issued_at"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return "1970-01-01T00:00:00Z"
