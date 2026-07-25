"""Non-executing Arc worker assignment-preview boundary."""

from __future__ import annotations

import copy
from typing import Any, Protocol

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import UnsafeRuntimeActionError, WorkerStateError


class ArcWorkerPreviewEndpoint(Protocol):
    """The only worker operation exposed by the first control-plane slice."""

    def acknowledge_preview(self, assignment: dict[str, Any]) -> dict[str, Any]:
        """Acknowledge or reject metadata; never execute the assignment."""


class LocalArcWorkerPreviewEndpoint:
    """In-process Arc endpoint used until authenticated transport is added."""

    def __init__(
        self,
        *,
        worker_id: str,
        tenant_id: str,
        capabilities: set[str] | frozenset[str],
        validator: ContractValidator,
        accept_previews: bool = True,
    ) -> None:
        self.worker_id = worker_id
        self.tenant_id = tenant_id
        self.capabilities = frozenset(capabilities)
        self.validator = validator
        self.accept_previews = accept_previews
        self.received_previews: list[dict[str, Any]] = []

    def acknowledge_preview(self, assignment: dict[str, Any]) -> dict[str, Any]:
        assignment = self.validator.validate(
            copy.deepcopy(assignment),
            "worker.assignment.preview",
        )
        self._assert_non_executing(assignment)
        if assignment["worker_id"] != self.worker_id:
            raise WorkerStateError("assignment worker identity mismatch")
        if assignment["tenant_id"] != self.tenant_id:
            raise WorkerStateError("assignment tenant mismatch")
        if assignment["capability"] not in self.capabilities:
            raise WorkerStateError("assignment capability mismatch")

        self.received_previews.append(copy.deepcopy(assignment))
        acknowledged = copy.deepcopy(assignment)
        acknowledged["producer"] = {
            "component": "worker",
            "produced_at": assignment["created_at"],
        }
        acknowledged["status"] = "acknowledged" if self.accept_previews else "rejected"
        acknowledged["acknowledged_at"] = assignment["created_at"]
        return self.validator.validate(acknowledged, "worker.assignment.preview")

    @staticmethod
    def _assert_non_executing(assignment: dict[str, Any]) -> None:
        if assignment.get("runtime_authority_blocked") is not True:
            raise UnsafeRuntimeActionError("Arc assignment must block runtime authority")
        if any(
            assignment.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise UnsafeRuntimeActionError("Arc assignment preview cannot authorize execution")
