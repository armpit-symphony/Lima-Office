"""Safety and contract tests for the bounded Office Operations Helper."""

from __future__ import annotations

import json
import unittest

from lima_office.guardian import GuardianPolicy
from lima_office.runtime.office_helper import (
    HELPER_CONFIRMATION,
    OfficeHelperError,
    OfficeOperationsHelperService,
)


class RecordingStore:
    def __init__(self, *, fail_at: int | None = None) -> None:
        self.fail_at = fail_at
        self.events: list[dict] = []
        self.calls = 0

    def record_event(self, event_type, payload):
        self.calls += 1
        if self.fail_at == self.calls:
            raise OSError("synthetic evidence failure")
        event = {"event_type": event_type, "payload": dict(payload)}
        self.events.append(event)
        return f"harness-event:helper-{self.calls}"


class DenyGuardian:
    def decide(self, _action, context):
        return GuardianPolicy().decide("unknown_helper_action", context)


class OfficeOperationsHelperTests(unittest.TestCase):
    def test_missing_field_review_is_contract_valid_and_non_executing(self):
        store = RecordingStore()
        service = OfficeOperationsHelperService(store)

        result = service.review_registration(
            scenario_id="missing-phone",
            confirmation=HELPER_CONFIRMATION,
        )

        self.assertEqual("completed", result["status"])
        self.assertEqual("needs_human_input", result["disposition"])
        self.assertEqual("phone", result["findings"][0]["field"])
        self.assertEqual("missing_value", result["findings"][0]["reason_code"])
        self.assertTrue(result["human_review_required"])
        for flag in (
            "model_called", "tools_used", "memory_used", "approval_requested",
            "arc_dispatched", "connector_accessed", "submission_allowed",
            "external_side_effects",
        ):
            self.assertFalse(result[flag], flag)
        self.assertEqual(3, len(store.events))
        encoded = json.dumps(store.events, sort_keys=True)
        self.assertNotIn("Avery Sample", encoded)
        self.assertNotIn("555-", encoded)
        self.assertNotIn("example.test", encoded)

    def test_complete_synthetic_scenario_still_requires_owner_review(self):
        result = OfficeOperationsHelperService(RecordingStore()).review_registration(
            scenario_id="complete-contact",
            confirmation=HELPER_CONFIRMATION,
        )
        self.assertEqual("ready_for_owner_review", result["disposition"])
        self.assertEqual([], result["findings"])
        self.assertIn("helper_ready_for_owner_review", result["reason_codes"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["submission_allowed"])

    def test_state_contains_only_fixed_scenario_metadata(self):
        state = OfficeOperationsHelperService(RecordingStore()).state_summary()
        self.assertTrue(state["runtime_enabled"])
        self.assertTrue(state["synthetic_data_only"])
        self.assertTrue(state["deterministic_review"])
        self.assertFalse(state["model_calls_enabled"])
        self.assertFalse(state["tools_enabled"])
        self.assertFalse(state["memory_enabled"])
        self.assertFalse(state["may_dispatch_workers"])
        encoded = json.dumps(state, sort_keys=True)
        self.assertNotIn("synthetic_profile", encoded)
        self.assertNotIn("Jordan Example", encoded)

    def test_unknown_scenario_and_missing_confirmation_write_no_evidence(self):
        for scenario, confirmation in (
            ("customer-upload", HELPER_CONFIRMATION),
            ("missing-phone", "yes"),
        ):
            with self.subTest(scenario=scenario, confirmation=confirmation):
                store = RecordingStore()
                service = OfficeOperationsHelperService(store)
                with self.assertRaises(OfficeHelperError):
                    service.review_registration(
                        scenario_id=scenario,
                        confirmation=confirmation,
                    )
                self.assertEqual([], store.events)

    def test_each_evidence_failure_fails_closed(self):
        expected = {
            1: "Pre-action evidence",
            2: "Guardian evidence",
            3: "Post-action evidence",
        }
        for fail_at, message in expected.items():
            with self.subTest(fail_at=fail_at):
                with self.assertRaisesRegex(OfficeHelperError, message):
                    OfficeOperationsHelperService(
                        RecordingStore(fail_at=fail_at)
                    ).review_registration(
                        scenario_id="missing-phone",
                        confirmation=HELPER_CONFIRMATION,
                    )

    def test_guardian_denial_stops_before_helper_review(self):
        store = RecordingStore()
        service = OfficeOperationsHelperService(store, guardian=DenyGuardian())
        with self.assertRaisesRegex(OfficeHelperError, "Guardian denied"):
            service.review_registration(
                scenario_id="missing-phone",
                confirmation=HELPER_CONFIRMATION,
            )
        self.assertEqual(1, len(store.events))

    def test_guardian_requires_every_helper_restriction(self):
        baseline = {
            "tenant_id": "tenant-lab-001",
            "customer_context_id": "customer-context-main",
            "execution_mode": "plan_only",
            "external_effect": "none",
            "evidence_required": True,
            "evidence_artifact_ids": ["ev-helper-test"],
            "attended": True,
            "operator_confirmation": True,
            "helper_role": "office_operations_helper",
            "review_type": "registration_sop_review",
            "data_classification": "synthetic_fixture_only",
            "synthetic_data_only": True,
            "deterministic_review": True,
            "model_call_allowed": False,
            "tool_execution_allowed": False,
            "memory_access_allowed": False,
            "approval_token_access_allowed": False,
            "arc_dispatch_allowed": False,
            "connector_access_allowed": False,
            "submission_allowed": False,
            "approval_required": False,
        }
        allowed = GuardianPolicy().decide("helper_synthetic_review", baseline)
        self.assertEqual("allow_with_evidence", allowed["decision"])

        unsafe_values = {
            "operator_confirmation": False,
            "synthetic_data_only": False,
            "model_call_allowed": True,
            "tool_execution_allowed": True,
            "memory_access_allowed": True,
            "approval_token_access_allowed": True,
            "arc_dispatch_allowed": True,
            "connector_access_allowed": True,
            "submission_allowed": True,
        }
        for key, value in unsafe_values.items():
            with self.subTest(key=key):
                context = {**baseline, key: value}
                denied = GuardianPolicy().decide("helper_synthetic_review", context)
                self.assertEqual("deny", denied["decision"])


if __name__ == "__main__":
    unittest.main()
