#!/usr/bin/env python3
"""Run the first real non-executing Supervisor-to-Arc control-plane smoke.

This operator-invoked smoke starts an explicit loopback Arc endpoint, performs
authenticated registration and heartbeat, requires Guardian and LIMA for a
safe-read request, routes an assignment preview over HTTP, persists evidence,
and stops. It never invokes a model, provider, tool, connector, or action.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import secrets
import sys
import tempfile
import threading
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


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    arc_source = args.arc_source.resolve()
    if not (arc_source / "arc_bot_shell" / "control_plane").is_dir():
        raise SystemExit("Arc source does not contain the worker control-plane package")
    sys.path.insert(0, str(arc_source))

    from arc_bot_shell.control_plane import (  # noqa: PLC0415
        ArcChannelReplayStore,
        ArcWorkerChannel,
        ArcWorkerPreviewService,
        build_worker_preview_server,
    )
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
        validator = ContractValidator(ContractLoader().load())
        supervisor_store = SQLiteEvidenceStore(
            evidence_root / "supervisor.db",
            validator,
        )
        arc_replay_store = ArcChannelReplayStore(evidence_root / "arc-replay.db")
        with ExitStack() as stack:
            stack.callback(supervisor_store.close)
            stack.callback(arc_replay_store.close)
            channel_args: dict[str, Any] = {
                "tenant_id": "tenant-lab-001",
                "customer_context_id": "customer-context-main",
                "worker_id": "arc-worker-001",
                "key_id": "ephemeral-lab-key-001",
                "shared_key": shared_key,
                "policy_version": "policy-phase0-v1",
            }
            arc_channel = ArcWorkerChannel(
                **channel_args,
                replay_store=arc_replay_store,
            )
            arc_service = ArcWorkerPreviewService(
                channel=arc_channel,
                worker_role="general_office_arc_worker",
                capabilities=("document_read", "it_diagnostics_read_only"),
                worker_version="arc-bot-shell-0.1.0",
                boot_id="boot-smoke-001",
            )
            server = build_worker_preview_server(
                host="127.0.0.1",
                port=0,
                service=arc_service,
            )
            stack.callback(server.server_close)
            server_thread = threading.Thread(
                target=server.serve_forever,
                name="explicit-arc-smoke-server",
            )
            server_thread.start()
            stack.callback(server.shutdown)

            supervisor_channel = WorkerChannel(
                **channel_args,
                validator=validator,
                evidence_store=supervisor_store,
            )
            client = AuthenticatedArcWorkerClient(
                base_url=f"http://127.0.0.1:{server.server_port}",
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

            server.shutdown()
            server_thread.join(timeout=5)
            if server_thread.is_alive():
                raise SystemExit("Arc smoke server did not stop")

            supervisor_store.close()
            reopened_store = SQLiteEvidenceStore(
                evidence_root / "supervisor.db",
                validator,
            )
            try:
                reopened_events = reopened_store.events_for_request(
                    "request-arc-smoke-001",
                    "tenant-lab-001",
                )
                reopened_workers = reopened_store.worker_records(
                    "tenant-lab-001"
                )
            finally:
                reopened_store.close()

            if len(reopened_events) != 6 or len(reopened_workers) != 1:
                raise SystemExit("durable evidence did not survive store restart")

            output = {
                "worker_registration": {
                    "worker_id": registered.worker_id,
                    "authenticated": registered.authenticated,
                    "channel_identity_ref": registered.channel_identity_ref,
                },
                "worker_heartbeat": {
                    "state": healthy.state,
                    "sequence": healthy.last_heartbeat_sequence,
                },
                "guardian": result["guardian"],
                "lima": result["lima"],
                "assignment": {
                    "assignment_id": result["assignment"]["assignment_id"],
                    "status": result["assignment"]["status"],
                    "worker_id": result["assignment"]["worker_id"],
                },
                "evidence_store_reopened": {
                    "event_types": [
                        event["event_type"] for event in reopened_events
                    ],
                    "worker_count": len(reopened_workers),
                    "worker_state": reopened_workers[0]["state"],
                },
                "transport": {
                    "bind": "127.0.0.1",
                    "authenticated": True,
                    "public_address_allowed": False,
                    "hidden_background_service": False,
                },
                "runtime_authority_blocked": result[
                    "runtime_authority_blocked"
                ],
                "executable": result["executable"],
                "execution_allowed": result["execution_allowed"],
                "side_effects_allowed": result["side_effects_allowed"],
            }
            print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
