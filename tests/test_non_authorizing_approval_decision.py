"""Non-authorizing approval decision lifecycle tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from lima_office.guardian import GuardianPolicy
from lima_office.runtime.approval_decision import (
    ApprovalDecisionError,
    DECISION_CONFIRMATION,
    NonAuthorizingApprovalDecisionService,
)
from lima_office.runtime.approval_preview import (
    CREATE_CONFIRMATION as PREVIEW_CREATE,
    TRANSITION_CONFIRMATION as PREVIEW_TRANSITION,
    OfficeApprovalPreviewService,
)
from lima_office.runtime.office_helper import HELPER_CONFIRMATION, OfficeOperationsHelperService
from lima_office.runtime.operator_harness import HarnessStateStore
from lima_office.runtime.operator_session import BIND_CONFIRMATION, AttendedOperatorSessionService
from lima_office.runtime.pending_approval_request import (
    CREATE_CONFIRMATION as REQUEST_CREATE,
    PendingApprovalRequestService,
    _digest,
)
from lima_office.runtime.errors import ContractValidationError
from lima_office.runtime.task_proposal import (
    CREATE_CONFIRMATION as PROPOSAL_CREATE,
    TRANSITION_CONFIRMATION as PROPOSAL_TRANSITION,
    OfficeTaskProposalService,
)


class FailingDecisionCommitStore(HarnessStateStore):
    def commit_office_non_authorizing_approval_decision(self, *args, **kwargs):
        raise OSError("synthetic decision commit failure")


class NonAuthorizingApprovalDecisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lima-approval-decision-")
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = HarnessStateStore(self.path)
        self.now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        self.helper = OfficeOperationsHelperService(self.store)
        self.proposals = OfficeTaskProposalService(self.store)
        self.previews = OfficeApprovalPreviewService(self.store, clock=lambda: self.now)
        self.sessions = AttendedOperatorSessionService(
            self.store, clock=lambda: self.now, subject_provider=lambda: "Local User")
        self.requests = PendingApprovalRequestService(
            self.store, self.sessions, clock=lambda: self.now)
        self.decisions = NonAuthorizingApprovalDecisionService(
            self.store, self.sessions, clock=lambda: self.now)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def create_request(self):
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
            expected_proposal_revision=proposal["revision"], confirmation=PREVIEW_CREATE)
        preview = self.previews.transition(
            approval_preview_id=preview["approval_preview_id"], expected_revision=1,
            action="review", confirmation=PREVIEW_TRANSITION)
        session = self.sessions.state_summary().get("binding")
        if session is None:
            session = self.sessions.bind(confirmation=BIND_CONFIRMATION)
        request = self.requests.create(
            approval_preview_id=preview["approval_preview_id"],
            expected_preview_revision=preview["revision"],
            operator_session_binding_id=session["binding_id"],
            confirmation=REQUEST_CREATE)
        return request, session

    def decide(self, request, session, action):
        return self.decisions.transition(
            approval_request_id=request["approval_request_id"],
            expected_request_hash=_digest(request), action=action,
            operator_session_binding_id=(None if action == "expire" else session["binding_id"]),
            confirmation=DECISION_CONFIRMATION)

    def test_deny_cancel_and_explicit_expiry_are_durable_and_non_authorizing(self):
        denied_request, session = self.create_request()
        cancelled_request, _ = self.create_request()
        expired_request, _ = self.create_request()

        outcomes = [
            self.decide(denied_request, session, "deny"),
            self.decide(cancelled_request, session, "cancel"),
        ]
        self.now += timedelta(seconds=901)
        outcomes.append(self.decide(expired_request, session, "expire"))

        expected = [
            ("denied", "denied_by_approver", "attended_deny"),
            ("cancelled", "cancelled", "attended_cancel"),
            ("expired", "expired", "explicit_expire"),
        ]
        for outcome, (state, reason, kind) in zip(outcomes, expected, strict=True):
            with self.subTest(state=state):
                request, result = outcome["request"], outcome["result"]
                self.assertEqual(state, request["status"])
                self.assertEqual(state, request["approval_result"])
                self.assertTrue(request["approval_result_created"])
                self.assertEqual(state, result["result"])
                self.assertEqual(reason, result["result_reason_code"])
                self.assertEqual(kind, result["decision_kind"])
                for flag in ("approval_binding_created", "token_verification_performed",
                             "replay_record_created", "arc_dispatch_allowed",
                             "arc_dispatched", "external_side_effects"):
                    self.assertFalse(request[flag], flag)
                    self.assertFalse(result[flag], flag)
                self.assertIsNone(result["approval_token_id"])
                self.assertIsNone(result["binding_id"])
                self.assertIsNone(result["assigned_worker_id"])
                self.assertEqual(result, self.store.office_approval_result_for_request(
                    request["approval_request_id"]))
        self.assertIsNone(outcomes[2]["result"]["approver_operator_id"])
        self.assertEqual("business_owner", outcomes[0]["result"]["approver_role_ref"])
        mismatched = dict(outcomes[0]["request"])
        mismatched["approval_result"] = "cancelled"
        with self.assertRaises(ContractValidationError):
            self.decisions.validator.validate(mismatched, "approval.request")

        self.store.close()
        reopened = HarnessStateStore(self.path)
        try:
            self.assertEqual(3, len(reopened.office_approval_results()))
            self.assertEqual(3, sum(
                item["status"] != "pending_review"
                for item in reopened.office_pending_approval_requests()))
        finally:
            reopened.close()
        self.store = HarnessStateStore(self.path)

    def test_positive_or_stale_or_mistimed_decisions_fail_before_authority(self):
        request, session = self.create_request()
        event_count = len(self.store.recent_events(limit=100))
        cases = (
            {"action": "approve", "expected_request_hash": _digest(request),
             "operator_session_binding_id": session["binding_id"]},
            {"action": "deny", "expected_request_hash": "sha256:" + "0" * 64,
             "operator_session_binding_id": session["binding_id"]},
            {"action": "expire", "expected_request_hash": _digest(request),
             "operator_session_binding_id": None},
        )
        for values in cases:
            with self.subTest(action=values["action"]), self.assertRaises(ApprovalDecisionError):
                self.decisions.transition(
                    approval_request_id=request["approval_request_id"],
                    confirmation=DECISION_CONFIRMATION, **values)
        self.assertEqual(event_count, len(self.store.recent_events(limit=100)))
        self.assertIsNone(self.store.office_approval_result_for_request(
            request["approval_request_id"]))

    def test_deny_after_expiry_and_cancel_from_new_session_fail_closed(self):
        request, session = self.create_request()
        new_session = self.sessions.bind(confirmation=BIND_CONFIRMATION)
        with self.assertRaisesRegex(ApprovalDecisionError, "original attended requester"):
            self.decisions.transition(
                approval_request_id=request["approval_request_id"],
                expected_request_hash=_digest(request), action="cancel",
                operator_session_binding_id=new_session["binding_id"],
                confirmation=DECISION_CONFIRMATION)
        self.now += timedelta(seconds=901)
        with self.assertRaisesRegex(ApprovalDecisionError, "record expiry"):
            self.decisions.transition(
                approval_request_id=request["approval_request_id"],
                expected_request_hash=_digest(request), action="deny",
                operator_session_binding_id=new_session["binding_id"],
                confirmation=DECISION_CONFIRMATION)

    def test_guardian_rule_fails_closed_on_each_authority_mutation(self):
        baseline = {
            "tenant_id": "tenant-lab-001", "customer_context_id": "customer-context-main",
            "approval_request_id": "approval-request:test",
            "execution_mode": "decision_metadata_only", "external_effect": "none",
            "evidence_required": True, "evidence_artifact_ids": ["ev-test"],
            "operator_confirmation": True, "fresh_intent": True,
            "operation": "deny", "result": "denied", "non_authorizing": True,
            "request_pending": True, "request_expired": False,
            "attended": True, "operator_session_active": True,
            "operator_session_binding_id": "operator-session-binding:test",
            "synthetic_data_only": True, "approval_result_created": True,
            "approval_token_access_allowed": False, "approval_binding_allowed": False,
            "token_verification_allowed": False, "replay_record_allowed": False,
            "model_call_allowed": False, "tool_execution_allowed": False,
            "arc_dispatch_allowed": False, "connector_access_allowed": False,
            "submission_allowed": False, "external_side_effects": False,
            "approval_required": False,
        }
        policy = GuardianPolicy()
        self.assertEqual("allow_with_evidence", policy.decide(
            "office_non_authorizing_approval_decision", baseline)["decision"])
        unsafe = {
            "non_authorizing": False, "approval_token_access_allowed": True,
            "approval_binding_allowed": True, "token_verification_allowed": True,
            "replay_record_allowed": True, "model_call_allowed": True,
            "tool_execution_allowed": True, "arc_dispatch_allowed": True,
            "connector_access_allowed": True, "submission_allowed": True,
            "external_side_effects": True,
        }
        for key, value in unsafe.items():
            with self.subTest(key=key):
                self.assertEqual("deny", policy.decide(
                    "office_non_authorizing_approval_decision",
                    {**baseline, key: value})["decision"])

    def test_atomic_commit_failure_leaves_request_pending_and_no_result(self):
        request, session = self.create_request()
        self.store.close()
        failing = FailingDecisionCommitStore(self.path)
        try:
            decisions = NonAuthorizingApprovalDecisionService(
                failing, self.sessions, clock=lambda: self.now)
            with self.assertRaisesRegex(ApprovalDecisionError, "atomically"):
                decisions.transition(
                    approval_request_id=request["approval_request_id"],
                    expected_request_hash=_digest(request), action="deny",
                    operator_session_binding_id=session["binding_id"],
                    confirmation=DECISION_CONFIRMATION)
            self.assertEqual("pending_review", failing.office_approval_request(
                request["approval_request_id"])["status"])
            self.assertIsNone(failing.office_approval_result_for_request(
                request["approval_request_id"]))
        finally:
            failing.close()
        self.store = HarnessStateStore(self.path)


if __name__ == "__main__":
    unittest.main()
