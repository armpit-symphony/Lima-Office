#!/usr/bin/env python3
"""Exercise the tokenless approval-preview lifecycle and restart recovery."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lima_office.runtime.approval_preview import (  # noqa: E402
    CREATE_CONFIRMATION,
    TRANSITION_CONFIRMATION,
    OfficeApprovalPreviewService,
)
from lima_office.runtime.office_helper import (  # noqa: E402
    HELPER_CONFIRMATION,
    OfficeOperationsHelperService,
)
from lima_office.runtime.operator_harness import HarnessStateStore  # noqa: E402
from lima_office.runtime.task_proposal import (  # noqa: E402
    CREATE_CONFIRMATION as PROPOSAL_CREATE_CONFIRMATION,
    TRANSITION_CONFIRMATION as PROPOSAL_TRANSITION_CONFIRMATION,
    OfficeTaskProposalService,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="lima-approval-preview-smoke-") as raw:
        path = Path(raw) / "harness.sqlite3"
        store = HarnessStateStore(path)
        helper = OfficeOperationsHelperService(store)
        proposals = OfficeTaskProposalService(store)
        previews = OfficeApprovalPreviewService(store)

        helper_result = helper.review_registration(
            scenario_id="missing-phone", confirmation=HELPER_CONFIRMATION
        )
        proposal = proposals.create_from_helper(
            helper_result=helper_result,
            confirmation=PROPOSAL_CREATE_CONFIRMATION,
        )
        for action in ("propose", "accept"):
            proposal = proposals.transition(
                proposal_id=proposal["proposal_id"],
                expected_revision=proposal["revision"],
                action=action,
                confirmation=PROPOSAL_TRANSITION_CONFIRMATION,
            )
        preview = previews.create_from_proposal(
            proposal_id=proposal["proposal_id"],
            expected_proposal_revision=proposal["revision"],
            confirmation=CREATE_CONFIRMATION,
        )
        preview = previews.transition(
            approval_preview_id=preview["approval_preview_id"],
            expected_revision=preview["revision"],
            action="review",
            confirmation=TRANSITION_CONFIRMATION,
        )
        event_count = len(store.recent_events(limit=100))
        store.close()

        reopened = HarnessStateStore(path)
        restored = reopened.office_approval_preview(preview["approval_preview_id"])
        reopened.close()
        if restored != preview:
            raise RuntimeError("approval preview did not survive store restart")
        if preview["state"] != "reviewed_no_authority":
            raise RuntimeError("unexpected final approval-preview state")
        blocked_flags = (
            "real_approval_request_created", "approval_result_created",
            "approval_token_issued", "approval_binding_created",
            "token_verification_performed", "replay_record_created",
            "arc_dispatch_allowed", "arc_dispatched", "model_called",
            "tools_used", "connector_accessed", "submission_allowed",
            "external_side_effects",
        )
        if any(preview[key] for key in blocked_flags) or preview["assigned_worker_id"] is not None:
            raise RuntimeError("approval preview crossed an authority boundary")
        print(json.dumps({
            "status": "passed",
            "final_state": preview["state"],
            "revision": preview["revision"],
            "event_count": event_count,
            "real_approval_request_created": False,
            "approval_token_issued": False,
            "arc_dispatched": False,
            "durable_after_restart": True,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
