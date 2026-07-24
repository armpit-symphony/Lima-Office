"""Mock-only in-memory replay-store helper for Phase 1A tests."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.invariants import assert_replay_store_record_consistent


class InMemoryReplayStore:
    """Represents future durable replay semantics in memory only."""

    def __init__(self, validator: ContractValidator) -> None:
        self.validator = validator
        self._records_by_id: dict[str, dict[str, Any]] = {}
        self._consumed_nonces: set[str] = set()

    @property
    def records(self) -> dict[str, dict[str, Any]]:
        return copy.deepcopy(self._records_by_id)

    @property
    def consumed_nonces(self) -> frozenset[str]:
        return frozenset(self._consumed_nonces)

    def check_record(
        self,
        record: dict[str, Any],
        *,
        requested_action: dict[str, Any] | None = None,
        guardian_decision: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validated = self.validator.validate(copy.deepcopy(record), "replay.store.record")
        checked = assert_replay_store_record_consistent(
            validated,
            requested_action=requested_action,
            guardian_decision=guardian_decision,
            approval_binding=approval_binding,
            for_authorization=False,
        )
        return copy.deepcopy(checked)

    def authorize_first_use(
        self,
        record: dict[str, Any],
        *,
        requested_action: dict[str, Any] | None = None,
        guardian_decision: dict[str, Any] | None = None,
        approval_binding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validated = self.validator.validate(copy.deepcopy(record), "replay.store.record")
        checked = assert_replay_store_record_consistent(
            validated,
            requested_action=requested_action,
            guardian_decision=guardian_decision,
            approval_binding=approval_binding,
            for_authorization=True,
        )
        nonce = checked.get("decision_nonce")
        if nonce in self._consumed_nonces:
            raise PolicyDenyError("replay store nonce has already been consumed")
        self._consumed_nonces.add(nonce)

        committed = copy.deepcopy(checked)
        committed["nonce_status"] = "consumed"
        committed["atomicity_status"] = "committed"
        committed["consumed_at"] = committed.get("checked_at")
        committed["failure_reason"] = None
        committed["denial_evidence_ref"] = None

        committed = self.validator.validate(committed, "replay.store.record")
        self._records_by_id[committed["replay_record_id"]] = copy.deepcopy(committed)
        return copy.deepcopy(committed)

    def mark_replay_denied(
        self,
        record: dict[str, Any],
        *,
        denial_evidence_ref: str,
    ) -> dict[str, Any]:
        denied = copy.deepcopy(record)
        denied["nonce_status"] = "replay_denied"
        denied["atomicity_status"] = "committed"
        denied["consumed_at"] = None
        denied["denial_evidence_ref"] = denial_evidence_ref
        denied["evidence_refs"] = [denial_evidence_ref]
        denied["failure_reason"] = None
        denied = self.validator.validate(denied, "replay.store.record")
        self._records_by_id[denied["replay_record_id"]] = copy.deepcopy(denied)
        return copy.deepcopy(denied)

    def fail_closed(
        self,
        record: dict[str, Any],
        *,
        failure_reason: str,
        evidence_refs: list[str],
    ) -> dict[str, Any]:
        failed = copy.deepcopy(record)
        failed["nonce_status"] = "failed"
        failed["atomicity_status"] = "failed_closed"
        failed["consumed_at"] = None
        failed["failure_reason"] = failure_reason
        failed["evidence_refs"] = list(evidence_refs)
        failed = self.validator.validate(failed, "replay.store.record")
        self._records_by_id[failed["replay_record_id"]] = copy.deepcopy(failed)
        return copy.deepcopy(failed)
