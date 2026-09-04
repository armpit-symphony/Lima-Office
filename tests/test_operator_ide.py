"""Behavior tests for the Arc operator IDE composition layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import unittest

from lima_office.runtime.operator_harness import HarnessBoundaryError
from lima_office.runtime.operator_ide import (
    DOCUMENT_PAGE_CHARS,
    OperatorIDEHarness,
    OperatorIDEStateStore,
)


class FakeSession:
    def __init__(self, root: Path, responses: list[str] | None = None) -> None:
        self.args = argparse.Namespace(
            execution_opt_in=True,
            execute_granted_capability=True,
            document_root=root,
            tenant_id="tenant-lab-001",
            worker_id="arc-worker-001",
        )
        self.worker_port = 41001
        self.supervisor_port = 41002
        self.responses = list(responses or [])
        self.requests: list[dict[str, str]] = []

    def request(self, *, action: str, resource_type: str, resource_id: str) -> str:
        self.requests.append(
            {
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )
        return self.responses.pop(0)


class FakeArcIDE:
    def __init__(self) -> None:
        self.resolved_refs: list[str] = []
        self.decisions: list[dict[str, str]] = []

    def snapshot(self, *, resolved_task_refs=()):
        self.resolved_refs = list(resolved_task_refs)
        return {
            "record_type": "arc_operator_ide_snapshot",
            "queue_standing": {"workable": len(self.resolved_refs)},
            "next_task": None,
            "tasks": [],
            "pending_approvals": [],
        }

    def decide(self, **payload):
        self.decisions.append(payload)
        return {
            "approval": {
                "approval_id": payload["approval_id"],
                "status": payload["decision"],
            },
            "execution_allowed": False,
            "execution_status": "approved_but_not_executable_in_v0_6",
        }


def success_output(content: str) -> str:
    return (
        json.dumps(
            {
                "status": "acknowledged",
                "decision_id": "decision:1",
                "execution_grant": {"grant_id": "grant:1"},
                "execution": {
                    "performed": True,
                    "capability": "document_read",
                    "byte_count": len(content.encode("utf-8")),
                    "side_effects_performed": False,
                },
            }
        )
        + "\n--- BEGIN DOCUMENT CONTENT 'report.txt' (1 bytes) ---\n"
        + content
        + "\n--- END DOCUMENT CONTENT ---\n"
    )


def listing_output(entries: list[dict[str, object]]) -> str:
    return json.dumps(
        {
            "status": "acknowledged",
            "decision_id": "decision:list-1",
            "execution_grant": {"grant_id": "grant:list-1"},
            "execution": {
                "performed": True,
                "capability": "document_list",
                "resource_id": ".",
                "entry_count": len(entries),
                "entry_limit": 200,
                "truncated": False,
                "entries": entries,
                "side_effects_performed": False,
            },
        }
    )


class OperatorIDEHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = OperatorIDEStateStore(self.root / "state.db")
        self.addCleanup(self.store.close)
        self.arc = FakeArcIDE()

    def harness(self, responses: list[str] | None = None) -> OperatorIDEHarness:
        return OperatorIDEHarness(
            FakeSession(self.root, responses), self.store, arc_ide=self.arc
        )

    def test_resolving_observed_gap_produces_arc_resolution_ref(self):
        harness = self.harness(
            [
                json.dumps(
                    {
                        "status": "acknowledged",
                        "execution_grant": {"grant_id": "grant:1"},
                        "execution": {
                            "performed": False,
                            "reason_code": "document_not_found",
                            "side_effects_performed": False,
                        },
                    }
                )
            ]
        )
        harness.set_mode("working")
        harness.governed_read(task_ref="task:waiting", resource_id="missing.txt")
        harness.set_mode("training")
        gap_id = harness.state()["gaps"][0]["gap_id"]

        result = harness.resolve_gap(
            gap_id=gap_id,
            instruction="Use the corrected document name.",
            resolved_by_role="system manager",
        )
        state = harness.state()

        self.assertEqual("task:waiting", result["resolved_task_ref"])
        self.assertIn("task:waiting", self.arc.resolved_refs)
        self.assertEqual(1, state["training_progress"]["instructed_gaps"])

    def test_large_document_is_paged_and_never_persisted(self):
        content = "x" * (DOCUMENT_PAGE_CHARS + 27)
        harness = self.harness([success_output(content)])
        harness.set_mode("working")

        result = harness.governed_read(task_ref="task:large", resource_id="large.txt")
        first = result["document_page"]
        second = harness.document_page(
            content_id=first["content_id"], offset=first["next_offset"]
        )

        self.assertEqual(DOCUMENT_PAGE_CHARS, len(first["content"]))
        self.assertTrue(first["has_more"])
        self.assertEqual(27, len(second["content"]))
        self.assertFalse(second["has_more"])
        self.assertNotIn(content, json.dumps(self.store.recent_events()))

    def test_document_buffers_clear_on_return_to_training(self):
        harness = self.harness([success_output("page")])
        harness.set_mode("working")
        result = harness.governed_read(task_ref="task:1", resource_id="r.txt")
        harness.set_mode("training")
        harness.set_mode("working")
        with self.assertRaises(HarnessBoundaryError):
            harness.document_page(
                content_id=result["document_page"]["content_id"], offset=0
            )

    def test_approval_requires_working_mode_and_remains_non_executable(self):
        harness = self.harness()
        with self.assertRaises(HarnessBoundaryError):
            harness.decide_approval(
                approval_id="approval-1",
                decision="approved",
                operator_id="operator-1",
                reason="Reviewed.",
            )
        harness.set_mode("working")
        result = harness.decide_approval(
            approval_id="approval-1",
            decision="approved",
            operator_id="operator-1",
            reason="Reviewed.",
        )
        self.assertFalse(result["execution_allowed"])
        self.assertEqual("operator-1", self.arc.decisions[0]["operator_id"])

    def test_customer_ladder_is_validated_and_durable(self):
        harness = self.harness()
        configured = harness.configure_ladder(
            {
                "tiers": [
                    {
                        "role": "IT lead",
                        "kind": "system_manager",
                        "may_permit": ["document_read"],
                    },
                    {
                        "role": "General manager",
                        "kind": "executive",
                        "may_permit": ["document_read"],
                    },
                    {
                        "role": "Owner",
                        "kind": "human",
                        "may_permit": ["*"],
                    },
                ]
            }
        )
        self.assertEqual("Owner", configured["terminal_role"])

        reopened = OperatorIDEStateStore(self.root / "state.db")
        self.addCleanup(reopened.close)
        restored = OperatorIDEHarness(
            FakeSession(self.root), reopened, arc_ide=FakeArcIDE()
        )
        self.assertEqual(
            "Owner", restored.state()["escalation_ladder"]["terminal_role"]
        )

    def test_governed_listing_is_sanitized_routed_and_not_persisted(self):
        entries = [
            {
                "name": "report.txt",
                "relative_path": r"C:\private\report.txt",
                "kind": "file",
                "byte_count": 12,
            },
            {
                "name": "team",
                "relative_path": "/outside/team",
                "kind": "directory",
                "byte_count": None,
            },
        ]
        session = FakeSession(self.root, [listing_output(entries)])
        harness = OperatorIDEHarness(session, self.store, arc_ide=self.arc)
        harness.set_mode("working")

        result = harness.governed_list(task_ref="task:list", resource_id=".")

        self.assertEqual(
            [{"action": "safe_list", "resource_type": "file", "resource_id": "."}],
            session.requests,
        )
        self.assertTrue(result["execution"]["performed"])
        self.assertEqual(
            ["report.txt", "team"],
            [entry["relative_path"] for entry in result["execution"]["entries"]],
        )
        self.assertEqual(
            ["document_list", "document_read"],
            harness.state()["allowed_working_capabilities"],
        )
        evidence = json.dumps(self.store.recent_events())
        self.assertNotIn("report.txt", evidence)
        self.assertNotIn(r"C:\private", evidence)

    def test_malformed_listing_fails_closed_without_exposing_entries(self):
        session = FakeSession(
            self.root,
            [
                listing_output(
                    [
                        {
                            "name": "bad\nname.txt",
                            "relative_path": "bad\nname.txt",
                            "kind": "file",
                            "byte_count": 1,
                        }
                    ]
                )
            ],
        )
        harness = OperatorIDEHarness(session, self.store, arc_ide=self.arc)
        harness.set_mode("working")

        result = harness.governed_list(task_ref="task:bad-list", resource_id=".")

        self.assertFalse(result["execution"]["performed"])
        self.assertEqual([], result["execution"]["entries"])
        self.assertIn("arc_listing_malformed", result["reason_codes"])
        self.assertEqual("blocked", result["outcome"]["status"])

    def test_listing_requires_working_mode_and_a_safe_relative_directory(self):
        session = FakeSession(self.root)
        harness = OperatorIDEHarness(session, self.store, arc_ide=self.arc)

        with self.assertRaises(HarnessBoundaryError):
            harness.governed_list(task_ref="task:list", resource_id=".")
        harness.set_mode("working")
        for directory in ("../outside", r"C:\outside", ".hidden"):
            with self.subTest(directory=directory):
                with self.assertRaises(HarnessBoundaryError):
                    harness.governed_list(
                        task_ref="task:list",
                        resource_id=directory,
                    )
        self.assertEqual([], session.requests)

    def test_registration_practice_suite_is_durable_synthetic_and_blocked(self):
        harness = self.harness()

        catalog = harness.registration_catalog()
        result = harness.run_registration_practice_suite()
        state = harness.state()["registration_practice"]

        self.assertEqual(25, len(catalog["scenarios"]))
        self.assertEqual(3, len(catalog["templates"]))
        self.assertEqual("passed", result["status"])
        self.assertEqual(25, result["passed_count"])
        self.assertEqual(0, result["failed_count"])
        self.assertEqual(100, result["average_score"])
        self.assertFalse(result["submission_allowed"])
        self.assertFalse(result["browser_automation_allowed"])
        self.assertFalse(result["external_side_effects"])
        self.assertEqual(25, state["attempt_count"])
        self.assertEqual(25, state["passed_count"])
        self.assertEqual(10, len(state["recent_attempts"]))

        evidence = json.dumps(self.store.recent_events())
        self.assertNotIn("Practice Person 01", evidence)
        self.assertNotIn("practice01@example.test", evidence)
        self.assertIn("registration_practice_suite_completed", evidence)

        reopened = OperatorIDEStateStore(self.root / "state.db")
        self.addCleanup(reopened.close)
        restored = OperatorIDEHarness(
            FakeSession(self.root), reopened, arc_ide=FakeArcIDE()
        )
        self.assertEqual(
            25, restored.state()["registration_practice"]["attempt_count"]
        )

    def test_single_registration_practice_flags_gap_without_inventing(self):
        harness = self.harness()

        result = harness.run_registration_practice(
            scenario_id="service-intake-missing-phone-02"
        )

        self.assertTrue(result["passed"])
        self.assertEqual("", result["prepared_fields"]["phone"])
        self.assertEqual("phone", result["issues"][0]["field"])
        self.assertEqual("NEEDS_HUMAN_INPUT", result["issues"][0]["status"])
        self.assertFalse(result["submission_allowed"])
        self.assertFalse(result["external_side_effects"])
        self.assertTrue(result["attempt_id"].startswith("registration-practice:"))
        self.assertTrue(result["evidence_ref"].startswith("harness-event:"))

    def test_human_approved_complete_draft_creates_only_local_mock_receipt(self):
        harness = self.harness()
        attempt = harness.run_registration_practice(
            scenario_id="community-program-complete-01"
        )

        result = harness.review_registration_practice(
            attempt_id=attempt["attempt_id"], decision="approved"
        )
        state = harness.state()["registration_practice"]

        self.assertEqual("mock_submitted", result["outcome"])
        self.assertEqual("allow_with_evidence", result["guardian_decision"])
        self.assertTrue(result["mock_submission_performed"])
        self.assertFalse(result["external_submission_allowed"])
        self.assertFalse(result["external_side_effects"])
        self.assertEqual(1, state["review_count"])
        self.assertEqual(1, state["mock_submitted_count"])
        evidence = json.dumps(self.store.recent_events())
        self.assertIn("registration_mock_review_requested", evidence)
        self.assertIn("registration_mock_review_completed", evidence)
        self.assertNotIn("Practice Person 01", evidence)

        with self.assertRaisesRegex(HarnessBoundaryError, "already reviewed"):
            harness.review_registration_practice(
                attempt_id=attempt["attempt_id"], decision="approved"
            )

    def test_unresolved_draft_is_guardian_blocked_and_rejection_is_recorded(self):
        harness = self.harness()
        incomplete = harness.run_registration_practice(
            scenario_id="service-intake-missing-phone-02"
        )
        blocked = harness.review_registration_practice(
            attempt_id=incomplete["attempt_id"], decision="approved"
        )
        complete = harness.run_registration_practice(
            scenario_id="community-program-complete-01"
        )
        rejected = harness.review_registration_practice(
            attempt_id=complete["attempt_id"], decision="rejected"
        )

        self.assertEqual("blocked", blocked["outcome"])
        self.assertEqual("deny", blocked["guardian_decision"])
        self.assertFalse(blocked["mock_submission_performed"])
        self.assertEqual("operator_rejected", rejected["outcome"])
        self.assertIsNone(rejected["guardian_decision"])
        state = harness.state()["registration_practice"]
        self.assertEqual(1, state["mock_blocked_count"])
        self.assertEqual(1, state["operator_rejected_count"])

    def test_registration_practice_requires_training_mode(self):
        harness = self.harness()
        harness.set_mode("working")

        with self.assertRaisesRegex(
            HarnessBoundaryError, "registration practice requires training mode"
        ):
            harness.run_registration_practice(scenario_id="complete-contact")
        with self.assertRaisesRegex(
            HarnessBoundaryError, "registration practice requires training mode"
        ):
            harness.run_registration_practice_suite()
        with self.assertRaisesRegex(
            HarnessBoundaryError, "registration mock review requires training mode"
        ):
            harness.review_registration_practice(
                attempt_id="registration-practice:none", decision="approved"
            )
        self.assertEqual(
            0, harness.state()["registration_practice"]["attempt_count"]
        )


if __name__ == "__main__":
    unittest.main()
