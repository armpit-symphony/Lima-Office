#!/usr/bin/env python3
"""Drive queued tasks through the governed path and route what comes back.

This is the seam running against real processes. Each task is submitted to a
real Supervisor, which consults the real Guardian and either issues a grant or
denies; the real Arc worker performs the read or refuses. Whatever comes back
is handed to ``route_task_outcome``, which decides whether the task finished,
retries, climbs the ladder, or stops - and records what Arc would need to learn
to not need anyone next time.

Two tasks, chosen because they answer different questions:

1. a document the worker can read -> completes at tier 1, nobody involved
2. a document that is not there   -> a correctable denial, so the task retries
   at the same rung and leaves an SOP gap behind

The second is the one worth running. A task that only ever succeeds proves the
happy path; a task that fails in a way Arc can be taught out of proves the loop
this system exists for.

Running it is also what found ``document_not_found`` unclassified. Every Arc
execution reason code was absent from the registry and therefore forbidden by
default, so a missing file reported as "no rung may permit this" - terminal, no
gap, nothing learned. Correct as a default and wrong as an answer.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import secrets
import sys
import tempfile
from typing import Any


OFFICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OFFICE_ROOT))

_SMOKE_PATH = OFFICE_ROOT / "scripts" / "arc-operator-supervisor-smoke.py"
_spec = importlib.util.spec_from_file_location("_arc_operator_smoke", _SMOKE_PATH)
assert _spec is not None and _spec.loader is not None
_smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_smoke)

from lima_office.runtime.escalation import default_ladder  # noqa: E402
from lima_office.runtime.sop import training_progress  # noqa: E402
from lima_office.runtime.task_outcome import (  # noqa: E402
    TaskAttempt,
    route_task_outcome,
)


DOCUMENT_NAME = "quarterly-report.txt"
DOCUMENT_BODY = "Q3 revenue summary for the governed office lab."


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run queued tasks through the real governed path and route the "
            "results. This command performs only governed reads."
        )
    )
    parser.add_argument("--arc-source", type=Path, required=True)
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the session directory so the evidence database survives.",
    )
    return parser


def _run_task(
    *,
    arc_source: Path,
    root: Path,
    task_ref: str,
    resource_id: str,
) -> dict[str, Any]:
    """One task, one pass through the real Supervisor and the real worker."""

    operator_key = secrets.token_bytes(32)
    worker_key = secrets.token_bytes(32)
    scenario = root / task_ref.replace(":", "-")
    scenario.mkdir(parents=True, exist_ok=True)
    documents = scenario / "documents"
    documents.mkdir(exist_ok=True)
    (documents / DOCUMENT_NAME).write_bytes(DOCUMENT_BODY.encode("utf-8"))

    worker_process = supervisor_process = None
    try:
        worker_process, worker_ready = _smoke._start_worker(
            arc_source=arc_source,
            replay_db=scenario / "worker-replay.db",
            worker_key=worker_key,
        )
        supervisor_process, supervisor_ready = _smoke._start_supervisor(
            office_source=OFFICE_ROOT,
            worker_url=f"http://127.0.0.1:{worker_ready['port']}",
            supervisor_db=scenario / "supervisor.db",
            operator_key=operator_key,
            worker_key=worker_key,
            execution_opt_in=True,
        )
        result = _smoke._run_operator(
            arc_source=arc_source,
            supervisor_url=f"http://127.0.0.1:{supervisor_ready['port']}",
            replay_db=scenario / "operator-replay.db",
            operator_key=operator_key,
            request_id=f"request-{task_ref}",
            idempotency_key=f"idem-{task_ref}",
            resource_id=resource_id,
            execute_granted_capability=True,
            document_root=documents,
        )
    finally:
        for process in (supervisor_process, worker_process):
            if process is not None:
                _smoke._stop(process)

    # The governed decision must never authorize execution, whatever happened.
    _smoke._assert_non_executing(result)
    return result


def _route(result: dict[str, Any], *, task_ref: str) -> Any:
    execution = result.get("execution") or {}
    reason_codes = list(result.get("reason_codes") or [])
    if not reason_codes:
        code = execution.get("reason_code")
        if code:
            reason_codes = [code]
    return route_task_outcome(
        TaskAttempt(task_ref=task_ref, capability="document_read"),
        performed=bool(execution.get("performed")),
        reason_codes=reason_codes,
        ladder=default_ladder(),
    )


def _report(task_ref: str, result: dict[str, Any], outcome: Any) -> None:
    print(f"  task        : {task_ref}")
    print(f"  supervisor  : {result.get('status')}")
    print(f"  outcome     : {outcome.status}")
    if outcome.disposition:
        print(f"  disposition : {outcome.disposition}")
    if outcome.reason_codes:
        print(f"  denied for  : {sorted(outcome.reason_codes)}")
    if outcome.gap is not None:
        print(f"  sop gap     : {outcome.gap.gap_id} ({outcome.gap.status})")
    if outcome.escalation is not None:
        print(f"  escalated to: {outcome.escalation['to']['role']}")
    if outcome.next_attempt is not None:
        print(
            f"  next        : attempt {outcome.next_attempt.attempt} "
            f"at tier {outcome.next_attempt.tier}"
        )
    print(f"  note        : {outcome.note}")
    print()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    arc_source = args.arc_source.expanduser().resolve()
    if not (arc_source / "arc_bot_shell").is_dir():
        raise SystemExit(f"--arc-source does not look like Arc: {arc_source}")

    holder = tempfile.TemporaryDirectory(prefix="arc-task-seam-")
    root = Path(holder.name)
    try:
        print("Governed task seam\n")
        outcomes = []

        print("1. a document the worker can read")
        readable = _run_task(
            arc_source=arc_source,
            root=root,
            task_ref="task:readable",
            resource_id=DOCUMENT_NAME,
        )
        readable_outcome = _route(readable, task_ref="task:readable")
        _report("task:readable", readable, readable_outcome)
        outcomes.append(readable_outcome)

        print("2. a document that is not there")
        missing = _run_task(
            arc_source=arc_source,
            root=root,
            task_ref="task:missing",
            resource_id="no-such-document.txt",
        )
        missing_outcome = _route(missing, task_ref="task:missing")
        _report("task:missing", missing, missing_outcome)
        outcomes.append(missing_outcome)

        completed = sum(1 for o in outcomes if o.status == "completed")
        gaps = [o.gap for o in outcomes if o.gap is not None]
        progress = training_progress(
            completed_alone=completed,
            stopped_short=len(outcomes) - completed,
            gaps=gaps,
        )
        print("training progress")
        print(json.dumps(progress, indent=2, sort_keys=True))

        if not any(o.status == "completed" for o in outcomes):
            raise SystemExit("no task completed; the governed read path is broken")
    finally:
        if args.keep:
            print(f"\nsession kept at {root}")
            holder._finalizer.detach()  # type: ignore[attr-defined]
        else:
            holder.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
