"""Attended operator binding and pending-only approval request tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from lima_office.guardian import GuardianPolicy
from lima_office.runtime.approval_preview import (
    CREATE_CONFIRMATION as PREVIEW_CREATE,
    TRANSITION_CONFIRMATION as PREVIEW_TRANSITION,
    OfficeApprovalPreviewService,
)
from lima_office.runtime.office_helper import HELPER_CONFIRMATION, OfficeOperationsHelperService
from lima_office.runtime.operator_harness import HarnessStateStore
from lima_office.runtime.operator_session import (
    BIND_CONFIRMATION, AttendedOperatorSessionService, OperatorSessionError,
)
from lima_office.runtime.pending_approval_request import (
    CREATE_CONFIRMATION, PendingApprovalRequestError, PendingApprovalRequestService,
)
from lima_office.runtime.task_proposal import (
    CREATE_CONFIRMATION as PROPOSAL_CREATE,
    TRANSITION_CONFIRMATION as PROPOSAL_TRANSITION,
    OfficeTaskProposalService,
)


class FailingPendingCommitStore(HarnessStateStore):
    def commit_office_pending_approval_request(self, *args, **kwargs):
        raise OSError("synthetic pending request commit failure")


class PendingApprovalRequestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lima-pending-approval-")
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = HarnessStateStore(self.path)
        self.now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
        self.helper = OfficeOperationsHelperService(self.store)
        self.proposals = OfficeTaskProposalService(self.store)
        self.previews = OfficeApprovalPreviewService(self.store, clock=lambda: self.now)
        self.sessions = AttendedOperatorSessionService(
            self.store, clock=lambda: self.now, subject_provider=lambda: "Local User"
        )
        self.requests = PendingApprovalRequestService(
            self.store, self.sessions, clock=lambda: self.now
        )

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def reviewed_preview(self):
        helper = self.helper.review_registration(
            scenario_id="missing-phone", confirmation=HELPER_CONFIRMATION)
        proposal = self.proposals.create_from_helper(
            helper_result=helper, confirmation=PROPOSAL_CREATE)
        proposal = self.proposals.transition(
            proposal_id=proposal["proposal_id"], expected_revision=1,
            action="propose", confirmation=PROPOSAL_TRANSITION)
        proposal = self.proposals.transition(
            proposal_id=proposal["proposal_id"], expected_revision=2,
            action="accept", confirmation=PROPOSAL_TRANSITION)
        preview = self.previews.create_from_proposal(
            proposal_id=proposal["proposal_id"],
            expected_proposal_revision=proposal["revision"],
            confirmation=PREVIEW_CREATE)
        preview = self.previews.transition(
            approval_preview_id=preview["approval_preview_id"], expected_revision=1,
            action="review", confirmation=PREVIEW_TRANSITION)
        return proposal, preview

    def test_session_is_pseudonymous_process_bound_and_not_approval(self):
        session = self.sessions.bind(confirmation=BIND_CONFIRMATION)
        self.assertTrue(session["operator_id"].startswith("operator-lab:"))
        self.assertNotIn("Local User", json.dumps(session))
        self.assertFalse(session["raw_os_username_stored"])
        self.assertFalse(session["credentials_collected"])
        self.assertFalse(session["production_identity_verified"])
        self.assertFalse(session["approval_authority"])
        self.assertFalse(session["approval_token_allowed"])
        self.assertFalse(session["arc_dispatch_allowed"])
        self.assertFalse(session["survives_process_restart"])

    def test_creates_only_durable_pending_request(self):
        proposal, preview = self.reviewed_preview()
        session = self.sessions.bind(confirmation=BIND_CONFIRMATION)
        request = self.requests.create(
            approval_preview_id=preview["approval_preview_id"],
            expected_preview_revision=preview["revision"],
            operator_session_binding_id=session["binding_id"],
            confirmation=CREATE_CONFIRMATION)
        self.assertEqual("approval.request", request["contract_name"])
        self.assertEqual("pending_review", request["status"])
        self.assertEqual("pending", request["approval_result"])
        self.assertEqual("none", request["requested_scope"]["external_effect"])
        self.assertEqual(0, request["requested_scope"]["max_uses"])
        self.assertEqual(["review_prepared_form_plan"], request["requested_scope"]["allowed_operations"])
        self.assertEqual(proposal["proposal_id"], request["task_id"])
        for flag in ("approval_result_created", "approval_binding_created",
                     "token_verification_performed", "replay_record_created",
                     "arc_dispatch_allowed", "arc_dispatched", "external_side_effects"):
            self.assertFalse(request[flag], flag)
        self.assertIsNone(request["approval_token_id"])
        self.assertIsNone(request["binding_id"])
        self.assertIsNone(request["assigned_worker_id"])
        self.assertEqual(request, self.store.office_pending_approval_request_for_preview(
            preview["approval_preview_id"]))
        self.assertEqual("office_pending_approval_request_created",
                         self.store.recent_events(limit=1)[0]["event_type"])

    def test_requires_reviewed_preview_session_fresh_intent_and_exact_revision(self):
        _, preview = self.reviewed_preview()
        event_count = len(self.store.recent_events(limit=100))
        for kwargs in (
            {"expected_preview_revision": preview["revision"],
             "operator_session_binding_id": "missing", "confirmation": CREATE_CONFIRMATION},
            {"expected_preview_revision": 99,
             "operator_session_binding_id": "missing", "confirmation": CREATE_CONFIRMATION},
            {"expected_preview_revision": preview["revision"],
             "operator_session_binding_id": "missing", "confirmation": "yes"},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(PendingApprovalRequestError):
                    self.requests.create(approval_preview_id=preview["approval_preview_id"], **kwargs)
        self.assertEqual(event_count, len(self.store.recent_events(limit=100)))

    def test_duplicate_and_expired_session_fail_closed(self):
        _, preview = self.reviewed_preview()
        session = self.sessions.bind(confirmation=BIND_CONFIRMATION)
        self.requests.create(
            approval_preview_id=preview["approval_preview_id"],
            expected_preview_revision=preview["revision"],
            operator_session_binding_id=session["binding_id"], confirmation=CREATE_CONFIRMATION)
        event_count = len(self.store.recent_events(limit=100))
        with self.assertRaisesRegex(PendingApprovalRequestError, "already has"):
            self.requests.create(
                approval_preview_id=preview["approval_preview_id"],
                expected_preview_revision=preview["revision"],
                operator_session_binding_id=session["binding_id"], confirmation=CREATE_CONFIRMATION)
        self.assertEqual(event_count, len(self.store.recent_events(limit=100)))

        self.now += timedelta(seconds=1801)
        with self.assertRaisesRegex(OperatorSessionError, "expired"):
            self.sessions.require_active(session["binding_id"])

    def test_request_persists_but_operator_session_does_not(self):
        _, preview = self.reviewed_preview()
        session = self.sessions.bind(confirmation=BIND_CONFIRMATION)
        request = self.requests.create(
            approval_preview_id=preview["approval_preview_id"],
            expected_preview_revision=preview["revision"],
            operator_session_binding_id=session["binding_id"], confirmation=CREATE_CONFIRMATION)
        self.store.close()
        reopened = HarnessStateStore(self.path)
        try:
            self.assertEqual([request], reopened.office_pending_approval_requests())
            restarted_sessions = AttendedOperatorSessionService(
                reopened, clock=lambda: self.now, subject_provider=lambda: "Local User")
            self.assertFalse(restarted_sessions.state_summary()["active"])
        finally:
            reopened.close()
        self.store = HarnessStateStore(self.path)

    def test_guardian_requires_pending_only_restrictions(self):
        baseline = {
            "tenant_id": "tenant-lab-001", "customer_context_id": "customer-context-main",
            "approval_request_id": "approval-request:test",
            "execution_mode": "request_metadata_only", "external_effect": "none",
            "evidence_required": True, "evidence_artifact_ids": ["ev-test"],
            "attended": True, "operator_confirmation": True,
            "operator_session_active": True,
            "operator_session_binding_id": "operator-session-binding:test",
            "production_identity_verified": False, "fresh_intent": True,
            "preview_reviewed_no_authority": True, "source_current": True,
            "synthetic_data_only": True, "free_form_content_allowed": False,
            "request_only": True, "approval_result_allowed": False,
            "approval_token_access_allowed": False, "approval_binding_allowed": False,
            "token_verification_allowed": False, "replay_record_allowed": False,
            "model_call_allowed": False, "tool_execution_allowed": False,
            "arc_dispatch_allowed": False, "connector_access_allowed": False,
            "submission_allowed": False, "external_side_effects": False,
            "approval_required": True,
        }
        policy = GuardianPolicy()
        self.assertEqual("requires_approval", policy.decide(
            "office_pending_approval_request_create", baseline)["decision"])
        unsafe = {
            "operator_confirmation": False, "operator_session_active": False,
            "production_identity_verified": True, "fresh_intent": False,
            "preview_reviewed_no_authority": False, "source_current": False,
            "synthetic_data_only": False, "free_form_content_allowed": True,
            "request_only": False, "approval_result_allowed": True,
            "approval_token_access_allowed": True, "approval_binding_allowed": True,
            "token_verification_allowed": True, "replay_record_allowed": True,
            "model_call_allowed": True, "tool_execution_allowed": True,
            "arc_dispatch_allowed": True, "connector_access_allowed": True,
            "submission_allowed": True, "external_side_effects": True,
        }
        for key, value in unsafe.items():
            with self.subTest(key=key):
                self.assertEqual("deny", policy.decide(
                    "office_pending_approval_request_create",
                    {**baseline, key: value})["decision"])


if __name__ == "__main__":
    unittest.main()
