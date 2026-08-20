"""Operator IDE extensions for the bounded Arc physical runtime harness.

This layer composes the existing governed read harness with Arc-owned queue
projection, explicit human approval evidence, durable SOP resolution, a
customer-shaped escalation ladder, and in-memory document paging.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Any, Mapping, Protocol
import uuid

from lima_office.runtime.escalation import EscalationLadder, load_ladder
from lima_office.runtime.operator_harness import (
    HarnessBoundaryError,
    HarnessStateStore,
    RuntimeHarness,
    TRAINING_MODE,
    WORKING_MODE,
    _required_text,
)


DOCUMENT_PAGE_CHARS = 8_000
MAX_DOCUMENT_BUFFERS = 4


class ArcIDEPort(Protocol):
    """Arc-owned queue/approval operations consumed by the Office surface."""

    def snapshot(self, *, resolved_task_refs: Collection[str] = ()) -> dict[str, Any]:
        """Return Arc's authoritative queue and approval projection."""

    def decide(
        self,
        *,
        approval_id: str,
        decision: str,
        operator_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Record one explicit operator decision without granting execution."""


class OperatorIDEStateStore(HarnessStateStore):
    """Harness state plus durable, non-secret IDE configuration."""

    def __init__(self, path):
        super().__init__(path)
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS harness_settings (
                    setting_name TEXT PRIMARY KEY,
                    setting_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def gap(self, gap_id: str):
        for gap in self.gaps():
            if gap.gap_id == gap_id:
                return gap
        return None

    def resolved_task_refs(self) -> list[str]:
        return sorted(
            {
                gap.task_ref
                for gap in self.gaps()
                if gap.status in {"instructed", "retired"}
            }
        )

    def save_setting(self, name: str, payload: Mapping[str, Any]) -> None:
        from lima_office.runtime.operator_harness import _utc_now
        import json

        encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO harness_settings (setting_name, setting_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(setting_name) DO UPDATE SET
                    setting_json=excluded.setting_json,
                    updated_at=excluded.updated_at
                """,
                (name, encoded, _utc_now()),
            )

    def setting(self, name: str) -> dict[str, Any] | None:
        import json

        with self._lock:
            row = self._connection.execute(
                "SELECT setting_json FROM harness_settings WHERE setting_name=?",
                (name,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["setting_json"])
        return payload if isinstance(payload, dict) else None


class OperatorIDEHarness(RuntimeHarness):
    """Daily-use IDE controls around the already-governed runtime lane."""

    def __init__(
        self,
        session,
        store: OperatorIDEStateStore,
        *,
        arc_ide: ArcIDEPort,
        ladder: EscalationLadder | None = None,
    ) -> None:
        stored = store.setting("escalation_ladder")
        configured = ladder or (load_ladder(stored) if stored is not None else None)
        super().__init__(session, store, ladder=configured)
        self.store: OperatorIDEStateStore = store
        self.arc_ide = arc_ide
        self._documents: dict[str, str] = {}

    def set_mode(self, mode: Any) -> dict[str, Any]:
        result = super().set_mode(mode)
        if result["mode"] == TRAINING_MODE:
            with self._lock:
                self._documents.clear()
        return result

    def resolve_gap(
        self,
        *,
        gap_id: Any,
        instruction: Any,
        resolved_by_role: Any,
    ) -> dict[str, Any]:
        with self._lock:
            if self.mode != TRAINING_MODE:
                raise HarnessBoundaryError("SOP gap resolution requires training mode")
            identifier = _required_text(gap_id, name="gap_id", limit=200)
            gap = self.store.gap(identifier)
            if gap is None:
                raise HarnessBoundaryError("unknown SOP gap")
            if gap.status != "open":
                raise HarnessBoundaryError("only an open SOP gap can be instructed")
            text = _required_text(instruction, name="instruction", limit=4_000)
            role = _required_text(
                resolved_by_role, name="resolved_by_role", limit=200
            )
            instructed = gap.with_instruction(text, resolved_by_role=role)
            self.store.upsert_gap(instructed)
            event_id = self.store.record_event(
                "sop_gap_resolved",
                {
                    "gap_id": instructed.gap_id,
                    "task_ref": instructed.task_ref,
                    "capability": instructed.capability,
                },
            )
        result = instructed.to_dict()
        result["evidence_ref"] = event_id
        result["resolved_task_ref"] = instructed.task_ref
        return result

    def configure_ladder(self, payload: Any) -> dict[str, Any]:
        with self._lock:
            if self.mode != TRAINING_MODE:
                raise HarnessBoundaryError(
                    "escalation ladder configuration requires training mode"
                )
            ladder = load_ladder(payload)
            rendered = ladder.to_dict()
            self.store.save_setting("escalation_ladder", {"tiers": rendered["tiers"]})
            self.ladder = ladder
            event_id = self.store.record_event(
                "escalation_ladder_configured",
                {
                    "tier_count": rendered["tier_count"],
                    "terminal_role": rendered["terminal_role"],
                },
            )
        return {**rendered, "evidence_ref": event_id}

    def decide_approval(
        self,
        *,
        approval_id: Any,
        decision: Any,
        operator_id: Any,
        reason: Any,
    ) -> dict[str, Any]:
        with self._lock:
            if self.mode != WORKING_MODE:
                raise HarnessBoundaryError(
                    "approval decisions require working mode and explicit operator intent"
                )
            identifier = _required_text(
                approval_id, name="approval_id", limit=200
            )
            selected = _required_text(decision, name="decision", limit=20).lower()
            if selected not in {"approved", "denied"}:
                raise HarnessBoundaryError("decision must be approved or denied")
            operator = _required_text(operator_id, name="operator_id", limit=200)
            explanation = _required_text(reason, name="reason", limit=4_000)
            try:
                result = self.arc_ide.decide(
                    approval_id=identifier,
                    decision=selected,
                    operator_id=operator,
                    reason=explanation,
                )
            except (RuntimeError, ValueError, OSError) as exc:
                raise HarnessBoundaryError(str(exc)) from exc
            event_id = self.store.record_event(
                "operator_approval_decided",
                {
                    "approval_id": identifier,
                    "decision": selected,
                    "operator_id": operator,
                    "execution_allowed": False,
                },
            )
        result["evidence_ref"] = event_id
        return result

    def governed_read(self, *, task_ref: Any, resource_id: Any) -> dict[str, Any]:
        result = super().governed_read(task_ref=task_ref, resource_id=resource_id)
        content = result.pop("document_content", None)
        if content is None:
            result["document_page"] = None
            return result
        content_id = f"document-buffer:{uuid.uuid4().hex}"
        with self._lock:
            self._documents[content_id] = content
            while len(self._documents) > MAX_DOCUMENT_BUFFERS:
                self._documents.pop(next(iter(self._documents)))
        page = self._page(content_id, 0)
        result["document_content"] = page["content"]
        result["document_page"] = page
        return result

    def _page(self, content_id: str, offset: int) -> dict[str, Any]:
        content = self._documents.get(content_id)
        if content is None:
            raise HarnessBoundaryError(
                "document page is no longer in memory; run the governed read again"
            )
        if offset < 0 or offset > len(content):
            raise HarnessBoundaryError("document page offset is outside the result")
        end = min(len(content), offset + DOCUMENT_PAGE_CHARS)
        return {
            "content_id": content_id,
            "content": content[offset:end],
            "offset": offset,
            "next_offset": end if end < len(content) else None,
            "has_more": end < len(content),
            "page_number": (offset // DOCUMENT_PAGE_CHARS) + 1,
            "char_count": end - offset,
            "total_chars": len(content),
            "persistence": "process_memory_only",
        }

    def document_page(self, *, content_id: Any, offset: Any) -> dict[str, Any]:
        with self._lock:
            if self.mode != WORKING_MODE:
                raise HarnessBoundaryError("document paging requires working mode")
            identifier = _required_text(
                content_id, name="content_id", limit=200
            )
            if not isinstance(offset, int) or isinstance(offset, bool):
                raise HarnessBoundaryError("offset must be an integer")
            page = self._page(identifier, offset)
            event_id = self.store.record_event(
                "document_page_viewed",
                {
                    "content_id": identifier,
                    "offset": offset,
                    "char_count": page["char_count"],
                },
            )
        return {**page, "evidence_ref": event_id}

    def state(self) -> dict[str, Any]:
        with self._lock:
            state = super().state()
            try:
                queue = self.arc_ide.snapshot(
                    resolved_task_refs=self.store.resolved_task_refs()
                )
            except (RuntimeError, ValueError, OSError) as exc:
                queue = {
                    "record_type": "arc_operator_ide_snapshot",
                    "unavailable": True,
                    "error": type(exc).__name__,
                    "tasks": [],
                    "pending_approvals": [],
                    "next_task": None,
                }
            state["operator_ide"] = queue
            state["escalation_ladder"] = self.ladder.to_dict()
            state["document_paging"] = {
                "page_chars": DOCUMENT_PAGE_CHARS,
                "persistence": "process_memory_only",
                "buffer_count": len(self._documents),
            }
            return state
