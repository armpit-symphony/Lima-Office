"""Safety, durability, and state tests for Supervisor task proposals."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from lima_office.guardian import GuardianPolicy
from lima_office.runtime.office_helper import (
    HELPER_CONFIRMATION,
    OfficeHelperError,
    OfficeOperationsHelperService,
)
from lima_office.runtime.operator_harness import HarnessStateStore
from lima_office.runtime.task_proposal import (
    CREATE_CONFIRMATION,
    EDIT_CONFIRMATION,
    TRANSITION_CONFIRMATION,
    OfficeTaskProposalService,
    TaskProposalError,
)


class FailingCommitStore(HarnessStateStore):
    def commit_office_proposal(self, *args, **kwargs):
        raise OSError("synthetic atomic commit failure")


class OfficeTaskProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lima-task-proposal-")
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = HarnessStateStore(self.path)
        self.helper = OfficeOperationsHelperService(self.store)
        self.service = OfficeTaskProposalService(self.store)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def helper_result(self, scenario_id="missing-phone"):
        return self.helper.review_registration(
            scenario_id=scenario_id,
            confirmation=HELPER_CONFIRMATION,
        )

    def create(self, scenario_id="missing-phone"):
        return self.service.create_from_helper(
            helper_result=self.helper_result(scenario_id),
            confirmation=CREATE_CONFIRMATION,
        )

    def test_create_is_contract_valid_durable_and_non_executing(self):
        proposal = self.create()

        self.assertEqual("draft", proposal["state"])
        self.assertEqual(1, proposal["revision"])
        self.assertEqual("normal", proposal["priority"])
        self.assertEqual(["phone"], proposal["issue_fields"])
        self.assertTrue(proposal["approval_required_for_future_execution"])
        self.assertIsNone(proposal["assigned_worker_id"])
        for flag in (
            "approval_token_issued", "arc_dispatch_allowed", "arc_dispatched",
            "model_called", "tools_used", "connector_accessed",
            "submission_allowed", "external_side_effects",
        ):
            self.assertFalse(proposal[flag], flag)

        restored = self.store.office_proposal(proposal["proposal_id"])
        self.assertEqual(proposal, restored)
        events = self.store.recent_events(limit=20)
        self.assertEqual("office_task_proposal_change_committed", events[0]["event_type"])
        self.assertEqual(proposal["post_action_evidence_ref"], events[0]["event_id"])
        encoded = json.dumps(events, sort_keys=True)
        self.assertNotIn("Avery Sample", encoded)
        self.assertNotIn("example.test", encoded)

    def test_edit_propose_and_accept_never_grant_authority(self):
        proposal = self.create("complete-contact")
        proposal = self.service.edit(
            proposal_id=proposal["proposal_id"],
            expected_revision=proposal["revision"],
            priority="low",
            selected_step_ids=[
                "review_synthetic_scenario",
                "owner_review_prepared_form",
            ],
            confirmation=EDIT_CONFIRMATION,
        )
        self.assertEqual(2, proposal["revision"])
        self.assertEqual("low", proposal["priority"])

        proposal = self.service.transition(
            proposal_id=proposal["proposal_id"],
            expected_revision=proposal["revision"],
            action="propose",
            confirmation=TRANSITION_CONFIRMATION,
        )
        self.assertEqual("proposed", proposal["state"])
        proposal = self.service.transition(
            proposal_id=proposal["proposal_id"],
            expected_revision=proposal["revision"],
            action="accept",
            confirmation=TRANSITION_CONFIRMATION,
        )
        self.assertEqual("accepted_for_future_approval", proposal["state"])
        self.assertEqual("accepted", proposal["owner_decision"])
        self.assertFalse(proposal["approval_token_issued"])
        self.assertFalse(proposal["arc_dispatch_allowed"])
        self.assertFalse(proposal["arc_dispatched"])
        self.assertIsNone(proposal["assigned_worker_id"])

    def test_deny_and_cancel_paths_are_terminal(self):
        denied = self.create()
        denied = self.service.transition(
            proposal_id=denied["proposal_id"], expected_revision=1,
            action="propose", confirmation=TRANSITION_CONFIRMATION,
        )
        denied = self.service.transition(
            proposal_id=denied["proposal_id"], expected_revision=2,
            action="deny", confirmation=TRANSITION_CONFIRMATION,
        )
        self.assertEqual("denied", denied["state"])
        with self.assertRaises(TaskProposalError):
            self.service.transition(
                proposal_id=denied["proposal_id"], expected_revision=3,
                action="accept", confirmation=TRANSITION_CONFIRMATION,
            )

        cancelled = self.create("invalid-email")
        cancelled = self.service.transition(
            proposal_id=cancelled["proposal_id"], expected_revision=1,
            action="cancel", confirmation=TRANSITION_CONFIRMATION,
        )
        self.assertEqual("cancelled", cancelled["state"])

    def test_stale_revision_and_free_form_values_fail_before_commit(self):
        proposal = self.create()
        event_count = len(self.store.recent_events(limit=100))
        for call in (
            lambda: self.service.edit(
                proposal_id=proposal["proposal_id"], expected_revision=99,
                priority="urgent", selected_step_ids=["email_customer"],
                confirmation=EDIT_CONFIRMATION,
            ),
            lambda: self.service.edit(
                proposal_id=proposal["proposal_id"], expected_revision=1,
                priority="normal", selected_step_ids=["email_customer"],
                confirmation=EDIT_CONFIRMATION,
            ),
        ):
            with self.subTest(call=call):
                with self.assertRaises(TaskProposalError):
                    call()
        self.assertEqual(event_count, len(self.store.recent_events(limit=100)))

    def test_duplicate_source_and_cross_tenant_result_fail_closed(self):
        helper_result = self.helper_result()
        self.service.create_from_helper(
            helper_result=helper_result, confirmation=CREATE_CONFIRMATION
        )
        with self.assertRaisesRegex(TaskProposalError, "already has"):
            self.service.create_from_helper(
                helper_result=helper_result, confirmation=CREATE_CONFIRMATION
            )
        other_tenant = {**self.helper_result("invalid-postal-code"), "tenant_id": "other"}
        with self.assertRaisesRegex(TaskProposalError, "different tenant"):
            self.service.create_from_helper(
                helper_result=other_tenant, confirmation=CREATE_CONFIRMATION
            )

    def test_atomic_store_rolls_back_completion_event_on_unique_source_failure(self):
        proposal = self.create()
        duplicate = {
            **proposal,
            "proposal_id": "task-proposal:duplicate",
            "revision": 1,
            "idempotency_key": "idem-task-proposal-duplicate-r1",
        }
        event_id = "harness-event:must-roll-back"
        with self.assertRaises(Exception):
            self.store.commit_office_proposal(
                duplicate,
                event_id=event_id,
                event_type="office_task_proposal_change_committed",
                event_payload={"synthetic": True},
                expected_revision=None,
            )
        self.assertIsNone(self.store.office_proposal("task-proposal:duplicate"))
        self.assertNotIn(
            event_id,
            [item["event_id"] for item in self.store.recent_events(limit=100)],
        )

    def test_store_survives_restart(self):
        proposal = self.create()
        self.store.close()
        reopened = HarnessStateStore(self.path)
        try:
            restored = OfficeTaskProposalService(reopened).state_summary()["proposals"]
            self.assertEqual([proposal], restored)
        finally:
            reopened.close()
        self.store = HarnessStateStore(self.path)

    def test_helper_result_must_exist_in_current_process(self):
        result = self.helper_result()
        self.assertEqual(result, self.helper.proposal_source(result["helper_result_id"]))
        with self.assertRaises(OfficeHelperError):
            self.helper.proposal_source("helper-result:unknown")

    def test_atomic_commit_failure_withholds_proposal(self):
        failing_path = Path(self.temp.name) / "failing.sqlite3"
        failing = FailingCommitStore(failing_path)
        try:
            helper = OfficeOperationsHelperService(failing)
            result = helper.review_registration(
                scenario_id="missing-phone", confirmation=HELPER_CONFIRMATION
            )
            with self.assertRaisesRegex(TaskProposalError, "atomically"):
                OfficeTaskProposalService(failing).create_from_helper(
                    helper_result=result, confirmation=CREATE_CONFIRMATION
                )
            self.assertEqual([], failing.office_proposals())
        finally:
            failing.close()

    def test_guardian_requires_every_proposal_restriction(self):
        baseline = {
            "tenant_id": "tenant-lab-001",
            "customer_context_id": "customer-context-main",
            "execution_mode": "plan_only",
            "external_effect": "none",
            "evidence_required": True,
            "evidence_artifact_ids": ["ev-task-proposal-test"],
            "attended": True,
            "operator_confirmation": True,
            "operation": "create",
            "data_classification": "synthetic_fixture_only",
            "synthetic_data_only": True,
            "free_form_content_allowed": False,
            "model_call_allowed": False,
            "tool_execution_allowed": False,
            "approval_token_access_allowed": False,
            "arc_dispatch_allowed": False,
            "connector_access_allowed": False,
            "submission_allowed": False,
            "approval_required": False,
        }
        allowed = GuardianPolicy().decide("office_task_proposal_manage", baseline)
        self.assertEqual("allow_with_evidence", allowed["decision"])
        unsafe = {
            "operator_confirmation": False,
            "synthetic_data_only": False,
            "free_form_content_allowed": True,
            "model_call_allowed": True,
            "tool_execution_allowed": True,
            "approval_token_access_allowed": True,
            "arc_dispatch_allowed": True,
            "connector_access_allowed": True,
            "submission_allowed": True,
        }
        for key, value in unsafe.items():
            with self.subTest(key=key):
                denied = GuardianPolicy().decide(
                    "office_task_proposal_manage", {**baseline, key: value}
                )
                self.assertEqual("deny", denied["decision"])


if __name__ == "__main__":
    unittest.main()
