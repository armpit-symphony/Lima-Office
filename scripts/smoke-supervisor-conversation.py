#!/usr/bin/env python3
"""Run one isolated, synthetic, read-only Supervisor conversation smoke test."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

OFFICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OFFICE_ROOT))

from lima_office.runtime.operator_harness import HarnessStateStore
from lima_office.runtime.supervisor_conversation import (
    SupervisorConversationService,
    TURN_CONFIRMATION,
)


SYNTHETIC_MESSAGE = (
    "In one sentence, explain how a small office should review a synthetic "
    "registration form before any submission."
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="lima-supervisor-smoke-") as temp:
        store = HarnessStateStore(Path(temp) / "evidence.sqlite3")
        try:
            service = SupervisorConversationService(store)
            result = service.turn(
                message=SYNTHETIC_MESSAGE,
                confirmation=TURN_CONFIRMATION,
                data_classification="internal",
            )
            events = store.recent_events(limit=10)
        finally:
            store.close()

    encoded_events = json.dumps(events, sort_keys=True)
    if SYNTHETIC_MESSAGE in encoded_events or result["response_text"] in encoded_events:
        raise SystemExit("raw conversation content was persisted; smoke failed closed")
    if len(events) != 3:
        raise SystemExit("expected exactly three evidenced conversation events")
    if result.get("tool_event_count") != 0:
        raise SystemExit("disabled tool activity was detected")

    print(
        json.dumps(
            {
                "status": "passed",
                "turn_status": result["status"],
                "provider": result["provider"],
                "sandbox_mode": result["sandbox_mode"],
                "session_persistence": result["session_persistence"],
                "tool_event_count": result["tool_event_count"],
                "external_side_effects": result["external_side_effects"],
                "evidence_event_count": len(events),
                "raw_content_persisted": False,
                "response_length": result["response_length"],
                "response_sha256": result["response_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
