#!/usr/bin/env python3
"""Smoke the three durable, non-authorizing synthetic approval outcomes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lima_office.runtime.approval_decision import (  # noqa: E402
    DECISION_CONFIRMATION, NonAuthorizingApprovalDecisionService,
)
from lima_office.runtime.approval_preview import (  # noqa: E402
    CREATE_CONFIRMATION as PREVIEW_CREATE,
    TRANSITION_CONFIRMATION as PREVIEW_TRANSITION,
    OfficeApprovalPreviewService,
)
from lima_office.runtime.office_helper import (  # noqa: E402
    HELPER_CONFIRMATION, OfficeOperationsHelperService,
)
from lima_office.runtime.operator_harness import HarnessStateStore  # noqa: E402
from lima_office.runtime.operator_session import (  # noqa: E402
    BIND_CONFIRMATION, AttendedOperatorSessionService,
)
from lima_office.runtime.pending_approval_request import (  # noqa: E402
    CREATE_CONFIRMATION as REQUEST_CREATE, PendingApprovalRequestService, _digest,
)
from lima_office.runtime.task_proposal import (  # noqa: E402
    CREATE_CONFIRMATION as PROPOSAL_CREATE,
    TRANSITION_CONFIRMATION as PROPOSAL_TRANSITION,
    OfficeTaskProposalService,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="lima-decision-smoke-") as temp:
        path = Path(temp) / "state.sqlite3"
        store = HarnessStateStore(path)
        clock = [datetime(2026, 9, 9, 15, 0, tzinfo=timezone.utc)]
        now = lambda: clock[0]
        helper = OfficeOperationsHelperService(store)
        proposals = OfficeTaskProposalService(store)
        previews = OfficeApprovalPreviewService(store, clock=now)
        sessions = AttendedOperatorSessionService(
            store, clock=now, subject_provider=lambda: "Synthetic Smoke User")
        requests = PendingApprovalRequestService(store, sessions, clock=now)
        decisions = NonAuthorizingApprovalDecisionService(store, sessions, clock=now)
        session = sessions.bind(confirmation=BIND_CONFIRMATION)

        def new_request():
            helper_result = helper.review_registration(
                scenario_id="missing-phone", confirmation=HELPER_CONFIRMATION)
            proposal = proposals.create_from_helper(
                helper_result=helper_result, confirmation=PROPOSAL_CREATE)
            proposal = proposals.transition(
                proposal_id=proposal["proposal_id"], expected_revision=1,
                action="propose", confirmation=PROPOSAL_TRANSITION)
            proposal = proposals.transition(
                proposal_id=proposal["proposal_id"], expected_revision=2,
                action="accept", confirmation=PROPOSAL_TRANSITION)
            preview = previews.create_from_proposal(
                proposal_id=proposal["proposal_id"],
                expected_proposal_revision=proposal["revision"],
                confirmation=PREVIEW_CREATE)
            preview = previews.transition(
                approval_preview_id=preview["approval_preview_id"],
                expected_revision=1, action="review",
                confirmation=PREVIEW_TRANSITION)
            return requests.create(
                approval_preview_id=preview["approval_preview_id"],
                expected_preview_revision=preview["revision"],
                operator_session_binding_id=session["binding_id"],
                confirmation=REQUEST_CREATE)

        pending = {action: new_request() for action in ("deny", "cancel", "expire")}
        outcomes = {}
        for action in ("deny", "cancel"):
            outcomes[action] = decisions.transition(
                approval_request_id=pending[action]["approval_request_id"],
                expected_request_hash=_digest(pending[action]), action=action,
                operator_session_binding_id=session["binding_id"],
                confirmation=DECISION_CONFIRMATION)
        clock[0] += timedelta(seconds=901)
        outcomes["expire"] = decisions.transition(
            approval_request_id=pending["expire"]["approval_request_id"],
            expected_request_hash=_digest(pending["expire"]), action="expire",
            operator_session_binding_id=None, confirmation=DECISION_CONFIRMATION)

        safe = all(
            outcome["result"]["approval_token_id"] is None
            and outcome["result"]["binding_id"] is None
            and outcome["result"]["assigned_worker_id"] is None
            and outcome["result"]["arc_dispatched"] is False
            and outcome["result"]["external_side_effects"] is False
            for outcome in outcomes.values()
        )
        store.close()
        reopened = HarnessStateStore(path)
        summary = {
            "status": "PASS" if safe else "FAIL",
            "results": {action: value["result"]["result"]
                        for action, value in outcomes.items()},
            "durable_request_count": len(reopened.office_pending_approval_requests()),
            "durable_result_count": len(reopened.office_approval_results()),
            "evidence_event_count": len(reopened.recent_events(limit=100)),
            "positive_approval_created": False,
            "approval_token_created": False,
            "arc_dispatched": False,
            "external_side_effects": False,
        }
        reopened.close()
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if safe and summary["durable_result_count"] == 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
