"""Mock-only approval binding verifier for Phase 1A invariant tests."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.invariants import DEFAULT_REFERENCE_TIME, assert_approval_binding_authorizes_action


class ApprovalBindingVerifier:
    """Validate and consume approval bindings in memory only."""

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

    def verify_once(self, binding: dict[str, Any], requested_action: dict[str, Any]) -> dict[str, Any]:
        """Validate a binding and mark its nonce consumed for this in-memory verifier."""

        validated = self.validator.validate(copy.deepcopy(binding), "approval.binding")
        return copy.deepcopy(
            assert_approval_binding_authorizes_action(
                validated,
                requested_action,
                reference_time=self.reference_time,
                consumed_nonces=self._consumed_nonces,
                consume_nonce=True,
            )
        )

    def check(self, binding: dict[str, Any], requested_action: dict[str, Any]) -> dict[str, Any]:
        """Validate a binding without consuming nonce state."""

        validated = self.validator.validate(copy.deepcopy(binding), "approval.binding")
        return copy.deepcopy(
            assert_approval_binding_authorizes_action(
                validated,
                requested_action,
                reference_time=self.reference_time,
                consumed_nonces=self._consumed_nonces,
                consume_nonce=False,
            )
        )
