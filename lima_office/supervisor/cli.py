"""Foreground launcher for the authenticated non-executing Supervisor."""

from __future__ import annotations

import argparse
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
    parser.add_argument("--worker-id", required=True)
    parser.add_argument("--worker-key-id", required=True)
    parser.add_argument("--worker-url", required=True)
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
        help="Read the second hex-encoded ephemeral key line from stdin.",
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


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    operator_key = _read_key_line(sys.stdin, "operator")
    worker_key = _read_key_line(sys.stdin, "worker")
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
        worker_channel = WorkerChannel(
            tenant_id=args.tenant_id,
            customer_context_id=args.customer_context_id,
            worker_id=args.worker_id,
            key_id=args.worker_key_id,
            shared_key=worker_key,
            validator=validator,
            evidence_store=store,
            policy_version=args.policy_version,
        )
        worker_client = AuthenticatedArcWorkerClient(
            base_url=args.worker_url,
            channel=worker_channel,
            validator=validator,
        )
        if not any(record.worker_id == args.worker_id for record in restored):
            lifecycle.register(worker_client)
        worker = lifecycle.heartbeat(worker_client)

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
            worker_endpoints={args.worker_id: worker_client},
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
            print(
                json.dumps(
                    {
                        "status": "ready",
                        "host": args.host,
                        "port": server.server_port,
                        "tenant_id": args.tenant_id,
                        "operator_id": args.operator_id,
                        "worker_id": worker.worker_id,
                        "worker_state": worker.state,
                        "foreground": True,
                        "guardian_required": True,
                        "classification_authority": "supervisor_server_derived",
                        "runtime_authority_blocked": True,
                        "executable": False,
                        "execution_allowed": False,
                        "side_effects_allowed": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
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
