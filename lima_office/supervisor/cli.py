"""Foreground launcher for the authenticated non-executing Supervisor."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import TextIO

from lima_office.contracts import ContractLoader, ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.guardian.authority import GuardianCoreAuthority

from .control_plane import SupervisorControlPlane, load_lima_runner
from .operator_channel import OperatorChannel
from .operator_service import (
    OperatorControlPlaneService,
    build_supervisor_operator_server,
)
from .worker_channel import WorkerChannel
from .worker_client import AuthenticatedArcWorkerClient
from .worker_lifecycle import AuthenticatedWorkerLifecycleService
from .worker_registry import WorkerRegistry


@dataclass(frozen=True)
class WorkerBinding:
    """Non-secret foreground binding for one authenticated Arc worker."""

    worker_id: str
    key_id: str
    base_url: str


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one explicit foreground LIMA Office Supervisor. "
            "The service authenticates non-executing operator preflight requests."
        )
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--customer-context-id", required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--operator-key-id", required=True)
    parser.add_argument("--worker-id")
    parser.add_argument("--worker-key-id")
    parser.add_argument("--worker-url")
    parser.add_argument(
        "--worker-binding",
        action="append",
        nargs=3,
        metavar=("WORKER_ID", "KEY_ID", "LOOPBACK_URL"),
        help=(
            "Bind one Arc worker. Repeat 1-8 times. This cannot be mixed "
            "with the legacy single-worker arguments."
        ),
    )
    parser.add_argument("--evidence-db", type=Path, required=True)
    parser.add_argument(
        "--policy-version",
        default="guardian-policy-lab-v1",
    )
    parser.add_argument(
        "--operator-key-stdin",
        action="store_true",
        required=True,
        help="Read the first hex-encoded ephemeral key line from stdin.",
    )
    parser.add_argument(
        "--worker-key-stdin",
        action="store_true",
        required=True,
        help=(
            "Read one hex-encoded ephemeral worker key per binding from "
            "stdin after the operator key, in binding order."
        ),
    )
    return parser


def _read_key_line(stream: TextIO, label: str) -> bytes:
    encoded = stream.readline().strip()
    if not encoded:
        raise SystemExit(f"{label} key was not provided on stdin")
    try:
        key = bytes.fromhex(encoded)
    except ValueError as exc:
        raise SystemExit(f"{label} key on stdin is not valid hexadecimal") from exc
    finally:
        encoded = ""
    if len(key) < 32:
        raise SystemExit(f"{label} key must contain at least 32 bytes")
    return key


def _worker_bindings(args: argparse.Namespace) -> tuple[WorkerBinding, ...]:
    legacy = (args.worker_id, args.worker_key_id, args.worker_url)
    repeated = args.worker_binding or []
    if repeated and any(value is not None for value in legacy):
        raise SystemExit(
            "--worker-binding cannot be mixed with single-worker arguments"
        )
    if repeated:
        raw_bindings = repeated
    else:
        if any(value is None for value in legacy):
            raise SystemExit(
                "provide one complete single-worker binding or 1-8 "
                "--worker-binding values"
            )
        raw_bindings = [legacy]
    if not 1 <= len(raw_bindings) <= 8:
        raise SystemExit("Supervisor requires 1-8 Arc worker bindings")
    bindings = tuple(
        WorkerBinding(
            worker_id=str(values[0]).strip(),
            key_id=str(values[1]).strip(),
            base_url=str(values[2]).strip(),
        )
        for values in raw_bindings
    )
    if any(
        not binding.worker_id or not binding.key_id or not binding.base_url
        for binding in bindings
    ):
        raise SystemExit("Arc worker binding values cannot be empty")
    for label, values in (
        ("worker IDs", [binding.worker_id for binding in bindings]),
        ("worker key IDs", [binding.key_id for binding in bindings]),
        ("worker URLs", [binding.base_url for binding in bindings]),
    ):
        if len(set(values)) != len(values):
            raise SystemExit(f"Arc {label} must be unique")
    return bindings


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    bindings = _worker_bindings(args)
    operator_key = _read_key_line(sys.stdin, "operator")
    worker_keys = [
        _read_key_line(sys.stdin, f"worker {binding.worker_id}")
        for binding in bindings
    ]
    if len(set(worker_keys)) != len(worker_keys):
        raise SystemExit("Arc worker channel keys must be distinct")
    validator = ContractValidator(ContractLoader().load())
    store = SQLiteEvidenceStore(args.evidence_db, validator)
    try:
        registry = WorkerRegistry()
        lifecycle = AuthenticatedWorkerLifecycleService(
            tenant_id=args.tenant_id,
            customer_context_id=args.customer_context_id,
            policy_version=args.policy_version,
            validator=validator,
            registry=registry,
            evidence_store=store,
        )
        restored = lifecycle.restore()
        configured_ids = {binding.worker_id for binding in bindings}
        restored_ids = {record.worker_id for record in restored}
        unbound_restored = sorted(restored_ids - configured_ids)
        if unbound_restored:
            raise SystemExit(
                "persisted Arc workers are missing explicit bindings: "
                + ", ".join(unbound_restored)
            )
        worker_clients: dict[str, AuthenticatedArcWorkerClient] = {}
        worker_refreshers = {}
        workers = []
        for binding, worker_key in zip(bindings, worker_keys, strict=True):
            worker_channel = WorkerChannel(
                tenant_id=args.tenant_id,
                customer_context_id=args.customer_context_id,
                worker_id=binding.worker_id,
                key_id=binding.key_id,
                shared_key=worker_key,
                validator=validator,
                evidence_store=store,
                policy_version=args.policy_version,
            )
            worker_client = AuthenticatedArcWorkerClient(
                base_url=binding.base_url,
                channel=worker_channel,
                validator=validator,
            )
            worker_clients[binding.worker_id] = worker_client
            worker_refreshers[binding.worker_id] = (
                lambda client=worker_client: lifecycle.heartbeat(client)
            )
            if binding.worker_id not in restored_ids:
                lifecycle.register(worker_client)
            workers.append(lifecycle.heartbeat(worker_client))
        worker_keys.clear()

        operator_channel = OperatorChannel(
            tenant_id=args.tenant_id,
            customer_context_id=args.customer_context_id,
            actor_id=args.operator_id,
            key_id=args.operator_key_id,
            shared_key=operator_key,
            validator=validator,
            evidence_store=store,
            policy_version=args.policy_version,
        )
        control_plane = SupervisorControlPlane(
            tenant_id=args.tenant_id,
            customer_context_id=args.customer_context_id,
            authenticated_actors={args.operator_id: "operator"},
            validator=validator,
            registry=registry,
            evidence_store=store,
            guardian_authority=GuardianCoreAuthority(validator),
            lima_runner=load_lima_runner(),
            worker_endpoints=worker_clients,
            worker_health_refreshers=worker_refreshers,
            policy_version=args.policy_version,
            require_authenticated_workers=True,
        )
        service = OperatorControlPlaneService(
            channel=operator_channel,
            validator=validator,
            control_plane=control_plane,
        )
        server = build_supervisor_operator_server(
            host=args.host,
            port=args.port,
            service=service,
        )
        try:
            ready = {
                "status": "ready",
                "host": args.host,
                "port": server.server_port,
                "tenant_id": args.tenant_id,
                "operator_id": args.operator_id,
                "worker_count": len(workers),
                "workers": [
                    {"worker_id": worker.worker_id, "state": worker.state}
                    for worker in workers
                ],
                "foreground": True,
                "guardian_required": True,
                "classification_authority": "supervisor_server_derived",
                "runtime_authority_blocked": True,
                "executable": False,
                "execution_allowed": False,
                "side_effects_allowed": False,
            }
            if len(workers) == 1:
                ready["worker_id"] = workers[0].worker_id
                ready["worker_state"] = workers[0].state
            print(json.dumps(ready, sort_keys=True), flush=True)
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            return 0
        finally:
            server.server_close()
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
