"""Mock-only transaction-coordinator transition validator for Phase 1A tests."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import PolicyDenyError


ALLOWED_EVENT_TRANSITIONS: dict[str, set[str]] = {
    "transaction_started": {
        "preconditions_checked",
        "duplicate_request_detected",
        "transaction_failed_closed",
    },
    "preconditions_checked": {
        "replay_nonce_reserved",
        "token_binding_verified",
        "transaction_failed_closed",
    },
    "replay_nonce_reserved": {
        "token_binding_verified",
        "transaction_failed_closed",
    },
    "token_binding_verified": {
        "pre_action_evidence_appended",
        "transaction_failed_closed",
    },
    "pre_action_evidence_appended": {
        "decision_consumed",
        "transaction_failed_closed",
    },
    "decision_consumed": {
        "post_action_evidence_appended",
        "transaction_failed_closed",
    },
    "post_action_evidence_appended": {
        "transaction_committed",
        "transaction_rolled_back",
        "transaction_failed_closed",
    },
    "transaction_committed": {"reconciliation_started"},
    "transaction_rolled_back": {"reconciliation_started"},
    "transaction_failed_closed": {"reconciliation_started"},
    "duplicate_request_detected": {"reconciliation_started"},
    "reconciliation_started": {
        "reconciliation_completed",
        "transaction_failed_closed",
    },
    "reconciliation_completed": set(),
}


class InMemoryTransactionCoordinator:
    """Represents future transaction-coordinator semantics in memory only."""

    def __init__(self, validator: ContractValidator) -> None:
        self.validator = validator
        self._events_by_transaction: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self._event_ids: dict[str, dict[str, Any]] = {}
        self._idempotency_index: dict[tuple[str, str, str], str] = {}

    @property
    def event_log(self) -> dict[tuple[str, str], list[dict[str, Any]]]:
        return copy.deepcopy(self._events_by_transaction)

    @property
    def idempotency_index(self) -> dict[tuple[str, str, str], str]:
        return copy.deepcopy(self._idempotency_index)

    def validate_event(self, event: dict[str, Any]) -> dict[str, Any]:
        validated = self.validator.validate(copy.deepcopy(event), "transaction.coordinator.event")
        self._validate_event_status_alignment(validated)
        return copy.deepcopy(validated)

    def record_event(self, event: dict[str, Any]) -> dict[str, Any]:
        validated = self.validate_event(event)

        event_id = validated["coordinator_event_id"]
        if event_id in self._event_ids:
            existing = self._event_ids[event_id]
            if existing != validated:
                raise PolicyDenyError("coordinator event immutability violation")
            return copy.deepcopy(existing)

        tenant_id = validated["tenant_id"]
        transaction_id = validated["transaction_id"]

        self._check_tenant_scoped_idempotency(validated)

        key = (tenant_id, transaction_id)
        history = self._events_by_transaction.setdefault(key, [])
        self._validate_transition(history, validated)

        self._event_ids[event_id] = copy.deepcopy(validated)
        history.append(copy.deepcopy(validated))
        return copy.deepcopy(validated)

    def _check_tenant_scoped_idempotency(self, event: dict[str, Any]) -> None:
        idempotency_key = (
            event["tenant_id"],
            event["idempotency_scope"],
            event["idempotency_key"],
        )
        transaction_id = event["transaction_id"]
        existing_transaction = self._idempotency_index.get(idempotency_key)
        if existing_transaction is None:
            self._idempotency_index[idempotency_key] = transaction_id
            return
        if existing_transaction != transaction_id:
            raise PolicyDenyError("duplicate idempotency key detected in tenant scope")

    def _validate_transition(self, history: list[dict[str, Any]], event: dict[str, Any]) -> None:
        event_type = event["event_type"]
        previous_event_id = event.get("previous_event_id")

        if not history:
            if event_type != "transaction_started":
                raise PolicyDenyError("first coordinator event must be transaction_started")
            if previous_event_id is not None:
                raise PolicyDenyError("first coordinator event cannot set previous_event_id")
            return

        previous = history[-1]
        previous_type = previous["event_type"]
        allowed = ALLOWED_EVENT_TRANSITIONS.get(previous_type, set())
        if event_type not in allowed:
            raise PolicyDenyError("invalid coordinator event transition")

        expected_previous_id = previous["coordinator_event_id"]
        if previous_event_id is None:
            event["previous_event_id"] = expected_previous_id
        elif previous_event_id != expected_previous_id:
            raise PolicyDenyError("previous_event_id does not match last coordinator event")

        hinted = set(previous.get("next_expected_event_types", []))
        if hinted and event_type not in hinted:
            raise PolicyDenyError("event transition violates next_expected_event_types hint")

    def _validate_event_status_alignment(self, event: dict[str, Any]) -> None:
        event_type = event["event_type"]
        transaction_status = event["transaction_status"]

        if event_type == "transaction_committed" and transaction_status != "committed":
            raise PolicyDenyError("transaction_committed event requires committed status")
        if event_type == "transaction_rolled_back" and transaction_status != "rolled_back":
            raise PolicyDenyError("transaction_rolled_back event requires rolled_back status")
        if event_type == "transaction_failed_closed" and transaction_status != "failed_closed":
            raise PolicyDenyError("transaction_failed_closed event requires failed_closed status")
