"""Operator IDE extensions for the bounded Arc physical runtime harness.

This layer composes the existing governed read harness with Arc-owned queue
projection, explicit human approval evidence, durable SOP resolution, a
customer-shaped escalation ladder, and in-memory document paging.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Any, Mapping, Protocol
import json
import unicodedata
import uuid

from lima_office.guardian.policy import GuardianPolicy
from lima_office.runtime.escalation import EscalationLadder, load_ladder
from lima_office.runtime.operator_harness import (
    HarnessBoundaryError,
    HarnessStateStore,
    RuntimeHarness,
    TRAINING_MODE,
    WORKING_MODE,
    _required_text,
    _reason_codes,
    parse_operator_output,
)
from lima_office.runtime.registration_workflow import (
    RegistrationWorkflowError,
    catalog as registration_catalog,
    run_scenario as run_registration_scenario,
    run_suite as run_registration_suite,
)
from lima_office.runtime.task_outcome import TaskAttempt, route_task_outcome

DOCUMENT_PAGE_CHARS = 8_000
MAX_DOCUMENT_BUFFERS = 4
DOCUMENT_LIST_CAPABILITY = "document_list"
MAX_DOCUMENT_LIST_ENTRIES = 200


def _safe_relative_directory(value: Any) -> str:
    raw = _required_text(value, name="resource_id", limit=200)
    normalized = raw.replace("\\", "/")
    if raw.startswith(("/", "\\")) or ":" in normalized.split("/", 1)[0]:
        raise HarnessBoundaryError("resource_id must stay inside the document root")
    parts = normalized.split("/")
    if normalized == ".":
        return "."
    if any(part in {"", ".", ".."} for part in parts):
        raise HarnessBoundaryError("resource_id must stay inside the document root")
    if any(part.startswith(".") for part in parts):
        raise HarnessBoundaryError("hidden document directories are not listable")
    return "/".join(parts)


def _sanitized_listing_entries(
    execution: Mapping[str, Any],
    *,
    directory: str,
) -> list[dict[str, Any]]:
    entries = execution.get("entries")
    if (
        execution.get("capability") != DOCUMENT_LIST_CAPABILITY
        or execution.get("side_effects_performed") is not False
        or not isinstance(entries, list)
        or len(entries) > MAX_DOCUMENT_LIST_ENTRIES
        or execution.get("entry_count") != len(entries)
        or execution.get("entry_limit") != MAX_DOCUMENT_LIST_ENTRIES
        or not isinstance(execution.get("truncated"), bool)
        or (
            execution.get("truncated") is True
            and len(entries) != MAX_DOCUMENT_LIST_ENTRIES
        )
    ):
        raise HarnessBoundaryError("Arc document listing output was malformed")

    sanitized: list[dict[str, Any]] = []
    prefix = "" if directory == "." else f"{directory}/"
    for value in entries:
        if not isinstance(value, Mapping):
            raise HarnessBoundaryError("Arc document listing output was malformed")
        name = value.get("name")
        kind = value.get("kind")
        byte_count = value.get("byte_count")
        if (
            not isinstance(name, str)
            or not name
            or name in {".", ".."}
            or name.startswith(".")
            or "/" in name
            or "\\" in name
            or any(unicodedata.category(char).startswith("C") for char in name)
            or kind not in {"file", "directory"}
        ):
            raise HarnessBoundaryError("Arc document listing output was malformed")
        if kind == "file":
            if (
                not isinstance(byte_count, int)
                or isinstance(byte_count, bool)
                or byte_count < 0
            ):
                raise HarnessBoundaryError("Arc document listing output was malformed")
        elif byte_count is not None:
            raise HarnessBoundaryError("Arc document listing output was malformed")
        sanitized.append(
            {
                "name": name,
                "relative_path": f"{prefix}{name}",
                "kind": kind,
                "byte_count": byte_count,
            }
        )

    expected = sorted(
        sanitized,
        key=lambda entry: (entry["name"].casefold(), entry["name"]),
    )
    if sanitized != expected or len(
        {item["relative_path"] for item in sanitized}
    ) != len(sanitized):
        raise HarnessBoundaryError("Arc document listing output was malformed")
    return sanitized


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
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS harness_settings (
                    setting_name TEXT PRIMARY KEY,
                    setting_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS registration_practice_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    issue_fields_json TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS registration_mock_reviews (
                    review_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    attempt_id TEXT NOT NULL UNIQUE,
                    scenario_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    guardian_decision_id TEXT,
                    evidence_ref TEXT NOT NULL
                );
                """)

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
        with self._lock:
            row = self._connection.execute(
                "SELECT setting_json FROM harness_settings WHERE setting_name=?",
                (name,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["setting_json"])
        return payload if isinstance(payload, dict) else None

    def record_registration_attempt(
        self, result: Mapping[str, Any]
    ) -> tuple[str, str]:
        """Persist one sanitized practice summary and matching evidence event."""

        from lima_office.runtime.operator_harness import _utc_now

        scenario_id = str(result["scenario_id"])
        score = int(result["score"])
        passed = bool(result["passed"])
        issue_fields = sorted(
            str(issue["field"])
            for issue in result.get("issues", ())
            if isinstance(issue, Mapping) and issue.get("field")
        )
        attempt_id = f"registration-practice:{uuid.uuid4().hex}"
        evidence_ref = f"harness-event:{uuid.uuid4().hex}"
        occurred_at = _utc_now()
        evidence_payload = {
            "attempt_id": attempt_id,
            "scenario_id": scenario_id,
            "score": score,
            "passed": passed,
            "issue_fields": issue_fields,
            "synthetic_data_only": True,
            "submission_allowed": False,
            "external_side_effects": False,
        }
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO registration_practice_attempts
                    (attempt_id, occurred_at, scenario_id, score, passed,
                     issue_fields_json, evidence_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    occurred_at,
                    scenario_id,
                    score,
                    int(passed),
                    json.dumps(issue_fields, separators=(",", ":")),
                    evidence_ref,
                ),
            )
            self._connection.execute(
                "INSERT INTO harness_events VALUES (?, ?, ?, ?)",
                (
                    evidence_ref,
                    occurred_at,
                    "registration_practice_completed",
                    json.dumps(
                        evidence_payload, sort_keys=True, separators=(",", ":")
                    ),
                ),
            )
        return attempt_id, evidence_ref

    def registration_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT attempt_id, occurred_at, scenario_id, score, passed,
                       issue_fields_json, evidence_ref
                FROM registration_practice_attempts WHERE attempt_id=?
                """,
                (attempt_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "attempt_id": row["attempt_id"],
            "occurred_at": row["occurred_at"],
            "scenario_id": row["scenario_id"],
            "score": int(row["score"]),
            "passed": bool(row["passed"]),
            "issue_fields": json.loads(row["issue_fields_json"]),
            "evidence_ref": row["evidence_ref"],
        }

    def registration_review(self, attempt_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT review_id, occurred_at, attempt_id, scenario_id, decision,
                       outcome, guardian_decision_id, evidence_ref
                FROM registration_mock_reviews WHERE attempt_id=?
                """,
                (attempt_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def record_registration_review(
        self,
        *,
        attempt: Mapping[str, Any],
        decision: str,
        outcome: str,
        guardian_decision_id: str | None,
        request_evidence_ref: str,
    ) -> dict[str, Any]:
        """Persist a sanitized human review and localhost mock receipt."""

        from lima_office.runtime.operator_harness import _utc_now

        review_id = f"registration-review:{uuid.uuid4().hex}"
        evidence_ref = f"harness-event:{uuid.uuid4().hex}"
        occurred_at = _utc_now()
        record = {
            "review_id": review_id,
            "occurred_at": occurred_at,
            "attempt_id": str(attempt["attempt_id"]),
            "scenario_id": str(attempt["scenario_id"]),
            "decision": decision,
            "outcome": outcome,
            "guardian_decision_id": guardian_decision_id,
            "evidence_ref": evidence_ref,
            "request_evidence_ref": request_evidence_ref,
            "mock_target": "localhost_test_range",
            "mock_submission_performed": outcome == "mock_submitted",
            "external_submission_allowed": False,
            "external_side_effects": False,
        }
        evidence_payload = {
            key: value
            for key, value in record.items()
            if key not in {"occurred_at", "evidence_ref"}
        }
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO registration_mock_reviews
                    (review_id, occurred_at, attempt_id, scenario_id, decision,
                     outcome, guardian_decision_id, evidence_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    occurred_at,
                    record["attempt_id"],
                    record["scenario_id"],
                    decision,
                    outcome,
                    guardian_decision_id,
                    evidence_ref,
                ),
            )
            self._connection.execute(
                "INSERT INTO harness_events VALUES (?, ?, ?, ?)",
                (
                    evidence_ref,
                    occurred_at,
                    "registration_mock_review_completed",
                    json.dumps(evidence_payload, sort_keys=True, separators=(",", ":")),
                ),
            )
        return record

    def registration_review_summary(self) -> dict[str, int]:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(outcome='mock_submitted'), 0) AS mock_submitted,
                       COALESCE(SUM(outcome='operator_rejected'), 0) AS rejected,
                       COALESCE(SUM(outcome='blocked'), 0) AS blocked
                FROM registration_mock_reviews
                """
            ).fetchone()
        return {
            "review_count": int(row["total"]),
            "mock_submitted_count": int(row["mock_submitted"]),
            "operator_rejected_count": int(row["rejected"]),
            "mock_blocked_count": int(row["blocked"]),
        }

    def registration_attempts(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT attempt_id, occurred_at, scenario_id, score, passed,
                       issue_fields_json, evidence_ref
                FROM registration_practice_attempts
                ORDER BY rowid DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "attempt_id": row["attempt_id"],
                "occurred_at": row["occurred_at"],
                "scenario_id": row["scenario_id"],
                "score": int(row["score"]),
                "passed": bool(row["passed"]),
                "issue_fields": json.loads(row["issue_fields_json"]),
                "evidence_ref": row["evidence_ref"],
            }
            for row in rows
        ]

    def registration_summary(self) -> dict[str, Any]:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(passed), 0) AS passed,
                       COALESCE(ROUND(AVG(score)), 0) AS average_score
                FROM registration_practice_attempts
                """
            ).fetchone()
        total = int(row["total"])
        passed = int(row["passed"])
        return {
            "attempt_count": total,
            "passed_count": passed,
            "failed_count": total - passed,
            "average_score": int(row["average_score"]),
        }


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
            role = _required_text(resolved_by_role, name="resolved_by_role", limit=200)
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

    def registration_catalog(self) -> dict[str, Any]:
        return registration_catalog()

    def run_registration_practice(self, *, scenario_id: Any) -> dict[str, Any]:
        with self._lock:
            if self.mode != TRAINING_MODE:
                raise HarnessBoundaryError(
                    "registration practice requires training mode"
                )
            try:
                result = run_registration_scenario(scenario_id)
            except RegistrationWorkflowError as exc:
                raise HarnessBoundaryError(str(exc)) from exc
            attempt_id, evidence_ref = self.store.record_registration_attempt(result)
        return {**result, "attempt_id": attempt_id, "evidence_ref": evidence_ref}

    def run_registration_practice_suite(self) -> dict[str, Any]:
        with self._lock:
            if self.mode != TRAINING_MODE:
                raise HarnessBoundaryError(
                    "registration practice requires training mode"
                )
            suite = run_registration_suite()
            recorded: list[dict[str, Any]] = []
            for result in suite["results"]:
                attempt_id, evidence_ref = self.store.record_registration_attempt(result)
                recorded.append(
                    {**result, "attempt_id": attempt_id, "evidence_ref": evidence_ref}
                )
            suite_evidence = self.store.record_event(
                "registration_practice_suite_completed",
                {
                    "scenario_count": suite["scenario_count"],
                    "passed_count": suite["passed_count"],
                    "failed_count": suite["failed_count"],
                    "average_score": suite["average_score"],
                    "synthetic_data_only": True,
                    "submission_allowed": False,
                    "external_side_effects": False,
                },
            )
        return {**suite, "results": recorded, "evidence_ref": suite_evidence}

    def review_registration_practice(
        self, *, attempt_id: Any, decision: Any
    ) -> dict[str, Any]:
        """Record human review and optionally create a Guardian-gated mock receipt."""

        with self._lock:
            if self.mode != TRAINING_MODE:
                raise HarnessBoundaryError(
                    "registration mock review requires training mode"
                )
            identifier = _required_text(attempt_id, name="attempt_id", limit=200)
            selected = _required_text(decision, name="decision", limit=20).lower()
            if selected not in {"approved", "rejected"}:
                raise HarnessBoundaryError("decision must be approved or rejected")
            attempt = self.store.registration_attempt(identifier)
            if attempt is None:
                raise HarnessBoundaryError("unknown registration practice attempt")
            if self.store.registration_review(identifier) is not None:
                raise HarnessBoundaryError("registration practice attempt is already reviewed")

            request_evidence_ref = self.store.record_event(
                "registration_mock_review_requested",
                {
                    "attempt_id": identifier,
                    "scenario_id": attempt["scenario_id"],
                    "decision": selected,
                    "issue_fields": list(attempt["issue_fields"]),
                    "synthetic_data_only": True,
                    "mock_target": "localhost_test_range",
                    "external_submission_allowed": False,
                    "external_side_effects": False,
                },
            )
            guardian = None
            if selected == "rejected":
                outcome = "operator_rejected"
            else:
                guardian = GuardianPolicy().decide(
                    "mock_form_submission",
                    {
                        "tenant_id": str(self.session.args.tenant_id),
                        "customer_context_id": "customer-context-main",
                        "execution_mode": "mock_only",
                        "external_effect": "none",
                        "evidence_required": True,
                        "evidence_artifact_ids": [
                            attempt["evidence_ref"],
                            request_evidence_ref,
                        ],
                        "synthetic_data_only": True,
                        "operator_review_decision": selected,
                        "unresolved_issue_count": len(attempt["issue_fields"]),
                        "mock_target": "localhost_test_range",
                    },
                )
                outcome = (
                    "mock_submitted"
                    if guardian["decision"] in {"allow", "allow_with_evidence"}
                    else "blocked"
                )
            record = self.store.record_registration_review(
                attempt=attempt,
                decision=selected,
                outcome=outcome,
                guardian_decision_id=(guardian or {}).get("decision_id"),
                request_evidence_ref=request_evidence_ref,
            )
        return {**record, "guardian_decision": (guardian or {}).get("decision")}

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
            identifier = _required_text(approval_id, name="approval_id", limit=200)
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

    def governed_list(self, *, task_ref: Any, resource_id: Any) -> dict[str, Any]:
        with self._lock:
            if self.mode != WORKING_MODE:
                raise HarnessBoundaryError("governed listings require working mode")
            task = _required_text(task_ref, name="task_ref", limit=200)
            directory = _safe_relative_directory(resource_id)
            raw = self.session.request(
                action="safe_list",
                resource_type="file",
                resource_id=directory,
            )
            payload, _ = parse_operator_output(raw)
            execution_value = payload.get("execution")
            execution = (
                dict(execution_value) if isinstance(execution_value, Mapping) else {}
            )
            codes = _reason_codes(payload)
            performed = bool(execution.get("performed"))
            entries: list[dict[str, Any]] = []
            if performed:
                try:
                    entries = _sanitized_listing_entries(
                        execution,
                        directory=directory,
                    )
                except HarnessBoundaryError:
                    performed = False
                    if "arc_listing_malformed" not in codes:
                        codes.append("arc_listing_malformed")

            outcome = route_task_outcome(
                TaskAttempt(task_ref=task, capability=DOCUMENT_LIST_CAPABILITY),
                performed=performed,
                reason_codes=codes,
                ladder=self.ladder,
                instruction=self.store.instruction_for(
                    task_ref=task,
                    capability=DOCUMENT_LIST_CAPABILITY,
                ),
                metadata={"resource_ref": directory},
            )
            if outcome.gap is not None:
                self.store.upsert_gap(outcome.gap)
            self.store.increment(
                "completed_alone" if outcome.status == "completed" else "stopped_short"
            )
            event_id = self.store.record_event(
                "governed_list_routed",
                {
                    "task_ref": task,
                    "resource_ref": directory,
                    "outcome_status": outcome.status,
                    "reason_codes": sorted(codes),
                    "performed": performed,
                    "entry_count": len(entries),
                    "truncated": (
                        bool(execution.get("truncated", False)) if performed else False
                    ),
                    "side_effects_performed": bool(
                        execution.get("side_effects_performed", False)
                    ),
                    "decision_id": payload.get("decision_id"),
                },
            )
            return {
                "task_ref": task,
                "supervisor_status": (
                    str(payload.get("status"))
                    if payload.get("status") is not None
                    else None
                ),
                "grant_issued": isinstance(
                    payload.get("execution_grant"),
                    Mapping,
                ),
                "execution": {
                    "performed": performed,
                    "capability": (
                        DOCUMENT_LIST_CAPABILITY
                        if performed
                        else execution.get("capability")
                    ),
                    "resource_id": directory,
                    "entry_count": len(entries),
                    "entry_limit": MAX_DOCUMENT_LIST_ENTRIES,
                    "truncated": (
                        bool(execution.get("truncated", False)) if performed else False
                    ),
                    "entries": entries,
                    "reason_code": (
                        "arc_listing_malformed"
                        if "arc_listing_malformed" in codes
                        else execution.get("reason_code")
                    ),
                    "side_effects_performed": bool(
                        execution.get("side_effects_performed", False)
                    ),
                },
                "reason_codes": sorted(codes),
                "outcome": outcome.to_dict(),
                "evidence_ref": event_id,
            }

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
            identifier = _required_text(content_id, name="content_id", limit=200)
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
            state["allowed_working_capabilities"] = [
                DOCUMENT_LIST_CAPABILITY,
                "document_read",
            ]
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
            practice = registration_catalog()
            state["registration_practice"] = {
                **self.store.registration_summary(),
                **self.store.registration_review_summary(),
                "scenario_count": len(practice["scenarios"]),
                "template_count": len(practice["templates"]),
                "recent_attempts": self.store.registration_attempts(limit=10),
                "synthetic_data_only": True,
                "submission_allowed": False,
                "mock_target": "localhost_test_range",
                "mock_submission_available": True,
                "browser_automation_allowed": False,
                "external_side_effects": False,
            }
            return state
