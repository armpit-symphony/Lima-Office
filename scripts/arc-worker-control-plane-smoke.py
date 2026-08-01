#!/usr/bin/env python3
"""Run the real non-executing Supervisor-to-Arc control-plane smoke.

The operator-invoked smoke launches Arc as a separate foreground worker
process, provisions one ephemeral channel key over stdin, performs
authenticated registration and heartbeat, requires Guardian and LIMA for a
safe-read request, routes an assignment preview over HTTP, restarts the worker
and SQLite store, verifies durable evidence, and stops. It never invokes a
model, provider, tool, connector, or action.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the authenticated non-executing Arc control-plane smoke."
    )
    parser.add_argument(
        "--arc-source",
        type=Path,
        required=True,
        help="Clean Arc-Bot-shell source tree containing the worker endpoint.",
    )
    return parser


def _start_worker(
    *,
    arc_source: Path,
    replay_db: Path,
    shared_key: bytes,
    boot_id: str,
) -> tuple[subprocess.Popen[str], dict[str, Any]]:
    command = [
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
        boot_id,
        "--key-id",
        "ephemeral-lab-key-001",
        "--policy-version",
        "policy-phase0-v1",
        "--capability",
        "document_read",
        "--capability",
        "it_diagnostics_read_only",
        "--replay-db",
        str(replay_db),
        "--channel-key-stdin",
    ]
    process = subprocess.Popen(
        command,
        cwd=arc_source,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.stdin is None or process.stdout is None:
        _stop_worker(process)
        raise SystemExit("Arc worker process streams are unavailable")
    process.stdin.write(shared_key.hex() + "\n")
    process.stdin.flush()
    process.stdin.close()
    ready_line = process.stdout.readline()
    if not ready_line:
        _stop_worker(process)
        raise SystemExit("Arc worker process did not report readiness")
    try:
        ready = json.loads(ready_line)
    except json.JSONDecodeError as exc:
        _stop_worker(process)
        raise SystemExit("Arc worker readiness record is invalid") from exc
    expected = {
        "status": "ready",
        "host": "127.0.0.1",
        "worker_id": "arc-worker-001",
        "foreground": True,
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
    }
    if any(ready.get(key) != value for key, value in expected.items()):
        _stop_worker(process)
        raise SystemExit("Arc worker readiness boundary failed closed")
    if not isinstance(ready.get("port"), int) or ready["port"] < 1:
        _stop_worker(process)
        raise SystemExit("Arc worker readiness port is invalid")
    return process, ready


def _stop_worker(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _assert_key_not_persisted(paths: tuple[Path, ...], shared_key: bytes) -> None:
    encoded_key = shared_key.hex().encode("ascii")
    for path in paths:
        content = path.read_bytes()
        if shared_key in content or encoded_key in content:
            raise SystemExit("ephemeral Arc channel key was persisted")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    arc_source = args.arc_source.resolve()
    if not (arc_source / "arc_bot_shell" / "control_plane").is_dir():
        raise SystemExit("Arc source does not contain the worker control-plane package")

    from lima_office.contracts import ContractLoader, ContractValidator
    from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
    from lima_office.guardian.authority import GuardianCoreAuthority
    from lima_office.supervisor import (
        AuthenticatedArcWorkerClient,
        AuthenticatedWorkerLifecycleService,
        SupervisorControlPlane,
        WorkerChannel,
        WorkerRegistry,
        load_lima_runner,
    )

    shared_key = secrets.token_bytes(32)
    with tempfile.TemporaryDirectory(prefix="lima-office-arc-smoke-") as temporary:
        evidence_root = Path(temporary)
        supervisor_db = evidence_root / "supervisor.db"
        arc_replay_db = evidence_root / "arc-replay.db"
        validator = ContractValidator(ContractLoader().load())
        channel_args: dict[str, Any] = {
            "tenant_id": "tenant-lab-001",
            "customer_context_id": "customer-context-main",
            "worker_id": "arc-worker-001",
            "key_id": "ephemeral-lab-key-001",
            "shared_key": shared_key,
            "policy_version": "policy-phase0-v1",
        }

        supervisor_store = SQLiteEvidenceStore(supervisor_db, validator)
        worker_process: subprocess.Popen[str] | None = None
        try:
            worker_process, ready = _start_worker(
                arc_source=arc_source,
                replay_db=arc_replay_db,
                shared_key=shared_key,
                boot_id="boot-smoke-001",
            )
            supervisor_channel = WorkerChannel(
                **channel_args,
                validator=validator,
                evidence_store=supervisor_store,
            )
            client = AuthenticatedArcWorkerClient(
                base_url=f"http://127.0.0.1:{ready['port']}",
                channel=supervisor_channel,
                validator=validator,
            )
            registry = WorkerRegistry()
            lifecycle = AuthenticatedWorkerLifecycleService(
                tenant_id="tenant-lab-001",
                customer_context_id="customer-context-main",
                policy_version="policy-phase0-v1",
                validator=validator,
                registry=registry,
                evidence_store=supervisor_store,
            )
            registered = lifecycle.register(client)
            healthy = lifecycle.heartbeat(client)
            control_plane = SupervisorControlPlane(
                tenant_id="tenant-lab-001",
                customer_context_id="customer-context-main",
                authenticated_actors={"operator-lab-001": "operator"},
                validator=validator,
                registry=registry,
                evidence_store=supervisor_store,
                guardian_authority=GuardianCoreAuthority(validator),
                lima_runner=load_lima_runner(),
                worker_endpoints={"arc-worker-001": client},
                require_authenticated_workers=True,
            )
            result = control_plane.submit(
                {
                    "request_id": "request-arc-smoke-001",
                    "tenant_id": "tenant-lab-001",
                    "actor_id": "operator-lab-001",
                    "action": "safe_read",
                    "resource_type": "worker_status",
                    "resource_id": "arc-worker-001",
                    "worker_id": "arc-worker-001",
                    "idempotency_key": "idem-arc-smoke-001",
                }
            )
        finally:
            if worker_process is not None:
                _stop_worker(worker_process)
            supervisor_store.close()

        if result["status"] != "acknowledged":
            raise SystemExit("Arc control-plane assignment was not acknowledged")
        if result["guardian"] is None or result["lima"] is None:
            raise SystemExit("Guardian and LIMA evidence are required")
        if result["lima"]["source_policy"] != "guardian_core.policy":
            raise SystemExit("LIMA static fallback is forbidden")
        if any(
            result[field] is not expected
            for field, expected in (
                ("runtime_authority_blocked", True),
                ("executable", False),
                ("execution_allowed", False),
                ("side_effects_allowed", False),
            )
        ):
            raise SystemExit("control-plane execution boundary failed")

        reopened_store = SQLiteEvidenceStore(supervisor_db, validator)
        restarted_process: subprocess.Popen[str] | None = None
        try:
            restarted_registry = WorkerRegistry()
            restarted_lifecycle = AuthenticatedWorkerLifecycleService(
                tenant_id="tenant-lab-001",
                customer_context_id="customer-context-main",
                policy_version="policy-phase0-v1",
                validator=validator,
                registry=restarted_registry,
                evidence_store=reopened_store,
            )
            restored_workers = restarted_lifecycle.restore()
            restarted_process, restarted_ready = _start_worker(
                arc_source=arc_source,
                replay_db=arc_replay_db,
                shared_key=shared_key,
                boot_id="boot-smoke-002",
            )
            restarted_channel = WorkerChannel(
                **channel_args,
                validator=validator,
                evidence_store=reopened_store,
            )
            restarted_client = AuthenticatedArcWorkerClient(
                base_url=f"http://127.0.0.1:{restarted_ready['port']}",
                channel=restarted_channel,
                validator=validator,
            )
            restarted_worker = restarted_lifecycle.heartbeat(restarted_client)
            reopened_events = reopened_store.events_for_request(
                "request-arc-smoke-001",
                "tenant-lab-001",
            )
            reopened_workers = reopened_store.worker_records("tenant-lab-001")
        finally:
            if restarted_process is not None:
                _stop_worker(restarted_process)
            reopened_store.close()
        _assert_key_not_persisted((supervisor_db, arc_replay_db), shared_key)

        if (
            len(reopened_events) != 6
            or len(reopened_workers) != 1
            or len(restored_workers) != 1
            or restarted_worker.boot_id != "boot-smoke-002"
        ):
            raise SystemExit("worker or evidence restart proof failed closed")

        output = {
            "worker_registration": {
                "worker_id": registered.worker_id,
                "authenticated": registered.authenticated,
                "channel_identity_ref": registered.channel_identity_ref,
            },
            "worker_heartbeat": {
                "initial_state": healthy.state,
                "restarted_state": restarted_worker.state,
                "restarted_boot_id": restarted_worker.boot_id,
                "sequence": restarted_worker.last_heartbeat_sequence,
            },
            "guardian": result["guardian"],
            "lima": result["lima"],
            "assignment": {
                "assignment_id": result["assignment"]["assignment_id"],
                "status": result["assignment"]["status"],
                "worker_id": result["assignment"]["worker_id"],
            },
            "restart_proof": {
                "arc_process_restarted": True,
                "evidence_store_reopened": True,
                "event_types": [event["event_type"] for event in reopened_events],
                "worker_count": len(reopened_workers),
                "worker_state": reopened_workers[0]["state"],
            },
            "transport": {
                "bind": "127.0.0.1",
                "authenticated": True,
                "ephemeral_key_via_stdin": True,
                "public_address_allowed": False,
                "hidden_background_service": False,
            },
            "runtime_authority_blocked": result["runtime_authority_blocked"],
            "executable": result["executable"],
            "execution_allowed": result["execution_allowed"],
            "side_effects_allowed": result["side_effects_allowed"],
        }
        print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
