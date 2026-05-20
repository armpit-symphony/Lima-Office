"""Shared test helpers for Phase 1A runtime scaffolding."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"


def example(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def task_example() -> dict:
    return copy.deepcopy(example("task.execution.example.json"))


def heartbeat_example() -> dict:
    return copy.deepcopy(example("worker.heartbeat.example.json"))


def token_valid_example() -> dict:
    return copy.deepcopy(example("token.verification.valid.example.json"))


def token_expired_example() -> dict:
    return copy.deepcopy(example("token.verification.expired.example.json"))


def guardian_allow_decision() -> dict:
    from lima_office.guardian.policy import GuardianPolicy

    return GuardianPolicy().decide(
        "read_only_diagnostic",
        {
            "tenant_id": "tenant-lab-001",
            "customer_context_id": "customer-context-main",
            "execution_mode": "mock_only",
            "external_effect": "none",
            "evidence_required": True,
            "evidence_artifact_ids": ["ev-task-it-health-001"],
        },
    )


def has_jsonschema() -> bool:
    try:
        import jsonschema  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def validator():
    from lima_office.contracts import ContractLoader, ContractValidator

    return ContractValidator(ContractLoader().load())
