#!/usr/bin/env python3
"""Prove the execution grant path end to end, and prove each gate denies.

Runs four scenarios against real Arc and Supervisor processes:

1. both opt-ins on   -> a real document read happens
2. Supervisor opt-in off -> no grant is issued, so nothing runs
3. Arc opt-in off        -> a grant arrives and Arc refuses it
4. no document root      -> Arc opts in but can read nothing

Scenarios 2 to 4 are the point of this script. A gate that has never been
watched failing is not a gate anyone should trust.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from typing import Any


OFFICE_ROOT = Path(__file__).resolve().parents[1]
_SMOKE_PATH = OFFICE_ROOT / "scripts" / "arc-operator-supervisor-smoke.py"

_spec = importlib.util.spec_from_file_location("_arc_operator_smoke", _SMOKE_PATH)
assert _spec is not None and _spec.loader is not None
_smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_smoke)

DOCUMENT_NAME = "quarterly-report.txt"
DOCUMENT_BODY = "Q3 revenue summary for the governed office lab."


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prove a granted read-only document read across LIMA, the "
            "Supervisor, and Arc, and prove each opt-in gate denies."
        )
    )
    parser.add_argument("--arc-source", type=Path, required=True)
    return parser


def _scenario(
    *,
    arc_source: Path,
    root: Path,
    label: str,
    supervisor_opt_in: bool,
    arc_opt_in: bool,
    pass_document_root: bool,
) -> dict[str, Any]:
    operator_key = secrets.token_bytes(32)
    worker_key = secrets.token_bytes(32)
    scenario_root = root / label
    scenario_root.mkdir(parents=True, exist_ok=True)
    documents = scenario_root / "documents"
    documents.mkdir(exist_ok=True)
    (documents / DOCUMENT_NAME).write_text(DOCUMENT_BODY, encoding="utf-8")

    worker_process: subprocess.Popen[str] | None = None
    supervisor_process: subprocess.Popen[str] | None = None
    try:
        worker_process, worker_ready = _smoke._start_worker(
            arc_source=arc_source,
            replay_db=scenario_root / "worker-replay.db",
            worker_key=worker_key,
        )
        supervisor_process, supervisor_ready = _smoke._start_supervisor(
            office_source=OFFICE_ROOT,
            worker_url=f"http://127.0.0.1:{worker_ready['port']}",
            supervisor_db=scenario_root / "supervisor.db",
            operator_key=operator_key,
            worker_key=worker_key,
            execution_opt_in=supervisor_opt_in,
        )
        result = _smoke._run_operator(
            arc_source=arc_source,
            supervisor_url=f"http://127.0.0.1:{supervisor_ready['port']}",
            replay_db=scenario_root / "operator-replay.db",
            operator_key=operator_key,
            request_id=f"request-{label}",
            idempotency_key=f"idem-{label}",
            resource_id=DOCUMENT_NAME,
            execute_granted_capability=arc_opt_in,
            document_root=documents if pass_document_root else None,
        )
    finally:
        for process in (supervisor_process, worker_process):
            if process is not None:
                _smoke._stop(process)

    # The governed decision must never authorize execution, in any scenario.
    _smoke._assert_non_executing(result)
    return result


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"execution grant proof failed: {message}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    arc_source = args.arc_source.resolve()
    if not (arc_source / "arc_bot_shell" / "control_plane").is_dir():
        raise SystemExit("Arc source lacks the control-plane package")

    summary: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="lima-office-grant-smoke-") as raw:
        root = Path(raw)

        # 1. Both gates open: a real read must happen.
        granted = _scenario(
            arc_source=arc_source,
            root=root,
            label="both-opt-in",
            supervisor_opt_in=True,
            arc_opt_in=True,
            pass_document_root=True,
        )
        grant = granted.get("execution_grant")
        execution = granted.get("execution") or {}
        _require(isinstance(grant, dict), "no grant reached Arc with both opt-ins on")
        _require(
            grant.get("granted_capability") == "document_read",
            "grant was not for document_read",
        )
        _require(grant.get("requires_operator_opt_in") is True, "grant waived opt-in")
        _require(execution.get("performed") is True, "the granted read did not happen")
        _require(
            execution.get("byte_count") == len(DOCUMENT_BODY),
            "the read returned an unexpected byte count",
        )
        _require(
            execution.get("side_effects_performed") is False,
            "a side effect was reported during a read-only capability",
        )
        _require(
            DOCUMENT_BODY not in json.dumps(granted),
            "document content leaked into the operator result",
        )
        summary["both_opt_in"] = {
            "grant_issued": True,
            "read_performed": True,
            "byte_count": execution.get("byte_count"),
            "capability": execution.get("capability"),
        }

        # 2. Supervisor gate closed: no grant at all.
        no_grant = _scenario(
            arc_source=arc_source,
            root=root,
            label="supervisor-opt-out",
            supervisor_opt_in=False,
            arc_opt_in=True,
            pass_document_root=True,
        )
        _require(
            no_grant.get("execution_grant") is None,
            "a grant was issued while the Supervisor opt-in was off",
        )
        _require(
            (no_grant.get("execution") or {}).get("performed") is False,
            "a read happened while the Supervisor opt-in was off",
        )
        summary["supervisor_opt_out"] = {
            "grant_issued": False,
            "read_performed": False,
            "reason_code": (no_grant.get("execution") or {}).get("reason_code"),
        }

        # 3. Arc gate closed: the grant arrives and is refused.
        refused = _scenario(
            arc_source=arc_source,
            root=root,
            label="arc-opt-out",
            supervisor_opt_in=True,
            arc_opt_in=False,
            pass_document_root=True,
        )
        refused_execution = refused.get("execution") or {}
        _require(
            isinstance(refused.get("execution_grant"), dict),
            "the Supervisor did not issue a grant in the Arc opt-out scenario",
        )
        _require(
            refused_execution.get("performed") is False,
            "Arc performed a read while its own opt-in was off",
        )
        _require(
            refused_execution.get("reason_code") == "arc_execution_opt_in_disabled",
            "Arc refused for the wrong reason",
        )
        summary["arc_opt_out"] = {
            "grant_issued": True,
            "read_performed": False,
            "reason_code": refused_execution.get("reason_code"),
        }

        # 4. Opted in, but nothing configured to read.
        rootless = _scenario(
            arc_source=arc_source,
            root=root,
            label="no-document-root",
            supervisor_opt_in=True,
            arc_opt_in=True,
            pass_document_root=False,
        )
        rootless_execution = rootless.get("execution") or {}
        _require(
            rootless_execution.get("performed") is False,
            "a read happened without a configured document root",
        )
        _require(
            rootless_execution.get("reason_code") == "document_root_not_configured",
            "the missing document root was refused for the wrong reason",
        )
        summary["no_document_root"] = {
            "read_performed": False,
            "reason_code": rootless_execution.get("reason_code"),
        }

    summary["both_gates_required"] = True
    summary["executable"] = False
    summary["execution_allowed"] = False
    summary["side_effects_allowed"] = False
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
