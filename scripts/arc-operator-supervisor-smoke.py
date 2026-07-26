#!/usr/bin/env python3
"""Run the real foreground Arc operator → Supervisor → Arc lab path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from typing import Any

OFFICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OFFICE_ROOT))

from lima_office.contracts import ContractLoader, ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Launch separate Arc worker and Supervisor processes, submit a real "
            "Arc operator preflight, prove replay rejection and durable evidence."
        )
    )
    parser.add_argument("--arc-source", type=Path, required=True)
    return parser


def _stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _readiness(
    process: subprocess.Popen[str],
    *,
    expected: dict[str, Any],
) -> dict[str, Any]:
    if process.stdout is None:
        _stop(process)
        raise SystemExit("foreground process stdout is unavailable")
    line = process.stdout.readline()
    if not line:
        _stop(process)
        raise SystemExit("foreground process did not report readiness")
    try:
        ready = json.loads(line)
    except json.JSONDecodeError as exc:
        _stop(process)
        raise SystemExit("foreground readiness record is invalid") from exc
    if any(ready.get(key) != value for key, value in expected.items()):
        _stop(process)
        raise SystemExit("foreground readiness boundary failed closed")
    if not isinstance(ready.get("port"), int) or ready["port"] < 1:
        _stop(process)
        raise SystemExit("foreground readiness port is invalid")
    return ready


def _start_worker(
    *,
    arc_source: Path,
    replay_db: Path,
    worker_key: bytes,
) -> tuple[subprocess.Popen[str], dict[str, Any]]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.control_plane.cli",
            "--host",
            "127.0.0.1",
            "--port",
            "0",
            "--tenant-id",
            "tenant-lab-001",
            "--customer-context-id",
            "customer-context-main",
            "--worker-id",
            "arc-worker-001",
            "--worker-role",
            "general_office_arc_worker",
            "--worker-version",
            "arc-bot-shell-0.1.0",
            "--boot-id",
            "boot-operator-smoke-001",
            "--key-id",
            "worker-key-001",
            "--policy-version",
            "guardian-policy-lab-v1",
            "--capability",
            "document_read",
            "--capability",
            "it_diagnostics_read_only",
            "--replay-db",
            str(replay_db),
            "--channel-key-stdin",
        ],
        cwd=arc_source,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.stdin is None:
        _stop(process)
        raise SystemExit("Arc worker stdin is unavailable")
    process.stdin.write(worker_key.hex() + "\n")
    process.stdin.flush()
    process.stdin.close()
    ready = _readiness(
        process,
        expected={
            "status": "ready",
            "host": "127.0.0.1",
            "worker_id": "arc-worker-001",
            "foreground": True,
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        },
    )
    return process, ready


def _start_supervisor(
    *,
    office_source: Path,
    worker_url: str,
    supervisor_db: Path,
    operator_key: bytes,
    worker_key: bytes,
) -> tuple[subprocess.Popen[str], dict[str, Any]]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "lima_office.supervisor.cli",
            "--host",
            "127.0.0.1",
            "--port",
            "0",
            "--tenant-id",
            "tenant-lab-001",
            "--customer-context-id",
            "customer-context-main",
            "--operator-id",
            "operator-lab-001",
            "--operator-key-id",
            "operator-key-001",
            "--worker-id",
            "arc-worker-001",
            "--worker-key-id",
            "worker-key-001",
            "--worker-url",
            worker_url,
            "--evidence-db",
            str(supervisor_db),
            "--policy-version",
            "guardian-policy-lab-v1",
            "--operator-key-stdin",
            "--worker-key-stdin",
        ],
        cwd=office_source,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.stdin is None:
        _stop(process)
        raise SystemExit("Supervisor stdin is unavailable")
    process.stdin.write(operator_key.hex() + "\n")
    process.stdin.write(worker_key.hex() + "\n")
    process.stdin.flush()
    process.stdin.close()
    ready = _readiness(
        process,
        expected={
            "status": "ready",
            "host": "127.0.0.1",
            "operator_id": "operator-lab-001",
            "worker_id": "arc-worker-001",
            "worker_state": "healthy",
            "foreground": True,
            "guardian_required": True,
            "classification_authority": "supervisor_server_derived",
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        },
    )
    return process, ready


def _run_operator(
    *,
    arc_source: Path,
    supervisor_url: str,
    replay_db: Path,
    operator_key: bytes,
    request_id: str,
    idempotency_key: str,
    action: str = "safe_read",
    resource_type: str = "worker_status",
    resource_id: str = "arc-worker-001",
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.control_plane.operator_cli",
            "--supervisor-url",
            supervisor_url,
            "--tenant-id",
            "tenant-lab-001",
            "--customer-context-id",
            "customer-context-main",
            "--operator-id",
            "operator-lab-001",
            "--operator-key-id",
            "operator-key-001",
            "--worker-id",
            "arc-worker-001",
            "--action",
            action,
            "--resource-type",
            resource_type,
            "--resource-id",
            resource_id,
            "--request-id",
            request_id,
            "--idempotency-key",
            idempotency_key,
            "--replay-db",
            str(replay_db),
            "--operator-key-stdin",
        ],
        cwd=arc_source,
        input=operator_key.hex() + "\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"Arc operator preflight failed closed for request {request_id}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("Arc operator result is invalid") from exc


def _assert_non_executing(result: dict[str, Any]) -> None:
    if result.get("runtime_authority_blocked") is not True:
        raise SystemExit("runtime authority was not blocked")
    if any(
        result.get(field) is not False
        for field in ("executable", "execution_allowed", "side_effects_allowed")
    ):
        raise SystemExit("operator result attempted to authorize execution")
    lima = result.get("lima")
    if isinstance(lima, dict):
        if lima.get("source_policy") != "guardian_core.policy":
            raise SystemExit("mandatory Guardian-backed LIMA policy is absent")
        if any(
            lima.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise SystemExit("LIMA result attempted to authorize execution")


def _assert_keys_not_persisted(
    paths: tuple[Path, ...],
    keys: tuple[bytes, ...],
) -> None:
    for path in paths:
        content = path.read_bytes()
        for key in keys:
            if key in content or key.hex().encode("ascii") in content:
                raise SystemExit("ephemeral channel key was persisted")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    arc_source = args.arc_source.resolve()
    office_source = OFFICE_ROOT
    if not (arc_source / "arc_bot_shell" / "control_plane").is_dir():
        raise SystemExit("Arc source lacks the control-plane package")

    operator_key = secrets.token_bytes(32)
    worker_key = secrets.token_bytes(32)
    with tempfile.TemporaryDirectory(prefix="lima-office-operator-smoke-") as raw:
        root = Path(raw)
        supervisor_db = root / "supervisor.db"
        worker_replay_db = root / "worker-replay.db"
        operator_replay_db = root / "operator-replay.db"
        worker_process: subprocess.Popen[str] | None = None
        supervisor_process: subprocess.Popen[str] | None = None
        try:
            worker_process, worker_ready = _start_worker(
                arc_source=arc_source,
                replay_db=worker_replay_db,
                worker_key=worker_key,
            )
            worker_url = f"http://127.0.0.1:{worker_ready['port']}"
            supervisor_process, supervisor_ready = _start_supervisor(
                office_source=office_source,
                worker_url=worker_url,
                supervisor_db=supervisor_db,
                operator_key=operator_key,
                worker_key=worker_key,
            )
            supervisor_url = (
                f"http://127.0.0.1:{supervisor_ready['port']}"
            )
            first = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id="operator-request-001",
                idempotency_key="idem-operator-request-001",
            )
            external_write = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id="operator-request-external-write",
                idempotency_key="idem-operator-request-external-write",
                action="external_write",
                resource_type="external_message",
                resource_id="draft-message-001",
            )
            shell = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id="operator-request-shell",
                idempotency_key="idem-operator-request-shell",
                action="shell",
                resource_type="terminal",
                resource_id="terminal-blocked",
            )
            credential = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id="operator-request-credential",
                idempotency_key="idem-operator-request-credential",
                action="credential_access",
                resource_type="credential_ref",
                resource_id="credential-blocked",
            )
            unknown = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id="operator-request-unknown",
                idempotency_key="idem-operator-request-unknown",
                action="unknown",
                resource_type="unknown",
                resource_id="unknown",
            )
            replay = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id="operator-request-001",
                idempotency_key="idem-operator-request-001",
            )
            _assert_non_executing(first)
            _assert_non_executing(external_write)
            _assert_non_executing(shell)
            _assert_non_executing(credential)
            _assert_non_executing(unknown)
            _assert_non_executing(replay)
            if first["status"] != "acknowledged":
                raise SystemExit("first operator request was not acknowledged")
            if replay["status"] != "denied" or "nonce_replay_denied" not in replay[
                "reason_codes"
            ]:
                raise SystemExit("duplicate operator request was not denied")
            expected_statuses = {
                "external_write": (external_write, "confirm_required"),
                "shell": (shell, "denied"),
                "credential_access": (credential, "privileged_required"),
                "unknown": (unknown, "denied"),
            }
            for name, (result, expected_status) in expected_statuses.items():
                if result["status"] != expected_status:
                    raise SystemExit(
                        f"{name} did not produce the expected governed status"
                    )

            _stop(supervisor_process)
            supervisor_process = None
            supervisor_process, restarted_ready = _start_supervisor(
                office_source=office_source,
                worker_url=worker_url,
                supervisor_db=supervisor_db,
                operator_key=operator_key,
                worker_key=worker_key,
            )
            restarted_url = f"http://127.0.0.1:{restarted_ready['port']}"
            fresh = _run_operator(
                arc_source=arc_source,
                supervisor_url=restarted_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id="operator-request-002",
                idempotency_key="idem-operator-request-002",
            )
            _assert_non_executing(fresh)
            if fresh["status"] != "acknowledged":
                raise SystemExit(
                    "fresh repeated action was incorrectly treated as replay"
                )
        finally:
            if supervisor_process is not None:
                _stop(supervisor_process)
            if worker_process is not None:
                _stop(worker_process)

        validator = ContractValidator(ContractLoader().load())
        reopened = SQLiteEvidenceStore(supervisor_db, validator)
        try:
            first_events = reopened.events_for_request(
                "operator-request-001",
                "tenant-lab-001",
            )
            fresh_events = reopened.events_for_request(
                "operator-request-002",
                "tenant-lab-001",
            )
            workers = reopened.worker_records("tenant-lab-001")
        finally:
            reopened.close()
        _assert_keys_not_persisted(
            (supervisor_db, worker_replay_db, operator_replay_db),
            (operator_key, worker_key),
        )
        if len(first_events) != 8 or len(fresh_events) != 7 or len(workers) != 1:
            raise SystemExit("durable operator evidence restart proof failed")

        output = {
            "operator_request": {
                "status": first["status"],
                "classification_authority": first["classification_authority"],
                "guardian_decision": first["guardian"]["decision"],
                "lima_status": first["lima"]["status"],
                "lima_source_policy": first["lima"]["source_policy"],
                "assignment_status": first["assignment_status"],
                "evidence_event_types": [
                    event["event_type"] for event in first["evidence"]
                ],
            },
            "replay": {
                "status": replay["status"],
                "reason_codes": replay["reason_codes"],
            },
            "decision_matrix": {
                "safe_read": first["status"],
                "external_write": external_write["status"],
                "shell": shell["status"],
                "credential_access": credential["status"],
                "unknown": unknown["status"],
            },
            "restart": {
                "supervisor_restarted": True,
                "fresh_repeated_action_status": fresh["status"],
                "first_request_event_count": len(first_events),
                "fresh_request_event_count": len(fresh_events),
                "worker_count": len(workers),
                "worker_state": workers[0]["state"],
            },
            "transport": {
                "arc_worker_process": "foreground",
                "supervisor_process": "foreground",
                "operator_client": "arc-preflight",
                "loopback_only": True,
                "ephemeral_keys_via_stdin": True,
                "keys_persisted": False,
            },
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
