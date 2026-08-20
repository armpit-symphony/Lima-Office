"""Safety and behavior tests for the Arc Training/Working harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import unittest

from lima_office.runtime.operator_harness import (
    HarnessBoundaryError,
    HarnessStateStore,
    RuntimeHarness,
    parse_operator_output,
)


class FakeSession:
    def __init__(
        self,
        *,
        supervisor_opt_in: bool = False,
        arc_opt_in: bool = False,
        document_root: Path | None = None,
        responses: list[str] | None = None,
    ) -> None:
        self.args = argparse.Namespace(
            execution_opt_in=supervisor_opt_in,
            execute_granted_capability=arc_opt_in,
            document_root=document_root,
            tenant_id="tenant-lab-001",
            worker_id="arc-worker-001",
        )
        self.worker_port = 41001
        self.supervisor_port = 41002
        self.responses = list(responses or [])
        self.requests: list[dict[str, str]] = []

    def request(self, *, action: str, resource_type: str, resource_id: str) -> str:
        self.requests.append(
            {"action": action, "resource_type": resource_type, "resource_id": resource_id}
        )
        if not self.responses:
            raise AssertionError("fake session has no response")
        return self.responses.pop(0)


def success_output(content: str = "safe document") -> str:
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
        + f"\n--- BEGIN DOCUMENT CONTENT 'report.txt' ({len(content)} bytes) ---\n"
        + content
        + "\n--- END DOCUMENT CONTENT ---\n"
    )


def denied_output(reason: str = "document_not_found") -> str:
    return json.dumps(
        {
            "status": "acknowledged",
            "execution_grant": {"grant_id": "grant:2"},
            "execution": {
                "performed": False,
                "reason_code": reason,
                "side_effects_performed": False,
            },
        }
    )


class RuntimeHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.doCleanups()
        self.temp.cleanup()

    def harness(self, session: FakeSession) -> tuple[RuntimeHarness, HarnessStateStore]:
        store = HarnessStateStore(self.root / "harness-state.db")
        return RuntimeHarness(session, store), store

    def test_defaults_to_training_and_refuses_work(self):
        session = FakeSession()
        harness, store = self.harness(session)
        self.addCleanup(store.close)

        self.assertEqual("training", harness.mode)
        self.assertFalse(harness.working_ready)
        with self.assertRaises(HarnessBoundaryError):
            harness.set_mode("working")
        with self.assertRaises(HarnessBoundaryError):
            harness.governed_read(task_ref="task:1", resource_id="report.txt")
        self.assertEqual([], session.requests)

    def test_working_requires_all_three_startup_gates(self):
        combinations = (
            (False, True, self.root),
            (True, False, self.root),
            (True, True, None),
        )
        for supervisor, arc, document_root in combinations:
            with self.subTest(supervisor=supervisor, arc=arc, root=document_root):
                session = FakeSession(
                    supervisor_opt_in=supervisor,
                    arc_opt_in=arc,
                    document_root=document_root,
                )
                store = HarnessStateStore(self.root / f"state-{supervisor}-{arc}-{document_root is None}.db")
                try:
                    harness = RuntimeHarness(session, store)
                    with self.assertRaises(HarnessBoundaryError):
                        harness.set_mode("working")
                finally:
                    store.close()

    def test_training_instruction_is_durable_without_counting_a_failed_attempt(self):
        harness, store = self.harness(FakeSession())
        result = harness.teach(
            task_ref="document-review",
            instruction="Read the named file only after a grant is issued.",
            authored_by_role="human operator",
        )
        state = harness.state()
        self.assertEqual("instructed", result["status"])
        self.assertEqual(1, state["training_progress"]["gap_count"])
        self.assertEqual(0, state["training_progress"]["attempts"])
        store.close()

        reopened = HarnessStateStore(self.root / "harness-state.db")
        self.addCleanup(reopened.close)
        self.assertEqual(
            "Read the named file only after a grant is issued.",
            reopened.instruction_for(task_ref="document-review", capability="document_read"),
        )

    def test_working_read_uses_real_governed_session_shape_and_routes_success(self):
        session = FakeSession(
            supervisor_opt_in=True,
            arc_opt_in=True,
            document_root=self.root,
            responses=[success_output("quarterly summary")],
        )
        harness, store = self.harness(session)
        self.addCleanup(store.close)
        harness.set_mode("working")

        result = harness.governed_read(task_ref="document-review", resource_id="report.txt")

        self.assertEqual("completed", result["outcome"]["status"])
        self.assertEqual("quarterly summary", result["document_content"])
        self.assertTrue(result["grant_issued"])
        self.assertEqual(
            [{"action": "safe_read", "resource_type": "file", "resource_id": "report.txt"}],
            session.requests,
        )
        self.assertEqual(1, harness.state()["training_progress"]["completed_alone"])
        self.assertNotIn("quarterly summary", json.dumps(store.recent_events()))

    def test_correctable_denial_opens_a_durable_gap_and_escalates(self):
        session = FakeSession(
            supervisor_opt_in=True,
            arc_opt_in=True,
            document_root=self.root,
            responses=[denied_output()],
        )
        harness, store = self.harness(session)
        self.addCleanup(store.close)
        harness.set_mode("working")

        result = harness.governed_read(task_ref="document-review", resource_id="missing.txt")

        self.assertEqual("escalated", result["outcome"]["status"])
        self.assertEqual("correctable", result["outcome"]["disposition"])
        self.assertEqual("system manager", result["outcome"]["escalation"]["from"]["role"])
        self.assertEqual("executive manager", result["outcome"]["escalation"]["to"]["role"])
        state = harness.state()
        self.assertEqual(1, state["training_progress"]["stopped_short"])
        self.assertEqual(1, state["training_progress"]["open_gaps"])

    def test_path_traversal_is_refused_before_the_session(self):
        session = FakeSession(
            supervisor_opt_in=True,
            arc_opt_in=True,
            document_root=self.root,
        )
        harness, store = self.harness(session)
        self.addCleanup(store.close)
        harness.set_mode("working")
        for path in ("../secret.txt", "/absolute.txt", "C:\\secret.txt"):
            with self.subTest(path=path), self.assertRaises(HarnessBoundaryError):
                harness.governed_read(task_ref="task:1", resource_id=path)
        self.assertEqual([], session.requests)

    def test_training_is_refused_while_working(self):
        session = FakeSession(
            supervisor_opt_in=True,
            arc_opt_in=True,
            document_root=self.root,
        )
        harness, store = self.harness(session)
        self.addCleanup(store.close)
        harness.set_mode("working")
        with self.assertRaises(HarnessBoundaryError):
            harness.teach(
                task_ref="task:1",
                instruction="an instruction",
                authored_by_role="operator",
            )


class OperatorOutputTests(unittest.TestCase):
    def test_rejects_non_json_operator_output(self):
        with self.assertRaises(HarnessBoundaryError):
            parse_operator_output("not-json")

    def test_extracts_document_without_marker_lines(self):
        payload, content = parse_operator_output(success_output("hello"))
        self.assertEqual("acknowledged", payload["status"])
        self.assertEqual("hello", content)


if __name__ == "__main__":
    unittest.main()
