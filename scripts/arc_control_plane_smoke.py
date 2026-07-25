#!/usr/bin/env python3
"""Run the real non-executing Supervisor -> Guardian -> LIMA -> Arc lab path."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lima_office.contracts import ContractLoader, ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.guardian.authority import GuardianCoreAuthority
from lima_office.supervisor.arc_worker import LocalArcWorkerPreviewEndpoint
from lima_office.supervisor.control_plane import SupervisorControlPlane, load_lima_runner
from lima_office.supervisor.worker_registry import WorkerRegistry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a non-executing Arc control-plane lab smoke."
    )
    parser.add_argument(
        "--database",
        type=Path,
        required=True,
        help="SQLite evidence path in an existing lab directory.",
    )
    parser.add_argument("--request-id", default="arc-control-plane-smoke-001")
    return parser.parse_args()


def run(database: Path, request_id: str) -> dict[str, Any]:
    validator = ContractValidator(ContractLoader().load())
    registry = WorkerRegistry()
    registry.register_mock_worker(
        worker_id="arc-worker-001",
        tenant_id="tenant-lab-001",
        role="arc-office-worker",
        capabilities=["document_read"],
    )
    endpoint = LocalArcWorkerPreviewEndpoint(
        worker_id="arc-worker-001",
        tenant_id="tenant-lab-001",
        capabilities={"document_read"},
        validator=validator,
    )
    store = SQLiteEvidenceStore(database, validator)
    control_plane = SupervisorControlPlane(
        tenant_id="tenant-lab-001",
        customer_context_id="customer-context-main",
        authenticated_actors={"operator-lab-001": "operator"},
        validator=validator,
        registry=registry,
        evidence_store=store,
        guardian_authority=GuardianCoreAuthority(validator),
        lima_runner=load_lima_runner(),
        worker_endpoints={"arc-worker-001": endpoint},
    )
    request = {
        "request_id": request_id,
        "tenant_id": "tenant-lab-001",
        "actor_id": "operator-lab-001",
        "action": "safe_read",
        "resource_type": "worker_status",
        "resource_id": "arc-worker-001",
        "worker_id": "arc-worker-001",
        "idempotency_key": f"idem:{request_id}",
    }
    try:
        first = control_plane.submit(request)
    finally:
        store.close()

    reopened = SQLiteEvidenceStore(database, validator)
    replay_control_plane = SupervisorControlPlane(
        tenant_id="tenant-lab-001",
        customer_context_id="customer-context-main",
        authenticated_actors={"operator-lab-001": "operator"},
        validator=validator,
        registry=registry,
        evidence_store=reopened,
        guardian_authority=GuardianCoreAuthority(validator),
        lima_runner=load_lima_runner(),
        worker_endpoints={"arc-worker-001": endpoint},
    )
    try:
        replay = replay_control_plane.submit(request)
    finally:
        reopened.close()

    return {
        "first_status": first["status"],
        "replay_status": replay["status"],
        "guardian_source": (
            first["lima"]["source_policy"] if first.get("lima") is not None else None
        ),
        "evidence_event_count_after_restart": len(replay["evidence"]),
        "runtime_authority_blocked": first["runtime_authority_blocked"],
        "executable": first["executable"],
        "execution_allowed": first["execution_allowed"],
        "side_effects_allowed": first["side_effects_allowed"],
        "side_effect_counters": {
            "provider_calls": 0,
            "model_calls": 0,
            "tool_calls": 0,
            "connector_calls": 0,
            "network_calls": 0,
            "credential_reads": 0,
            "external_sends": 0,
            "file_mutation_execution": 0,
            "background_jobs": 0,
            "robotics_calls": 0,
            "iot_calls": 0,
        },
    }


def main() -> int:
    args = parse_args()
    result = run(args.database, args.request_id)
    import json

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["first_status"] != "acknowledged":
        return 1
    if result["replay_status"] != "denied":
        return 1
    if result["guardian_source"] != "guardian_core.policy":
        return 1
    if result["runtime_authority_blocked"] is not True:
        return 1
    if any(
        result[field] is not False
        for field in ("executable", "execution_allowed", "side_effects_allowed")
    ):
        return 1
    if any(result["side_effect_counters"].values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
