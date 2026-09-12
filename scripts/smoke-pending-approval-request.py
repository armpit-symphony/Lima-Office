#!/usr/bin/env python3
"""Exercise attended-session binding through durable pending request creation."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lima_office.runtime.approval_preview import (  # noqa: E402
    CREATE_CONFIRMATION as PREVIEW_CREATE,
    TRANSITION_CONFIRMATION as PREVIEW_TRANSITION,
    OfficeApprovalPreviewService,
)
from lima_office.runtime.office_helper import HELPER_CONFIRMATION, OfficeOperationsHelperService  # noqa: E402
from lima_office.runtime.operator_harness import HarnessStateStore  # noqa: E402
from lima_office.runtime.operator_session import BIND_CONFIRMATION, AttendedOperatorSessionService  # noqa: E402
from lima_office.runtime.pending_approval_request import CREATE_CONFIRMATION, PendingApprovalRequestService  # noqa: E402
from lima_office.runtime.task_proposal import (  # noqa: E402
    CREATE_CONFIRMATION as PROPOSAL_CREATE,
    TRANSITION_CONFIRMATION as PROPOSAL_TRANSITION,
    OfficeTaskProposalService,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="lima-pending-request-smoke-") as temp:
        path = Path(temp) / "state.sqlite3"
        store = HarnessStateStore(path)
        helper = OfficeOperationsHelperService(store)
        proposals = OfficeTaskProposalService(store)
        previews = OfficeApprovalPreviewService(store)
        sessions = AttendedOperatorSessionService(store, subject_provider=lambda: "Synthetic Local User")
        requests = PendingApprovalRequestService(store, sessions)
        result = helper.review_registration(
            scenario_id="missing-phone", confirmation=HELPER_CONFIRMATION)
        proposal = proposals.create_from_helper(helper_result=result, confirmation=PROPOSAL_CREATE)
        for action in ("propose", "accept"):
            proposal = proposals.transition(
                proposal_id=proposal["proposal_id"], expected_revision=proposal["revision"],
                action=action, confirmation=PROPOSAL_TRANSITION)
        preview = previews.create_from_proposal(
            proposal_id=proposal["proposal_id"],
            expected_proposal_revision=proposal["revision"], confirmation=PREVIEW_CREATE)
        preview = previews.transition(
            approval_preview_id=preview["approval_preview_id"],
            expected_revision=preview["revision"], action="review",
            confirmation=PREVIEW_TRANSITION)
        session = sessions.bind(confirmation=BIND_CONFIRMATION)
        request = requests.create(
            approval_preview_id=preview["approval_preview_id"],
            expected_preview_revision=preview["revision"],
            operator_session_binding_id=session["binding_id"],
            confirmation=CREATE_CONFIRMATION)
        event_count = len(store.recent_events(limit=100))
        store.close()

        reopened = HarnessStateStore(path)
        restored = reopened.office_pending_approval_request_for_preview(
            preview["approval_preview_id"])
        restarted_sessions = AttendedOperatorSessionService(
            reopened, subject_provider=lambda: "Synthetic Local User")
        summary = {
            "status": request["status"],
            "approval_result": request["approval_result"],
            "external_effect": request["requested_scope"]["external_effect"],
            "max_uses": request["requested_scope"]["max_uses"],
            "event_count": event_count,
            "request_restored_after_restart": restored == request,
            "operator_session_restored_after_restart": restarted_sessions.state_summary()["active"],
            "production_identity_verified": session["production_identity_verified"],
            "approval_result_created": request["approval_result_created"],
            "approval_token_created": request["approval_token_id"] is not None,
            "approval_binding_created": request["approval_binding_created"],
            "replay_record_created": request["replay_record_created"],
            "worker_assigned": request["assigned_worker_id"] is not None,
            "arc_dispatched": request["arc_dispatched"],
            "external_side_effects": request["external_side_effects"],
        }
        reopened.close()
        print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
