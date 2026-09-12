"""Safety, expiry, durability, and authority tests for approval previews."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from lima_office.guardian import GuardianPolicy
from lima_office.runtime.approval_preview import (
    CREATE_CONFIRMATION,
    TRANSITION_CONFIRMATION,
    ApprovalPreviewError,
    OfficeApprovalPreviewService,
)
from lima_office.runtime.office_helper import (
    HELPER_CONFIRMATION,
    OfficeOperationsHelperService,
)
from lima_office.runtime.operator_harness import HarnessStateStore
from lima_office.runtime.task_proposal import (
    CREATE_CONFIRMATION as PROPOSAL_CREATE_CONFIRMATION,
    TRANSITION_CONFIRMATION as PROPOSAL_TRANSITION_CONFIRMATION,
    OfficeTaskProposalService,
)


class FailingPreviewCommitStore(HarnessStateStore):
    def commit_office_approval_preview(self, *args, **kwargs):
        raise OSError("synthetic preview commit failure")


class OfficeApprovalPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lima-approval-preview-")
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = HarnessStateStore(self.path)
        self.helper = OfficeOperationsHelperService(self.store)
        self.proposals = OfficeTaskProposalService(self.store)
        self.now = datetime(2026, 9, 7, 18, 0, tzinfo=timezone.utc)
        self.service = OfficeApprovalPreviewService(
            self.store, clock=lambda: self.now
        )

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def accepted_proposal(self, scenario_id="missing-phone"):
        result = self.helper.review_registration(
            scenario_id=scenario_id, confirmation=HELPER_CONFIRMATION
        )
        proposal = self.proposals.create_from_helper(
            helper_result=result, confirmation=PROPOSAL_CREATE_CONFIRMATION
        )
        proposal = self.proposals.transition(
            proposal_id=proposal["proposal_id"], expected_revision=1,
            action="propose", confirmation=PROPOSAL_TRANSITION_CONFIRMATION,
        )
        return self.proposals.transition(
            proposal_id=proposal["proposal_id"], expected_revision=2,
            action="accept", confirmation=PROPOSAL_TRANSITION_CONFIRMATION,
        )

    def create_preview(self, scenario_id="missing-phone"):
        proposal = self.accepted_proposal(scenario_id)
        preview = self.service.create_from_proposal(
            proposal_id=proposal["proposal_id"],
            expected_proposal_revision=proposal["revision"],
            confirmation=CREATE_CONFIRMATION,
        )
        return proposal, preview

    def test_create_is_tokenless_contract_valid_and_durable(self):
        proposal, preview = self.create_preview()

        self.assertEqual("preview_ready", preview["state"])
        self.assertEqual("pending", preview["review_outcome"])
        self.assertEqual(proposal["proposal_id"], preview["source_proposal_id"])
        self.assertEqual(proposal["revision"], preview["source_proposal_revision"])
        self.assertEqual(0, preview["preview_scope"]["max_uses"])
        self.assertEqual("none", preview["preview_scope"]["external_effect"])
        self.assertEqual("not_bound_in_preview", preview["approver_requirements"]["identity_binding_status"])
        for flag in (
            "real_approval_request_created", "approval_result_created",
            "approval_token_issued", "approval_binding_created",
            "token_verification_performed", "replay_record_created",
            "arc_dispatch_allowed", "arc_dispatched", "model_called",
            "tools_used", "connector_accessed", "submission_allowed",
            "external_side_effects",
        ):
            self.assertFalse(preview[flag], flag)
        self.assertIsNone(preview["assigned_worker_id"])
        self.assertEqual(preview, self.store.office_approval_preview(preview["approval_preview_id"]))
        event = self.store.recent_events(limit=1)[0]
        self.assertEqual("office_approval_preview_change_committed", event["event_type"])
        self.assertEqual(preview["post_action_evidence_ref"], event["event_id"])
        encoded = json.dumps(self.store.recent_events(limit=100), sort_keys=True)
        self.assertNotIn("Avery Sample", encoded)
        self.assertNotIn("example.test", encoded)

    def test_review_marks_no_authority_and_is_terminal(self):
        _, preview = self.create_preview("complete-contact")
        preview = self.service.transition(
            approval_preview_id=preview["approval_preview_id"],
            expected_revision=1,
            action="review",
            confirmation=TRANSITION_CONFIRMATION,
        )
        self.assertEqual("reviewed_no_authority", preview["state"])
        self.assertEqual("reviewed_no_authority", preview["review_outcome"])
        self.assertFalse(preview["real_approval_request_created"])
        self.assertFalse(preview["approval_token_issued"])
        self.assertFalse(preview["arc_dispatched"])
        with self.assertRaises(ApprovalPreviewError):
            self.service.transition(
                approval_preview_id=preview["approval_preview_id"],
                expected_revision=2,
                action="review",
                confirmation=TRANSITION_CONFIRMATION,
            )

    def test_deny_and_withdraw_are_tokenless_terminal_states(self):
        for scenario, action, expected in (
            ("invalid-email", "deny", "denied"),
            ("invalid-postal-code", "withdraw", "withdrawn"),
        ):
            with self.subTest(action=action):
                _, preview = self.create_preview(scenario)
                preview = self.service.transition(
                    approval_preview_id=preview["approval_preview_id"],
                    expected_revision=1,
                    action=action,
                    confirmation=TRANSITION_CONFIRMATION,
                )
                self.assertEqual(expected, preview["state"])
                self.assertFalse(preview["approval_result_created"])
                self.assertFalse(preview["approval_token_issued"])

    def test_only_accepted_exact_revision_proposal_is_eligible(self):
        result = self.helper.review_registration(
            scenario_id="missing-phone", confirmation=HELPER_CONFIRMATION
        )
        draft = self.proposals.create_from_helper(
            helper_result=result, confirmation=PROPOSAL_CREATE_CONFIRMATION
        )
        event_count = len(self.store.recent_events(limit=100))
        for revision in (draft["revision"], 99):
            with self.subTest(revision=revision):
                with self.assertRaises(ApprovalPreviewError):
                    self.service.create_from_proposal(
                        proposal_id=draft["proposal_id"],
                        expected_proposal_revision=revision,
                        confirmation=CREATE_CONFIRMATION,
                    )
        self.assertEqual(event_count, len(self.store.recent_events(limit=100)))

    def test_duplicate_source_is_denied_before_evidence(self):
        proposal, _ = self.create_preview()
        event_count = len(self.store.recent_events(limit=100))
        with self.assertRaisesRegex(ApprovalPreviewError, "already has"):
            self.service.create_from_proposal(
                proposal_id=proposal["proposal_id"],
                expected_proposal_revision=proposal["revision"],
                confirmation=CREATE_CONFIRMATION,
            )
        self.assertEqual(event_count, len(self.store.recent_events(limit=100)))

    def test_invalid_confirmation_and_action_write_no_evidence(self):
        _, preview = self.create_preview()
        event_count = len(self.store.recent_events(limit=100))
        for action, confirmation in (
            ("review", "yes"),
            (["review"], TRANSITION_CONFIRMATION),
        ):
            with self.subTest(action=action):
                with self.assertRaises(ApprovalPreviewError):
                    self.service.transition(
                        approval_preview_id=preview["approval_preview_id"],
                        expected_revision=1,
                        action=action,
                        confirmation=confirmation,
                    )
        self.assertEqual(event_count, len(self.store.recent_events(limit=100)))

    def test_atomic_store_rolls_back_event_on_duplicate_source(self):
        _, preview = self.create_preview()
        duplicate = {
            **preview,
            "approval_preview_id": "approval-preview:duplicate",
            "revision": 1,
            "idempotency_key": "idem-approval-preview-duplicate-r1",
        }
        event_id = "harness-event:preview-must-roll-back"
        with self.assertRaises(Exception):
            self.store.commit_office_approval_preview(
                duplicate,
                event_id=event_id,
                event_type="office_approval_preview_change_committed",
                event_payload={"synthetic": True},
                expected_revision=None,
            )
        self.assertIsNone(
            self.store.office_approval_preview("approval-preview:duplicate")
        )
        self.assertNotIn(
            event_id,
            [item["event_id"] for item in self.store.recent_events(limit=100)],
        )

    def test_expired_preview_cannot_be_marked_reviewed(self):
        _, preview = self.create_preview()
        self.now += timedelta(seconds=901)
        summary = self.service.state_summary()["previews"][0]
        self.assertTrue(summary["expired_for_review"])
        self.assertFalse(summary["review_available"])
        with self.assertRaisesRegex(ApprovalPreviewError, "expired"):
            self.service.transition(
                approval_preview_id=preview["approval_preview_id"],
                expected_revision=1,
                action="review",
                confirmation=TRANSITION_CONFIRMATION,
            )
        self.assertEqual("preview_ready", self.store.office_approval_preview(preview["approval_preview_id"])["state"])

    def test_source_hash_and_revision_are_rechecked(self):
        proposal, preview = self.create_preview()
        changed = {
            **proposal,
            "revision": proposal["revision"] + 1,
            "priority": "low" if proposal["priority"] == "normal" else "normal",
            "idempotency_key": "synthetic-source-drift",
        }
        self.store.commit_office_proposal(
            changed,
            event_id="harness-event:synthetic-source-drift",
            event_type="synthetic_source_drift",
            event_payload={"synthetic": True},
            expected_revision=proposal["revision"],
        )
        summary = self.service.state_summary()["previews"][0]
        self.assertFalse(summary["source_current"])
        self.assertFalse(summary["review_available"])
        with self.assertRaisesRegex(ApprovalPreviewError, "no longer matches"):
            self.service.transition(
                approval_preview_id=preview["approval_preview_id"],
                expected_revision=1,
                action="review",
                confirmation=TRANSITION_CONFIRMATION,
            )

    def test_store_survives_restart(self):
        _, preview = self.create_preview()
        self.store.close()
        reopened = HarnessStateStore(self.path)
        try:
            self.assertEqual(preview, reopened.office_approval_preview(preview["approval_preview_id"]))
        finally:
            reopened.close()
        self.store = HarnessStateStore(self.path)

    def test_atomic_commit_failure_withholds_preview(self):
        failing = FailingPreviewCommitStore(Path(self.temp.name) / "failing.sqlite3")
        try:
            helper = OfficeOperationsHelperService(failing)
            proposals = OfficeTaskProposalService(failing)
            result = helper.review_registration(
                scenario_id="missing-phone", confirmation=HELPER_CONFIRMATION
            )
            proposal = proposals.create_from_helper(
                helper_result=result, confirmation=PROPOSAL_CREATE_CONFIRMATION
            )
            proposal = proposals.transition(
                proposal_id=proposal["proposal_id"], expected_revision=1,
                action="propose", confirmation=PROPOSAL_TRANSITION_CONFIRMATION,
            )
            proposal = proposals.transition(
                proposal_id=proposal["proposal_id"], expected_revision=2,
                action="accept", confirmation=PROPOSAL_TRANSITION_CONFIRMATION,
            )
            with self.assertRaisesRegex(ApprovalPreviewError, "atomically"):
                OfficeApprovalPreviewService(failing, clock=lambda: self.now).create_from_proposal(
                    proposal_id=proposal["proposal_id"],
                    expected_proposal_revision=proposal["revision"],
                    confirmation=CREATE_CONFIRMATION,
                )
            self.assertEqual([], failing.office_approval_previews())
        finally:
            failing.close()

    def test_guardian_requires_every_tokenless_restriction(self):
        baseline = {
            "tenant_id": "tenant-lab-001", "customer_context_id": "customer-context-main",
            "execution_mode": "plan_only", "external_effect": "none",
            "evidence_required": True, "evidence_artifact_ids": ["ev-preview-test"],
            "attended": True, "operator_confirmation": True, "operation": "create",
            "data_classification": "synthetic_fixture_only", "synthetic_data_only": True,
            "free_form_content_allowed": False, "preview_only": True,
            "real_approval_request_allowed": False, "approval_result_allowed": False,
            "approval_token_access_allowed": False, "approval_binding_allowed": False,
            "token_verification_allowed": False, "replay_record_allowed": False,
            "model_call_allowed": False, "tool_execution_allowed": False,
            "arc_dispatch_allowed": False, "connector_access_allowed": False,
            "submission_allowed": False, "approval_required": False,
        }
        allowed = GuardianPolicy().decide("office_approval_preview_manage", baseline)
        self.assertEqual("allow_with_evidence", allowed["decision"])
        unsafe = {
            "operator_confirmation": False, "synthetic_data_only": False,
            "free_form_content_allowed": True, "preview_only": False,
            "real_approval_request_allowed": True, "approval_result_allowed": True,
            "approval_token_access_allowed": True, "approval_binding_allowed": True,
            "token_verification_allowed": True, "replay_record_allowed": True,
            "model_call_allowed": True, "tool_execution_allowed": True,
            "arc_dispatch_allowed": True, "connector_access_allowed": True,
            "submission_allowed": True,
        }
        for key, value in unsafe.items():
            with self.subTest(key=key):
                denied = GuardianPolicy().decide(
                    "office_approval_preview_manage", {**baseline, key: value}
                )
                self.assertEqual("deny", denied["decision"])


if __name__ == "__main__":
    unittest.main()
