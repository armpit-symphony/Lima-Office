#!/usr/bin/env python3
"""Exercise the tokenless Supervisor task-proposal lifecycle locally."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lima_office.runtime.office_helper import (  # noqa: E402
    HELPER_CONFIRMATION,
    OfficeOperationsHelperService,
)
from lima_office.runtime.operator_harness import HarnessStateStore  # noqa: E402
from lima_office.runtime.task_proposal import (  # noqa: E402
    CREATE_CONFIRMATION,
    EDIT_CONFIRMATION,
    TRANSITION_CONFIRMATION,
    OfficeTaskProposalService,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="lima-task-proposal-smoke-") as raw:
        path = Path(raw) / "harness.sqlite3"
        store = HarnessStateStore(path)
        helper = OfficeOperationsHelperService(store)
        proposals = OfficeTaskProposalService(store)
        helper_result = helper.review_registration(
            scenario_id="missing-phone",
            confirmation=HELPER_CONFIRMATION,
        )
        proposal = proposals.create_from_helper(
            helper_result=helper.proposal_source(helper_result["helper_result_id"]),
            confirmation=CREATE_CONFIRMATION,
        )
        proposal = proposals.edit(
            proposal_id=proposal["proposal_id"],
            expected_revision=proposal["revision"],
            priority="low",
            selected_step_ids=[
                "review_synthetic_scenario",
                "resolve_human_input_fields",
                "owner_review_prepared_form",
            ],
            confirmation=EDIT_CONFIRMATION,
        )
        for action in ("propose", "accept"):
            proposal = proposals.transition(
                proposal_id=proposal["proposal_id"],
                expected_revision=proposal["revision"],
                action=action,
                confirmation=TRANSITION_CONFIRMATION,
            )
        event_count = len(store.recent_events(limit=100))
        store.close()

        reopened = HarnessStateStore(path)
        restored = reopened.office_proposal(proposal["proposal_id"])
        reopened.close()
        if restored != proposal:
            raise RuntimeError("proposal did not survive store restart")
        if proposal["state"] != "accepted_for_future_approval":
            raise RuntimeError("unexpected final proposal state")
        if any(
            proposal[key]
            for key in (
                "approval_token_issued", "arc_dispatch_allowed", "arc_dispatched",
                "model_called", "tools_used", "connector_accessed",
                "submission_allowed", "external_side_effects",
            )
        ):
            raise RuntimeError("proposal crossed a blocked capability boundary")
        print(json.dumps({
            "status": "passed",
            "final_state": proposal["state"],
            "revision": proposal["revision"],
            "event_count": event_count,
            "approval_token_issued": False,
            "arc_dispatched": False,
            "durable_after_restart": True,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
