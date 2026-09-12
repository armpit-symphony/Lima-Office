#!/usr/bin/env python3
"""Run every fixed synthetic scenario through the bounded Office Helper."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

OFFICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OFFICE_ROOT))

from lima_office.runtime.office_helper import (
    HELPER_CONFIRMATION,
    OfficeOperationsHelperService,
)
from lima_office.runtime.operator_harness import HarnessStateStore


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="lima-office-helper-smoke-") as temp:
        store = HarnessStateStore(Path(temp) / "helper-evidence.sqlite3")
        try:
            helper = OfficeOperationsHelperService(store)
            scenarios = helper.state_summary()["scenarios"]
            results = [
                helper.review_registration(
                    scenario_id=item["scenario_id"],
                    confirmation=HELPER_CONFIRMATION,
                )
                for item in scenarios
            ]
            events = store.recent_events(limit=100)
        finally:
            store.close()

    encoded = json.dumps(events, sort_keys=True)
    forbidden_fixture_values = (
        "Jordan Example", "Avery Sample", "Casey Fixture", "Morgan Mock",
        "Riley Training", "example.test", "555-01",
    )
    if any(value in encoded for value in forbidden_fixture_values):
        raise SystemExit("synthetic profile content entered evidence; smoke failed")
    if len(events) != len(results) * 3:
        raise SystemExit("helper evidence count mismatch")
    if any(
        result[flag]
        for result in results
        for flag in (
            "model_called", "tools_used", "memory_used", "approval_requested",
            "arc_dispatched", "connector_accessed", "submission_allowed",
            "external_side_effects",
        )
    ):
        raise SystemExit("helper authority boundary failed")

    print(
        json.dumps(
            {
                "status": "passed",
                "scenario_count": len(results),
                "completed_count": sum(item["status"] == "completed" for item in results),
                "human_input_count": sum(item["disposition"] == "needs_human_input" for item in results),
                "owner_review_count": sum(item["disposition"] == "ready_for_owner_review" for item in results),
                "evidence_event_count": len(events),
                "raw_profile_persisted": False,
                "model_called": False,
                "tools_used": False,
                "arc_dispatched": False,
                "external_side_effects": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
