#!/usr/bin/env python3
"""Prove one foreground Supervisor with 1, 2, or 8 real Arc processes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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


@dataclass
class WorkerProcess:
    worker_id: str
    key_id: str
    key: bytes
    replay_db: Path
    process: subprocess.Popen[str]
    ready: dict[str, Any]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Launch one Supervisor with 1, 2, or 8 separate foreground Arc "
            "workers, then prove non-executing routing and offline isolation."
        )
    )
    parser.add_argument("--arc-source", type=Path, required=True)
    parser.add_argument(
        "--worker-count",
        type=int,
        choices=(1, 2, 8),
        required=True,
    )
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
    root: Path,
    index: int,
) -> WorkerProcess:
    worker_id = f"arc-worker-{index:03d}"
    key_id = f"worker-key-{index:03d}"
    key = secrets.token_bytes(32)
    replay_db = root / f"{worker_id}-replay.db"
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
            worker_id,
            "--worker-role",
            "general_office_arc_worker",
            "--worker-version",
            "arc-bot-shell-0.1.0",
            "--boot-id",
            f"boot-multi-worker-{index:03d}",
            "--key-id",
            key_id,
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
        raise SystemExit(f"{worker_id} stdin is unavailable")
    process.stdin.write(key.hex() + "\n")
    process.stdin.flush()
    process.stdin.close()
    ready = _readiness(
        process,
        expected={
            "status": "ready",
            "host": "127.0.0.1",
            "worker_id": worker_id,
            "foreground": True,
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        },
    )
    return WorkerProcess(
        worker_id=worker_id,
        key_id=key_id,
        key=key,
        replay_db=replay_db,
        process=process,
        ready=ready,
    )


def _start_supervisor(
    *,
    root: Path,
    workers: list[WorkerProcess],
    operator_key: bytes,
) -> tuple[subprocess.Popen[str], dict[str, Any]]:
    command = [
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
        "--evidence-db",
        str(root / "supervisor.db"),
        "--policy-version",
        "guardian-policy-lab-v1",
        "--operator-key-stdin",
        "--worker-key-stdin",
    ]
    for worker in workers:
        command.extend(
            [
                "--worker-binding",
                worker.worker_id,
                worker.key_id,
                f"http://127.0.0.1:{worker.ready['port']}",
            ]
        )
    process = subprocess.Popen(
        command,
        cwd=OFFICE_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.stdin is None:
        _stop(process)
        raise SystemExit("Supervisor stdin is unavailable")
    process.stdin.write(operator_key.hex() + "\n")
    for worker in workers:
        process.stdin.write(worker.key.hex() + "\n")
    process.stdin.flush()
    process.stdin.close()
    ready = _readiness(
        process,
        expected={
            "status": "ready",
            "host": "127.0.0.1",
            "operator_id": "operator-lab-001",
            "worker_count": len(workers),
            "foreground": True,
            "guardian_required": True,
            "classification_authority": "supervisor_server_derived",
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        },
    )
    reported = {
        str(worker["worker_id"]): str(worker["state"])
        for worker in ready.get("workers", [])
        if isinstance(worker, dict)
    }
    expected_workers = {worker.worker_id: "healthy" for worker in workers}
    if reported != expected_workers:
        _stop(process)
        raise SystemExit("Supervisor did not report the complete healthy worker set")
    return process, ready


def _run_operator(
    *,
    arc_source: Path,
    supervisor_url: str,
    replay_db: Path,
    operator_key: bytes,
    worker_id: str,
    request_id: str,
    idempotency_key: str,
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
            worker_id,
            "--action",
            "safe_read",
            "--resource-type",
            "worker_status",
            "--resource-id",
            worker_id,
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
        raise SystemExit(f"Arc preflight failed closed for {request_id}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("Arc operator result is invalid") from exc
    _assert_non_executing(result)
    return result


def _run_inventory(
    *,
    arc_source: Path,
    supervisor_url: str,
    replay_db: Path,
    operator_key: bytes,
    request_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.control_plane.worker_inventory_cli",
            "--refresh",
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
        timeout=30,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Arc worker inventory failed closed for {request_id}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("Arc worker inventory result is invalid") from exc
    _assert_non_executing(result)
    for worker in result.get("workers", []):
        _assert_non_executing(worker)
        if not worker.get("guardian_decision_id") or not worker.get(
            "lima_decision_id"
        ):
            raise SystemExit(
                "Arc inventory worker lacks Guardian/LIMA decision evidence"
            )
    return result


def _run_evidence(
    *,
    arc_source: Path,
    supervisor_url: str,
    replay_db: Path,
    operator_key: bytes,
    target_request_id: str,
    request_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "arc_bot_shell.control_plane.evidence_cli",
            "--read",
            "--target-request-id",
            target_request_id,
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
        timeout=30,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Arc evidence trace failed closed for {request_id}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("Arc evidence trace result is invalid") from exc
    _assert_non_executing(result)
    for event in result.get("events", []):
        _assert_non_executing(event)
        if event.get("request_id") != target_request_id:
            raise SystemExit("Arc evidence trace crossed a request boundary")
    return result


def _assert_non_executing(result: dict[str, Any]) -> None:
    if result.get("runtime_authority_blocked") is not True:
        raise SystemExit("runtime authority was not blocked")
    if any(
        result.get(field) is not False
        for field in (
            "executable",
            "execution_allowed",
            "side_effects_allowed",
        )
    ):
        raise SystemExit("operator result attempted to authorize execution")
    lima = result.get("lima")
    if isinstance(lima, dict):
        if lima.get("source_policy") != "guardian_core.policy":
            raise SystemExit("mandatory Guardian-backed LIMA policy is absent")
        if any(
            lima.get(field) is not False
            for field in (
                "executable",
                "execution_allowed",
                "side_effects_allowed",
            )
        ):
            raise SystemExit("LIMA result attempted to authorize execution")


def _assert_keys_not_persisted(
    paths: list[Path],
    keys: list[bytes],
) -> None:
    for path in paths:
        content = path.read_bytes()
        for key in keys:
            if key in content or key.hex().encode("ascii") in content:
                raise SystemExit("ephemeral channel key was persisted")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    arc_source = args.arc_source.resolve()
    if not (arc_source / "arc_bot_shell" / "control_plane").is_dir():
        raise SystemExit("Arc source lacks the control-plane package")
    operator_key = secrets.token_bytes(32)

    with tempfile.TemporaryDirectory(
        prefix=f"lima-office-{args.worker_count}-worker-smoke-"
    ) as raw:
        root = Path(raw)
        operator_replay_db = root / "operator-replay.db"
        workers: list[WorkerProcess] = []
        supervisor: subprocess.Popen[str] | None = None
        scale_results: dict[str, dict[str, Any]] = {}
        try:
            for index in range(1, args.worker_count + 1):
                workers.append(
                    _start_worker(
                        arc_source=arc_source,
                        root=root,
                        index=index,
                    )
                )
            supervisor, ready = _start_supervisor(
                root=root,
                workers=workers,
                operator_key=operator_key,
            )
            supervisor_url = f"http://127.0.0.1:{ready['port']}"
            initial_inventory = _run_inventory(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id=f"inventory-{args.worker_count}-initial",
                idempotency_key=f"idem-inventory-{args.worker_count}-initial",
            )
            if (
                initial_inventory["status"] != "healthy"
                or initial_inventory["worker_count"] != args.worker_count
                or not all(
                    worker["eligible"]
                    for worker in initial_inventory["workers"]
                )
            ):
                raise SystemExit(
                    "Arc did not display the complete governed healthy inventory"
                )
            for index, worker in enumerate(workers, start=1):
                result = _run_operator(
                    arc_source=arc_source,
                    supervisor_url=supervisor_url,
                    replay_db=operator_replay_db,
                    operator_key=operator_key,
                    worker_id=worker.worker_id,
                    request_id=f"scale-{args.worker_count}-worker-{index:03d}",
                    idempotency_key=(
                        f"idem-scale-{args.worker_count}-worker-{index:03d}"
                    ),
                )
                if result["status"] != "acknowledged":
                    raise SystemExit(
                        f"{worker.worker_id} did not acknowledge its preview"
                    )
                scale_results[worker.worker_id] = result

            _stop(supervisor)
            supervisor = None
            supervisor, ready = _start_supervisor(
                root=root,
                workers=workers,
                operator_key=operator_key,
            )
            supervisor_url = f"http://127.0.0.1:{ready['port']}"
            restart_result = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                worker_id=workers[0].worker_id,
                request_id=f"restart-{args.worker_count}-healthy",
                idempotency_key=f"idem-restart-{args.worker_count}-healthy",
            )
            if restart_result["status"] != "acknowledged":
                raise SystemExit("healthy worker did not survive Supervisor restart")

            evidence_target = f"scale-{args.worker_count}-worker-001"
            evidence_request_id = f"evidence-{args.worker_count}-after-restart"
            evidence_idempotency_key = (
                f"idem-evidence-{args.worker_count}-after-restart"
            )
            evidence_result = _run_evidence(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                target_request_id=evidence_target,
                request_id=evidence_request_id,
                idempotency_key=evidence_idempotency_key,
            )
            expected_event_types = {
                "request_received",
                "guardian_request",
                "guardian_decision",
                "lima_decision",
                "worker_heartbeat",
                "assignment_preview",
                "worker_acknowledgement",
            }
            observed_event_types = {
                event["event_type"] for event in evidence_result["events"]
            }
            if (
                evidence_result["status"] != "available"
                or evidence_result["target_request_id"] != evidence_target
                or not expected_event_types.issubset(observed_event_types)
                or not evidence_result["guardian_decision_id"]
                or not evidence_result["lima_decision_id"]
                or not evidence_result["authorization_evidence_refs"]
            ):
                raise SystemExit(
                    "Arc did not display the durable governed evidence chain "
                    "after Supervisor restart"
                )

            evidence_replay = _run_evidence(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                target_request_id=evidence_target,
                request_id=evidence_request_id,
                idempotency_key=evidence_idempotency_key,
            )
            if (
                evidence_replay["status"] != "denied"
                or evidence_replay["events"]
                or evidence_replay["reason_codes"] != ["nonce_replay_denied"]
            ):
                raise SystemExit("Arc evidence query replay did not fail closed")

            disconnected = workers[-1]
            _stop(disconnected.process)
            offline_result = _run_operator(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                worker_id=disconnected.worker_id,
                request_id=f"offline-{args.worker_count}-worker",
                idempotency_key=f"idem-offline-{args.worker_count}-worker",
            )
            if (
                offline_result["status"] != "blocked"
                or offline_result["reason_codes"] != ["worker_stale"]
            ):
                raise SystemExit("disconnected Arc worker did not fail closed")

            isolation_result: dict[str, Any] | None = None
            if args.worker_count > 1:
                isolation_result = _run_operator(
                    arc_source=arc_source,
                    supervisor_url=supervisor_url,
                    replay_db=operator_replay_db,
                    operator_key=operator_key,
                    worker_id=workers[0].worker_id,
                    request_id=f"isolation-{args.worker_count}-healthy",
                    idempotency_key=f"idem-isolation-{args.worker_count}-healthy",
                )
                if isolation_result["status"] != "acknowledged":
                    raise SystemExit(
                        "one disconnected worker affected a healthy Arc worker"
                    )
            degraded_inventory = _run_inventory(
                arc_source=arc_source,
                supervisor_url=supervisor_url,
                replay_db=operator_replay_db,
                operator_key=operator_key,
                request_id=f"inventory-{args.worker_count}-degraded",
                idempotency_key=f"idem-inventory-{args.worker_count}-degraded",
            )
            visible_states = {
                worker["worker_id"]: worker
                for worker in degraded_inventory["workers"]
            }
            if (
                degraded_inventory["status"] != "degraded_read_only"
                or degraded_inventory["worker_count"] != args.worker_count
                or visible_states[disconnected.worker_id]["eligible"] is not False
                or visible_states[disconnected.worker_id]["state"] != "offline"
                or (
                    args.worker_count > 1
                    and visible_states[workers[0].worker_id]["eligible"] is not True
                )
            ):
                raise SystemExit(
                    "Arc inventory did not isolate the disconnected worker"
                )
        finally:
            if supervisor is not None:
                _stop(supervisor)
            for worker in workers:
                _stop(worker.process)

        validator = ContractValidator(ContractLoader().load())
        store = SQLiteEvidenceStore(root / "supervisor.db", validator)
        try:
            records = store.worker_records("tenant-lab-001")
            offline_events = store.events_for_request(
                f"offline-{args.worker_count}-worker",
                "tenant-lab-001",
            )
            evidence_query_events = store.events_for_request(
                evidence_request_id,
                "tenant-lab-001",
            )
        finally:
            store.close()
        states = {
            str(record["worker_id"]): str(record["state"])
            for record in records
        }
        if len(states) != args.worker_count:
            raise SystemExit("durable worker inventory is incomplete")
        if states[workers[-1].worker_id] != "offline":
            raise SystemExit("disconnected worker state was not durable")
        if (
            args.worker_count > 1
            and states[workers[0].worker_id] != "healthy"
        ):
            raise SystemExit("healthy worker state was not durable")
        if [event["event_type"] for event in offline_events][-2:] != [
            "worker_heartbeat",
            "denial",
        ]:
            raise SystemExit("offline failure evidence chain is incomplete")
        evidence_query_event_types = [
            event["event_type"] for event in evidence_query_events
        ]
        if (
            "evidence_read" not in evidence_query_event_types
            or evidence_query_event_types[-1] != "replay_rejected"
        ):
            raise SystemExit(
                "evidence-read authorization or replay evidence was not durable"
            )

        persisted_paths = [
            root / "supervisor.db",
            operator_replay_db,
            *[worker.replay_db for worker in workers],
        ]
        _assert_keys_not_persisted(
            persisted_paths,
            [operator_key, *[worker.key for worker in workers]],
        )
        output = {
            "worker_count": args.worker_count,
            "scale_statuses": {
                worker_id: result["status"]
                for worker_id, result in scale_results.items()
            },
            "supervisor_restart": "passed",
            "arc_evidence_trace": {
                "status_after_restart": evidence_result["status"],
                "target_request_id": evidence_result["target_request_id"],
                "event_count": evidence_result["event_count"],
                "event_types": sorted(observed_event_types),
                "guardian_lima_authorized": True,
                "arc_acknowledged": True,
                "replay_status": evidence_replay["status"],
                "replay_reason_codes": evidence_replay["reason_codes"],
                "durable_query_event_types": evidence_query_event_types,
                "public_events_redacted": True,
            },
            "arc_worker_inventory": {
                "initial_status": initial_inventory["status"],
                "initial_worker_count": initial_inventory["worker_count"],
                "degraded_status": degraded_inventory["status"],
                "offline_worker_visible": True,
                "healthy_worker_eligible": True,
                "guardian_lima_evidence_present": True,
            },
            "disconnected_worker": {
                "worker_id": workers[-1].worker_id,
                "status": offline_result["status"],
                "reason_codes": offline_result["reason_codes"],
                "durable_state": states[workers[-1].worker_id],
                "evidence_event_types": [
                    event["event_type"] for event in offline_events
                ],
            },
            "healthy_worker_isolation": (
                isolation_result["status"]
                if isolation_result is not None
                else "not_applicable_one_worker"
            ),
            "transport": {
                "loopback_only": True,
                "foreground_supervisor": True,
                "foreground_arc_processes": args.worker_count,
                "ephemeral_keys_via_stdin": True,
                "keys_persisted": False,
                "background_jobs": 0,
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
