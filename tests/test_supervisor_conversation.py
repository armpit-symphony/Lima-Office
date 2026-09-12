"""Tests for the attended, Guardian-gated Supervisor subscription turn."""

from __future__ import annotations

import copy
import json
import unittest

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.supervisor_conversation import (
    CodexRunResult,
    SupervisorConversationError,
    SupervisorConversationService,
    TURN_CONFIRMATION,
)


class RecordingStore:
    def __init__(self, *, fail_at: int | None = None):
        self.events = []
        self.fail_at = fail_at

    def record_event(self, event_type, payload):
        if self.fail_at is not None and len(self.events) + 1 == self.fail_at:
            raise OSError("synthetic evidence failure")
        reference = f"harness-event:test-{len(self.events) + 1}"
        self.events.append((event_type, copy.deepcopy(dict(payload)), reference))
        return reference


class StubRunner:
    def __init__(self, *, tool_event_count=0, status="profile_detected"):
        self.calls = []
        self.tool_event_count = tool_event_count
        self.status = status

    def readiness(self):
        return {"status": self.status, "detail": "synthetic readiness"}

    def run(self, message):
        self.calls.append(message)
        return CodexRunResult(
            text="A draft-only plan with no external action.",
            model_name="test-subscription-model",
            tool_event_count=self.tool_event_count,
        )


class SupervisorConversationServiceTests(unittest.TestCase):
    def test_completed_turn_is_guardian_gated_evidenced_and_not_persisted_raw(self):
        store = RecordingStore()
        runner = StubRunner()
        service = SupervisorConversationService(store, runner=runner)

        result = service.turn(
            message="Summarize today's synthetic registration priorities.",
            confirmation=TURN_CONFIRMATION,
            data_classification="internal",
        )

        ContractValidator().validate(result, "supervisor.conversation.turn")
        self.assertEqual("completed", result["status"])
        self.assertFalse(result["tools_enabled"])
        self.assertFalse(result["external_side_effects"])
        self.assertEqual(1, len(runner.calls))
        persisted = json.dumps(store.events)
        self.assertNotIn("Summarize today's synthetic", persisted)
        self.assertNotIn("A draft-only plan", persisted)
        self.assertIn("message_sha256", persisted)
        self.assertEqual(
            [
                "supervisor_conversation_requested",
                "supervisor_model_call_authorized",
                "supervisor_conversation_completed",
            ],
            [event[0] for event in store.events],
        )

    def test_missing_confirmation_or_sensitive_classification_never_calls_model(self):
        for confirmation, data_classification in (
            ("", "internal"),
            (TURN_CONFIRMATION, "customer_confidential"),
        ):
            store = RecordingStore()
            runner = StubRunner()
            service = SupervisorConversationService(store, runner=runner)
            with self.subTest(data_classification=data_classification):
                with self.assertRaises(SupervisorConversationError):
                    service.turn(
                        message="Synthetic test",
                        confirmation=confirmation,
                        data_classification=data_classification,
                    )
            self.assertEqual([], runner.calls)
            self.assertEqual([], store.events)

    def test_pre_or_guardian_evidence_failure_denies_before_model_call(self):
        for fail_at in (1, 2):
            store = RecordingStore(fail_at=fail_at)
            runner = StubRunner()
            service = SupervisorConversationService(store, runner=runner)
            with self.subTest(fail_at=fail_at), self.assertRaises(
                SupervisorConversationError
            ):
                service.turn(
                    message="Synthetic test",
                    confirmation=TURN_CONFIRMATION,
                    data_classification="internal",
                )
            self.assertEqual([], runner.calls)

    def test_post_action_evidence_failure_withholds_response(self):
        store = RecordingStore(fail_at=3)
        runner = StubRunner()
        service = SupervisorConversationService(store, runner=runner)
        with self.assertRaisesRegex(SupervisorConversationError, "response withheld"):
            service.turn(
                message="Synthetic test",
                confirmation=TURN_CONFIRMATION,
                data_classification="internal",
            )
        self.assertEqual(1, len(runner.calls))

    def test_tool_event_rejects_model_response_and_records_failure(self):
        store = RecordingStore()
        runner = StubRunner(tool_event_count=1)
        service = SupervisorConversationService(store, runner=runner)
        with self.assertRaisesRegex(SupervisorConversationError, "disabled tool"):
            service.turn(
                message="Synthetic test",
                confirmation=TURN_CONFIRMATION,
                data_classification="internal",
            )
        self.assertEqual("supervisor_conversation_failed", store.events[-1][0])

    def test_unavailable_subscription_fails_before_evidence_or_model(self):
        store = RecordingStore()
        runner = StubRunner(status="sign_in_needed")
        service = SupervisorConversationService(store, runner=runner)
        with self.assertRaises(SupervisorConversationError):
            service.turn(
                message="Synthetic test",
                confirmation=TURN_CONFIRMATION,
                data_classification="internal",
            )
        self.assertEqual([], store.events)
        self.assertEqual([], runner.calls)


if __name__ == "__main__":
    unittest.main()
