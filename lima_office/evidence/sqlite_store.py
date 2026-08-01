"""Durable, metadata-only SQLite evidence spine for the lab control plane."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import EvidenceWriteError


_SECRET_PATTERNS = (
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|secret_value|private_key|api_key|provider_token)\b"),
)


class SQLiteEvidenceStore:
    """Persist redacted control-plane evidence without execution payloads."""

    def __init__(
        self,
        path: str | Path,
        validator: ContractValidator,
        *,
        fail_writes: bool = False,
    ) -> None:
        self.path = Path(path)
        self.validator = validator
        self.fail_writes = fail_writes
        if not self.path.parent.is_dir():
            raise EvidenceWriteError(f"evidence directory does not exist: {self.path.parent}")
        try:
            self._connection = sqlite3.connect(self.path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._create_schema()
            self._migrate_request_replay_identity()
        except sqlite3.Error as exc:
            raise EvidenceWriteError("SQLite evidence store is unavailable") from exc

    def close(self) -> None:
        self._connection.close()

    def reserve_request(self, request: dict[str, Any]) -> bool:
        """Reserve request/idempotency/hash identity atomically."""

        request = self.validator.validate(request, "supervisor.control_plane.request")
        self._require_writable()
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO control_plane_requests (
                        request_id,
                        tenant_id,
                        idempotency_key,
                        request_hash,
                        payload_hash,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        request["request_id"],
                        request["tenant_id"],
                        request["idempotency_key"],
                        request["request_hash"],
                        request["payload_hash"],
                        request["received_at"],
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as exc:
            raise EvidenceWriteError("request reservation failed closed") from exc

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event = self.validator.validate(event, "control_plane.event")
        self._require_writable()
        self._validate_redacted(event)
        encoded = json.dumps(event, sort_keys=True, separators=(",", ":"))
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO control_plane_events (
                        event_id,
                        tenant_id,
                        actor_id,
                        worker_id,
                        request_id,
                        decision_id,
                        guardian_decision_id,
                        event_type,
                        parent_event_id,
                        idempotency_key,
                        payload_hash,
                        outcome,
                        created_at,
                        event_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["event_id"],
                        event["tenant_id"],
                        event["actor_id"],
                        event["worker_id"],
                        event["request_id"],
                        event["decision_id"],
                        event["guardian_decision_id"],
                        event["event_type"],
                        event["parent_event_id"],
                        event["idempotency_key"],
                        event["payload_hash"],
                        event["outcome"],
                        event["created_at"],
                        encoded,
                    ),
                )
        except sqlite3.Error as exc:
            raise EvidenceWriteError("evidence event write failed closed") from exc
        return dict(event)

    def events_for_request(self, request_id: str, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT event_json
            FROM control_plane_events
            WHERE request_id = ? AND tenant_id = ?
            ORDER BY sequence_id
            """,
            (request_id, tenant_id),
        ).fetchall()
        return [json.loads(str(row["event_json"])) for row in rows]

    def latest_event_id(self, request_id: str, tenant_id: str) -> str | None:
        row = self._connection.execute(
            """
            SELECT event_id
            FROM control_plane_events
            WHERE request_id = ? AND tenant_id = ?
            ORDER BY sequence_id DESC
            LIMIT 1
            """,
            (request_id, tenant_id),
        ).fetchone()
        return str(row["event_id"]) if row is not None else None

    def reserve_channel_message(self, envelope: dict[str, Any]) -> None:
        """Atomically reject replayed authenticated worker messages."""

        envelope = self.validator.validate(envelope, "worker.channel.envelope")
        self._require_writable()
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO worker_channel_messages (
                        tenant_id,
                        worker_id,
                        key_id,
                        message_id,
                        nonce,
                        message_type,
                        payload_hash,
                        expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        envelope["tenant_id"],
                        envelope["worker_id"],
                        envelope["key_id"],
                        envelope["message_id"],
                        envelope["nonce"],
                        envelope["message_type"],
                        envelope["payload_hash"],
                        envelope["expires_at"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise EvidenceWriteError("authenticated worker message replay rejected") from exc
        except sqlite3.Error as exc:
            raise EvidenceWriteError("worker channel reservation failed closed") from exc

    def reserve_operator_message(self, envelope: dict[str, Any]) -> None:
        """Atomically reject replayed authenticated operator messages."""

        envelope = self.validator.validate(envelope, "operator.channel.envelope")
        self._require_writable()
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO operator_channel_messages (
                        tenant_id,
                        actor_id,
                        key_id,
                        message_id,
                        nonce,
                        message_type,
                        payload_hash,
                        expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        envelope["tenant_id"],
                        envelope["actor_id"],
                        envelope["key_id"],
                        envelope["message_id"],
                        envelope["nonce"],
                        envelope["message_type"],
                        envelope["payload_hash"],
                        envelope["expires_at"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise EvidenceWriteError(
                "authenticated operator message replay rejected"
            ) from exc
        except sqlite3.Error as exc:
            raise EvidenceWriteError(
                "operator channel reservation failed closed"
            ) from exc

    def upsert_worker_record(self, worker: dict[str, Any]) -> None:
        """Persist a redacted worker inventory/health snapshot."""

        forbidden = {"shared_key", "signature", "credentials", "provider_token"}
        if forbidden.intersection(worker):
            raise EvidenceWriteError("worker record contains forbidden credential material")
        self._require_writable()
        encoded = json.dumps(worker, sort_keys=True, separators=(",", ":"))
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO worker_records (
                        tenant_id,
                        worker_id,
                        state,
                        updated_at,
                        worker_json
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (tenant_id, worker_id) DO UPDATE SET
                        state = excluded.state,
                        updated_at = excluded.updated_at,
                        worker_json = excluded.worker_json
                    """,
                    (
                        worker["tenant_id"],
                        worker["worker_id"],
                        worker["state"],
                        worker["updated_at"],
                        encoded,
                    ),
                )
        except (KeyError, sqlite3.Error) as exc:
            raise EvidenceWriteError("worker record write failed closed") from exc

    def worker_records(self, tenant_id: str) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT worker_json
            FROM worker_records
            WHERE tenant_id = ?
            ORDER BY worker_id
            """,
            (tenant_id,),
        ).fetchall()
        return [json.loads(str(row["worker_json"])) for row in rows]

    def _create_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS control_plane_requests (
                    request_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (tenant_id, idempotency_key),
                    UNIQUE (tenant_id, payload_hash)
                );

                CREATE TABLE IF NOT EXISTS control_plane_events (
                    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    tenant_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    worker_id TEXT,
                    request_id TEXT NOT NULL,
                    decision_id TEXT,
                    guardian_decision_id TEXT,
                    event_type TEXT NOT NULL,
                    parent_event_id TEXT,
                    idempotency_key TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    event_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS control_plane_events_request
                ON control_plane_events (tenant_id, request_id, sequence_id);

                CREATE TABLE IF NOT EXISTS worker_channel_messages (
                    tenant_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    key_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, worker_id, key_id, message_id),
                    UNIQUE (tenant_id, worker_id, key_id, nonce)
                );

                CREATE TABLE IF NOT EXISTS worker_records (
                    tenant_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    worker_json TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, worker_id)
                );

                CREATE TABLE IF NOT EXISTS operator_channel_messages (
                    tenant_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    key_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, actor_id, key_id, message_id),
                    UNIQUE (tenant_id, actor_id, key_id, nonce)
                );
                """
            )

    def _migrate_request_replay_identity(self) -> None:
        """Replace the legacy permanent action-hash uniqueness without data loss."""

        row = self._connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'control_plane_requests'
            """
        ).fetchone()
        schema = str(row["sql"]) if row is not None else ""
        normalized = " ".join(schema.split()).lower()
        if "unique (tenant_id, request_hash)" not in normalized:
            return
        try:
            with self._connection:
                self._connection.executescript(
                    """
                    ALTER TABLE control_plane_requests
                    RENAME TO control_plane_requests_legacy;

                    CREATE TABLE control_plane_requests (
                        request_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL,
                        request_hash TEXT NOT NULL,
                        payload_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE (tenant_id, idempotency_key),
                        UNIQUE (tenant_id, payload_hash)
                    );

                    INSERT INTO control_plane_requests (
                        request_id,
                        tenant_id,
                        idempotency_key,
                        request_hash,
                        payload_hash,
                        created_at
                    )
                    SELECT
                        request_id,
                        tenant_id,
                        idempotency_key,
                        request_hash,
                        payload_hash,
                        created_at
                    FROM control_plane_requests_legacy;

                    DROP TABLE control_plane_requests_legacy;
                    """
                )
        except sqlite3.Error as exc:
            raise EvidenceWriteError(
                "request replay identity migration failed closed"
            ) from exc

    def _require_writable(self) -> None:
        if self.fail_writes:
            raise EvidenceWriteError("evidence store write failure injected")

    @staticmethod
    def _validate_redacted(event: dict[str, Any]) -> None:
        summary = str(event.get("redacted_summary") or "")
        if any(pattern.search(summary) for pattern in _SECRET_PATTERNS):
            raise EvidenceWriteError("evidence summary may contain secret material")
        serialized = json.dumps(event, sort_keys=True)
        forbidden_fields = ("raw_prompt", "credentials", "provider_token", "tool_args")
        if any(f'"{field}"' in serialized for field in forbidden_fields):
            raise EvidenceWriteError("evidence event contains a forbidden raw field")
