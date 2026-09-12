"""Authoritative state and controls for the Arc physical-PC test harness.

The browser is a renderer. Mode, training records, routed outcomes, and
evidence live here on the LIMA Office side. The controller accepts only the
already-proven governed document-read path; it never executes an action itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePath, PureWindowsPath
import sqlite3
from threading import RLock
from typing import Any, Mapping, Protocol
import uuid

from lima_office.runtime.escalation import EscalationLadder, default_ladder
from lima_office.runtime.sop import SopGap, operator_authored_gap, training_progress
from lima_office.runtime.task_outcome import TaskAttempt, route_task_outcome


TRAINING_MODE = "training"
WORKING_MODE = "working"
HARNESS_MODES = frozenset({TRAINING_MODE, WORKING_MODE})
DOCUMENT_CAPABILITY = "document_read"
MAX_TEXT_INPUT = 4_000
MAX_REFERENCE_INPUT = 200


class HarnessBoundaryError(ValueError):
    """The requested harness operation crosses a declared safety boundary."""


class GovernedSession(Protocol):
    """The only execution seam the harness may consume."""

    args: Any
    worker_port: int | None
    supervisor_port: int | None

    def request(self, *, action: str, resource_type: str, resource_id: str) -> str:
        """Return the Arc operator CLI result for one governed request."""

    def refresh_workers(self) -> dict[str, Any]:
        """Return the authenticated Supervisor-owned worker inventory."""

    def read_evidence(self, *, target_request_id: str) -> dict[str, Any]:
        """Return one authenticated, redacted Supervisor evidence trace."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _required_text(value: Any, *, name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HarnessBoundaryError(f"{name} must be a non-empty string")
    normalized = value.strip()
    if len(normalized) > limit:
        raise HarnessBoundaryError(f"{name} exceeds {limit} characters")
    return normalized


def _safe_relative_path(value: Any) -> str:
    path = _required_text(value, name="resource_id", limit=MAX_REFERENCE_INPUT)
    candidate = PurePath(path.replace("\\", "/"))
    if path.startswith(("/", "\\")):
        raise HarnessBoundaryError("resource_id must stay inside the document root")
    if candidate.is_absolute() or PureWindowsPath(path).drive or ".." in candidate.parts:
        raise HarnessBoundaryError("resource_id must stay inside the document root")
    if any(part in {"", "."} for part in candidate.parts):
        raise HarnessBoundaryError("resource_id contains an empty path segment")
    return path


def parse_operator_output(output: str) -> tuple[dict[str, Any], str | None]:
    """Split the operator CLI JSON from optional document content."""

    payload_text, marker, remainder = output.partition("--- BEGIN DOCUMENT CONTENT")
    try:
        payload = json.loads(payload_text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise HarnessBoundaryError("Arc operator output was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise HarnessBoundaryError("Arc operator output must be a JSON object")

    content: str | None = None
    if marker:
        body = remainder.split("---", 1)
        content = body[1] if len(body) == 2 else ""
        content = content.rsplit("--- END DOCUMENT CONTENT ---", 1)[0]
        content = content.lstrip("- \r\n").rstrip("\r\n")
    return payload, content


def _reason_codes(payload: Mapping[str, Any]) -> list[str]:
    execution = payload.get("execution")
    execution = execution if isinstance(execution, Mapping) else {}
    codes = [str(code) for code in payload.get("reason_codes") or []]
    for key in ("reason_code",):
        code = execution.get(key)
        if isinstance(code, str) and code and code not in codes:
            codes.append(code)
    return codes


@dataclass(frozen=True)
class HarnessReadResult:
    task_ref: str
    supervisor_status: str | None
    grant_issued: bool
    execution: Mapping[str, Any]
    reason_codes: tuple[str, ...]
    outcome: Mapping[str, Any]
    document_content: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_ref": self.task_ref,
            "supervisor_status": self.supervisor_status,
            "grant_issued": self.grant_issued,
            "execution": dict(self.execution),
            "reason_codes": list(self.reason_codes),
            "outcome": dict(self.outcome),
            "document_content": self.document_content,
        }


class HarnessStateStore:
    """Small durable store for training state and sanitized harness evidence."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sop_gaps (
                    gap_id TEXT PRIMARY KEY,
                    record_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS harness_events (
                    event_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS harness_metrics (
                    metric_name TEXT PRIMARY KEY,
                    metric_value INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS office_task_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    source_helper_result_id TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS office_approval_previews (
                    approval_preview_id TEXT PRIMARY KEY,
                    source_proposal_id TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS office_pending_approval_requests (
                    approval_request_id TEXT PRIMARY KEY,
                    source_approval_preview_id TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS office_approval_results (
                    approval_result_id TEXT PRIMARY KEY,
                    approval_request_id TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL,
                    decided_at TEXT NOT NULL
                );
                """
            )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str:
        event_id = f"harness-event:{uuid.uuid4().hex}"
        encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO harness_events VALUES (?, ?, ?, ?)",
                (event_id, _utc_now(), event_type, encoded),
            )
        return event_id

    def office_approval_preview(self, approval_preview_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT record_json FROM office_approval_previews WHERE approval_preview_id=?",
                (approval_preview_id,),
            ).fetchone()
        return json.loads(row["record_json"]) if row is not None else None

    def office_pending_approval_request_for_preview(
        self, approval_preview_id: str
    ) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT record_json FROM office_pending_approval_requests "
                "WHERE source_approval_preview_id=?",
                (approval_preview_id,),
            ).fetchone()
        return json.loads(row["record_json"]) if row is not None else None

    def office_approval_request(self, approval_request_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT record_json FROM office_pending_approval_requests "
                "WHERE approval_request_id=?", (approval_request_id,)
            ).fetchone()
        return json.loads(row["record_json"]) if row is not None else None

    def office_approval_result_for_request(
        self, approval_request_id: str
    ) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT record_json FROM office_approval_results "
                "WHERE approval_request_id=?", (approval_request_id,)
            ).fetchone()
        return json.loads(row["record_json"]) if row is not None else None

    def office_approval_results(self, limit: int = 50) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 100))
        with self._lock:
            rows = self._connection.execute(
                "SELECT record_json FROM office_approval_results "
                "ORDER BY decided_at DESC, approval_result_id DESC LIMIT ?",
                (bounded_limit,),
            ).fetchall()
        return [json.loads(row["record_json"]) for row in rows]

    def commit_office_non_authorizing_approval_decision(
        self, request: Mapping[str, Any], result: Mapping[str, Any], *,
        expected_request_hash: str, event_id: str, event_type: str,
        event_payload: Mapping[str, Any],
    ) -> str:
        request_record, result_record = dict(request), dict(result)
        request_id = request_record.get("approval_request_id")
        result_id = result_record.get("approval_result_id")
        if not isinstance(request_id, str) or not request_id:
            raise HarnessBoundaryError("approval_request_id is required")
        if not isinstance(result_id, str) or not result_id:
            raise HarnessBoundaryError("approval_result_id is required")
        if result_record.get("approval_request_id") != request_id:
            raise HarnessBoundaryError("approval result request mismatch")
        if not isinstance(expected_request_hash, str) or not expected_request_hash:
            raise HarnessBoundaryError("expected request hash is required")
        if not isinstance(event_id, str) or not event_id.startswith("harness-event:"):
            raise HarnessBoundaryError("a bounded harness event id is required")
        encoded_request = json.dumps(request_record, sort_keys=True, separators=(",", ":"))
        encoded_result = json.dumps(result_record, sort_keys=True, separators=(",", ":"))
        encoded_event = json.dumps(dict(event_payload), sort_keys=True, separators=(",", ":"))
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT record_json FROM office_pending_approval_requests "
                "WHERE approval_request_id=?", (request_id,)
            ).fetchone()
            if row is None:
                raise HarnessBoundaryError("approval request was not found")
            current = json.loads(row["record_json"])
            current_encoded = json.dumps(current, sort_keys=True, separators=(",", ":"))
            current_hash = "sha256:" + hashlib.sha256(current_encoded.encode()).hexdigest()
            if current_hash != expected_request_hash:
                raise HarnessBoundaryError("approval request changed; reload before deciding")
            if current.get("status") != "pending_review":
                raise HarnessBoundaryError("approval request is not pending review")
            existing = self._connection.execute(
                "SELECT 1 FROM office_approval_results WHERE approval_request_id=?",
                (request_id,),
            ).fetchone()
            if existing is not None:
                raise HarnessBoundaryError("approval result already exists")
            self._connection.execute(
                "INSERT INTO harness_events VALUES (?, ?, ?, ?)",
                (event_id, _utc_now(), event_type, encoded_event),
            )
            self._connection.execute(
                "INSERT INTO office_approval_results VALUES (?, ?, ?, ?)",
                (result_id, request_id, encoded_result, result_record["decided_at"]),
            )
            self._connection.execute(
                "UPDATE office_pending_approval_requests SET record_json=? "
                "WHERE approval_request_id=?", (encoded_request, request_id)
            )
        return event_id

    def office_pending_approval_requests(self, limit: int = 50) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 100))
        with self._lock:
            rows = self._connection.execute(
                "SELECT record_json FROM office_pending_approval_requests "
                "ORDER BY created_at DESC, approval_request_id DESC LIMIT ?",
                (bounded_limit,),
            ).fetchall()
        return [json.loads(row["record_json"]) for row in rows]

    def commit_office_pending_approval_request(
        self,
        request: Mapping[str, Any],
        *,
        event_id: str,
        event_type: str,
        event_payload: Mapping[str, Any],
    ) -> str:
        record = dict(request)
        request_id = record.get("approval_request_id")
        preview_id = record.get("source_approval_preview_id")
        if not isinstance(request_id, str) or not request_id:
            raise HarnessBoundaryError("approval_request_id is required")
        if not isinstance(preview_id, str) or not preview_id:
            raise HarnessBoundaryError("source_approval_preview_id is required")
        if not isinstance(event_id, str) or not event_id.startswith("harness-event:"):
            raise HarnessBoundaryError("a bounded harness event id is required")
        encoded_record = json.dumps(record, sort_keys=True, separators=(",", ":"))
        encoded_event = json.dumps(dict(event_payload), sort_keys=True, separators=(",", ":"))
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT 1 FROM office_pending_approval_requests "
                "WHERE approval_request_id=? OR source_approval_preview_id=?",
                (request_id, preview_id),
            ).fetchone()
            if existing is not None:
                raise HarnessBoundaryError("approval request already exists")
            self._connection.execute(
                "INSERT INTO harness_events VALUES (?, ?, ?, ?)",
                (event_id, _utc_now(), event_type, encoded_event),
            )
            self._connection.execute(
                "INSERT INTO office_pending_approval_requests VALUES (?, ?, ?, ?)",
                (request_id, preview_id, encoded_record, _utc_now()),
            )
        return event_id

    def office_approval_previews(self, limit: int = 50) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 100))
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT record_json FROM office_approval_previews
                ORDER BY updated_at DESC, approval_preview_id DESC LIMIT ?
                """,
                (bounded_limit,),
            ).fetchall()
        return [json.loads(row["record_json"]) for row in rows]

    def commit_office_approval_preview(
        self,
        preview: Mapping[str, Any],
        *,
        event_id: str,
        event_type: str,
        event_payload: Mapping[str, Any],
        expected_revision: int | None,
    ) -> str:
        record = dict(preview)
        preview_id = record.get("approval_preview_id")
        source_proposal_id = record.get("source_proposal_id")
        revision = record.get("revision")
        if not isinstance(preview_id, str) or not preview_id:
            raise HarnessBoundaryError("approval_preview_id is required")
        if not isinstance(source_proposal_id, str) or not source_proposal_id:
            raise HarnessBoundaryError("source_proposal_id is required")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise HarnessBoundaryError("approval preview revision must be a positive integer")
        if not isinstance(event_id, str) or not event_id.startswith("harness-event:"):
            raise HarnessBoundaryError("a bounded harness event id is required")
        encoded_record = json.dumps(record, sort_keys=True, separators=(",", ":"))
        encoded_event = json.dumps(
            dict(event_payload), sort_keys=True, separators=(",", ":")
        )
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT revision FROM office_approval_previews WHERE approval_preview_id=?",
                (preview_id,),
            ).fetchone()
            current_revision = int(row["revision"]) if row is not None else None
            if expected_revision is None:
                if current_revision is not None:
                    raise HarnessBoundaryError("approval preview already exists")
            elif current_revision != expected_revision:
                raise HarnessBoundaryError("approval preview revision conflict")
            self._connection.execute(
                "INSERT INTO harness_events VALUES (?, ?, ?, ?)",
                (event_id, _utc_now(), event_type, encoded_event),
            )
            self._connection.execute(
                """
                INSERT INTO office_approval_previews
                    (approval_preview_id, source_proposal_id, record_json, revision, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(approval_preview_id) DO UPDATE SET
                    source_proposal_id=excluded.source_proposal_id,
                    record_json=excluded.record_json,
                    revision=excluded.revision,
                    updated_at=excluded.updated_at
                """,
                (preview_id, source_proposal_id, encoded_record, revision, _utc_now()),
            )
        return event_id

    def office_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT record_json FROM office_task_proposals WHERE proposal_id=?",
                (proposal_id,),
            ).fetchone()
        return json.loads(row["record_json"]) if row is not None else None

    def office_proposals(self, limit: int = 50) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 100))
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT record_json FROM office_task_proposals
                ORDER BY updated_at DESC, proposal_id DESC LIMIT ?
                """,
                (bounded_limit,),
            ).fetchall()
        return [json.loads(row["record_json"]) for row in rows]

    def commit_office_proposal(
        self,
        proposal: Mapping[str, Any],
        *,
        event_id: str,
        event_type: str,
        event_payload: Mapping[str, Any],
        expected_revision: int | None,
    ) -> str:
        proposal_record = dict(proposal)
        proposal_id = proposal_record.get("proposal_id")
        source_helper_result_id = proposal_record.get("source_helper_result_id")
        revision = proposal_record.get("revision")
        if not isinstance(proposal_id, str) or not proposal_id:
            raise HarnessBoundaryError("proposal_id is required")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise HarnessBoundaryError("proposal revision must be a positive integer")
        if not isinstance(source_helper_result_id, str) or not source_helper_result_id:
            raise HarnessBoundaryError("source_helper_result_id is required")
        if not isinstance(event_id, str) or not event_id.startswith("harness-event:"):
            raise HarnessBoundaryError("a bounded harness event id is required")
        encoded_record = json.dumps(
            proposal_record, sort_keys=True, separators=(",", ":")
        )
        encoded_event = json.dumps(
            dict(event_payload), sort_keys=True, separators=(",", ":")
        )
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT revision FROM office_task_proposals WHERE proposal_id=?",
                (proposal_id,),
            ).fetchone()
            current_revision = int(row["revision"]) if row is not None else None
            if expected_revision is None:
                if current_revision is not None:
                    raise HarnessBoundaryError("proposal already exists")
            elif current_revision != expected_revision:
                raise HarnessBoundaryError("proposal revision conflict")
            self._connection.execute(
                "INSERT INTO harness_events VALUES (?, ?, ?, ?)",
                (event_id, _utc_now(), event_type, encoded_event),
            )
            self._connection.execute(
                """
                INSERT INTO office_task_proposals
                    (proposal_id, source_helper_result_id, record_json, revision, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(proposal_id) DO UPDATE SET
                    source_helper_result_id=excluded.source_helper_result_id,
                    record_json=excluded.record_json,
                    revision=excluded.revision,
                    updated_at=excluded.updated_at
                """,
                (proposal_id, source_helper_result_id, encoded_record, revision, _utc_now()),
            )
        return event_id

    def upsert_gap(self, gap: SopGap) -> None:
        encoded = json.dumps(gap.to_dict(), sort_keys=True, separators=(",", ":"))
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO sop_gaps (gap_id, record_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(gap_id) DO UPDATE SET
                    record_json=excluded.record_json,
                    updated_at=excluded.updated_at
                """,
                (gap.gap_id, encoded, _utc_now()),
            )

    @staticmethod
    def _gap_from_json(encoded: str) -> SopGap:
        payload = json.loads(encoded)
        payload.pop("record_type", None)
        payload["reason_codes"] = tuple(payload.get("reason_codes") or ())
        return SopGap(**payload)

    def gaps(self) -> list[SopGap]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT record_json FROM sop_gaps ORDER BY updated_at DESC"
            ).fetchall()
        return [self._gap_from_json(row["record_json"]) for row in rows]

    def instruction_for(self, *, task_ref: str, capability: str) -> str | None:
        for gap in self.gaps():
            if (
                gap.task_ref == task_ref
                and gap.capability == capability
                and gap.status in {"instructed", "retired"}
            ):
                return gap.instruction
        return None

    def increment(self, metric_name: str) -> None:
        if metric_name not in {"completed_alone", "stopped_short"}:
            raise HarnessBoundaryError("unknown harness metric")
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO harness_metrics (metric_name, metric_value)
                VALUES (?, 1)
                ON CONFLICT(metric_name) DO UPDATE SET
                    metric_value=metric_value + 1
                """,
                (metric_name,),
            )

    def metric(self, metric_name: str) -> int:
        with self._lock:
            row = self._connection.execute(
                "SELECT metric_value FROM harness_metrics WHERE metric_name=?",
                (metric_name,),
            ).fetchone()
        return int(row["metric_value"]) if row is not None else 0

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT event_id, occurred_at, event_type, payload_json
                FROM harness_events ORDER BY rowid DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "occurred_at": row["occurred_at"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]


class RuntimeHarness:
    """Mode boundary and governed-session adapter used by the operator UI."""

    def __init__(
        self,
        session: GovernedSession,
        store: HarnessStateStore,
        *,
        ladder: EscalationLadder | None = None,
    ) -> None:
        self.session = session
        self.store = store
        self.ladder = ladder or default_ladder()
        self._mode = TRAINING_MODE
        self._lock = RLock()
        self.store.record_event(
            "harness_started",
            {"mode": self._mode, "working_ready": self.working_ready},
        )

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def working_ready(self) -> bool:
        args = self.session.args
        return bool(
            getattr(args, "execution_opt_in", False)
            and getattr(args, "execute_granted_capability", False)
            and getattr(args, "document_root", None) is not None
        )

    def set_mode(self, mode: Any) -> dict[str, Any]:
        requested = _required_text(mode, name="mode", limit=20).lower()
        if requested not in HARNESS_MODES:
            raise HarnessBoundaryError("mode must be training or working")
        if requested == WORKING_MODE and not self.working_ready:
            raise HarnessBoundaryError(
                "working mode needs both execution opt-ins and a document root "
                "fixed at startup"
            )
        with self._lock:
            previous = self._mode
            self._mode = requested
            event_id = self.store.record_event(
                "mode_changed", {"from": previous, "to": requested}
            )
        return {"mode": self._mode, "evidence_ref": event_id}

    def teach(
        self,
        *,
        task_ref: Any,
        instruction: Any,
        authored_by_role: Any,
    ) -> dict[str, Any]:
        with self._lock:
            if self._mode != TRAINING_MODE:
                raise HarnessBoundaryError("SOP instruction entry requires training mode")
            task = _required_text(
                task_ref, name="task_ref", limit=MAX_REFERENCE_INPUT
            )
            role = _required_text(
                authored_by_role, name="authored_by_role", limit=MAX_REFERENCE_INPUT
            )
            text = _required_text(
                instruction, name="instruction", limit=MAX_TEXT_INPUT
            )
            gap = operator_authored_gap(
                task_ref=task,
                capability=DOCUMENT_CAPABILITY,
                instruction=text,
                authored_by_role=role,
                metadata={"source_surface": "arc_runtime_harness"},
            )
            self.store.upsert_gap(gap)
            event_id = self.store.record_event(
                "sop_instruction_saved",
                {"gap_id": gap.gap_id, "task_ref": task, "capability": DOCUMENT_CAPABILITY},
            )
        response = gap.to_dict()
        response["evidence_ref"] = event_id
        return response

    def governed_read(self, *, task_ref: Any, resource_id: Any) -> dict[str, Any]:
        with self._lock:
            if self._mode != WORKING_MODE:
                raise HarnessBoundaryError("governed reads require working mode")
            task = _required_text(
                task_ref, name="task_ref", limit=MAX_REFERENCE_INPUT
            )
            resource = _safe_relative_path(resource_id)
            raw = self.session.request(
                action="safe_read", resource_type="file", resource_id=resource
            )
            payload, content = parse_operator_output(raw)
            execution_value = payload.get("execution")
            execution = (
                dict(execution_value)
                if isinstance(execution_value, Mapping)
                else {}
            )
            codes = _reason_codes(payload)
            outcome = route_task_outcome(
                TaskAttempt(task_ref=task, capability=DOCUMENT_CAPABILITY),
                performed=bool(execution.get("performed")),
                reason_codes=codes,
                ladder=self.ladder,
                instruction=self.store.instruction_for(
                    task_ref=task, capability=DOCUMENT_CAPABILITY
                ),
                metadata={"resource_ref": resource},
            )
            if outcome.gap is not None:
                self.store.upsert_gap(outcome.gap)
            self.store.increment(
                "completed_alone" if outcome.status == "completed" else "stopped_short"
            )
            event_id = self.store.record_event(
                "governed_read_routed",
                {
                    "task_ref": task,
                    "resource_ref": resource,
                    "outcome_status": outcome.status,
                    "reason_codes": sorted(codes),
                    "performed": bool(execution.get("performed")),
                    "side_effects_performed": bool(
                        execution.get("side_effects_performed", False)
                    ),
                    "decision_id": payload.get("decision_id"),
                },
            )
            result = HarnessReadResult(
                task_ref=task,
                supervisor_status=(str(payload.get("status")) if payload.get("status") is not None else None),
                grant_issued=isinstance(payload.get("execution_grant"), Mapping),
                execution={
                    key: execution.get(key)
                    for key in (
                        "performed", "capability", "byte_count", "reason_code",
                        "content_reason_code", "side_effects_performed",
                    )
                },
                reason_codes=tuple(codes),
                outcome=outcome.to_dict(),
                document_content=content,
            ).to_dict()
            result["evidence_ref"] = event_id
            return result

    def worker_status(self) -> dict[str, Any]:
        with self._lock:
            raw = self.session.request(
                action="status",
                resource_type="worker_status",
                resource_id=str(self.session.args.worker_id),
            )
            payload, _ = parse_operator_output(raw)
            event_id = self.store.record_event(
                "worker_status_checked",
                {"worker_id": str(self.session.args.worker_id), "status": payload.get("status")},
            )
        return {"result": payload, "evidence_ref": event_id}

    def state(self) -> dict[str, Any]:
        gaps = self.store.gaps()
        completed = self.store.metric("completed_alone")
        stopped = self.store.metric("stopped_short")
        observed_gaps = [gap for gap in gaps if gap.source == "escalation"]
        progress = training_progress(
            completed_alone=completed,
            stopped_short=stopped,
            gaps=observed_gaps,
        )
        # Operator-authored instructions teach ahead of failure and therefore
        # do not imply a stopped attempt. They stay visible without changing
        # the measured autonomy denominator.
        progress["gap_count"] = len(gaps)
        progress["open_gaps"] = sum(gap.status == "open" for gap in gaps)
        progress["instructed_gaps"] = sum(gap.status == "instructed" for gap in gaps)
        progress["retired_gaps"] = sum(gap.status == "retired" for gap in gaps)
        args = self.session.args
        return {
            "mode": self._mode,
            "environment": "physical_pc_test",
            "loopback_only": True,
            "working_ready": self.working_ready,
            "gates": {
                "supervisor_execution_opt_in": bool(args.execution_opt_in),
                "arc_execution_opt_in": bool(args.execute_granted_capability),
                "document_root_configured": args.document_root is not None,
            },
            "session": {
                "tenant_id": str(args.tenant_id),
                "worker_id": str(args.worker_id),
                "worker_port": self.session.worker_port,
                "supervisor_port": self.session.supervisor_port,
            },
            "allowed_working_capabilities": [DOCUMENT_CAPABILITY],
            "blocked_capability_classes": [
                "connector_write", "external_send", "file_mutation",
                "network_egress", "remediation", "device_or_robotics_control",
            ],
            "training_progress": progress,
            "gaps": [
                {
                    "gap_id": gap.gap_id,
                    "task_ref": gap.task_ref,
                    "capability": gap.capability,
                    "status": gap.status,
                    "source": gap.source,
                    "reason_codes": sorted(gap.reason_codes),
                    "instruction_present": bool((gap.instruction or "").strip()),
                }
                for gap in gaps
            ],
            "recent_evidence": self.store.recent_events(),
        }
