"""HTTP and console-projection tests for tokenless task proposals."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import Request, urlopen

from lima_office.runtime.supervisor_console import build_supervisor_console_state


class TaskProposalConsoleTests(unittest.TestCase):
    def test_projection_includes_only_bounded_proposal_fields(self):
        proposal = {
            "proposal_id": "task-proposal:test",
            "revision": 1,
            "state": "draft",
            "source_helper_result_id": "helper-result:test",
            "scenario_id": "missing-phone",
            "task_class": "form_preparation",
            "priority": "normal",
            "selected_step_ids": ["review_synthetic_scenario"],
            "issue_fields": ["phone"],
            "transition_reason_codes": ["task_proposal_created"],
            "owner_decision": "none",
            "approval_token_issued": False,
            "arc_dispatched": False,
            "secret": "must-not-appear",
        }
        result = build_supervisor_console_state(
            {"mode": "training", "office_integration": {"connected": True}},
            {},
            proposal_state={
                "runtime_enabled": True,
                "allowed_priorities": ["low", "normal", "urgent"],
                "allowed_step_ids": ["review_synthetic_scenario", "email_customer"],
                "proposals": [proposal],
            },
        )
        self.assertTrue(result["work"]["proposal_runtime_enabled"])
        self.assertEqual(1, result["work"]["proposal_count"])
        self.assertEqual(["low", "normal"], result["work"]["proposal_priorities"])
        self.assertEqual(
            ["review_synthetic_scenario"], result["work"]["proposal_step_ids"]
        )
        self.assertNotIn("must-not-appear", json.dumps(result))

    def test_ui_contains_attended_proposal_controls_without_polling(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "ui" / "lima_office_supervisor_console.html").read_text(
            encoding="utf-8"
        )
        for endpoint in (
            "/api/office/proposals/create",
            "/api/office/proposals/edit",
            "/api/office/proposals/transition",
        ):
            self.assertIn(endpoint, source)
        self.assertIn("CREATE SYNTHETIC TASK DRAFT", source)
        self.assertIn("accepted for a future approval request only", source.lower())
        self.assertIn("No approval token", source)
        self.assertNotIn("setInterval", source)


class TaskProposalHTTPTests(unittest.TestCase):
    def test_harness_routes_create_edit_and_transition(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "arc-runtime-harness.py"
        spec = importlib.util.spec_from_file_location("_arc_runtime_harness_proposal_test", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeHarness:
            mode = "training"
            def state(self):
                return {"mode": "training", "office_integration": {"connected": True}}

        class FakeHelper:
            def state_summary(self):
                return {"runtime_enabled": True, "status": "ready", "scenarios": []}
            def proposal_source(self, helper_result_id):
                return {"helper_result_id": helper_result_id}

        class FakeProposals:
            def __init__(self):
                self.calls = []
            def state_summary(self):
                return {"runtime_enabled": True, "proposals": []}
            def create_from_helper(self, **payload):
                self.calls.append(("create", payload))
                return {"state": "draft", "revision": 1}
            def edit(self, **payload):
                self.calls.append(("edit", payload))
                return {"state": "draft", "revision": 2}
            def transition(self, **payload):
                self.calls.append(("transition", payload))
                return {"state": "proposed", "revision": 3}

        proposals = FakeProposals()
        server = module.HarnessHTTPServer(
            ("127.0.0.1", 0),
            FakeHarness(),
            b"arc",
            b"office",
            office_helper=FakeHelper(),
            task_proposals=proposals,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            requests = (
                ("/api/office/proposals/create", {
                    "helper_result_id": "helper-result:test",
                    "confirmation": "CREATE SYNTHETIC TASK DRAFT",
                }),
                ("/api/office/proposals/edit", {
                    "proposal_id": "task-proposal:test", "expected_revision": 1,
                    "priority": "low", "selected_step_ids": ["review_synthetic_scenario"],
                    "confirmation": "EDIT SYNTHETIC TASK DRAFT",
                }),
                ("/api/office/proposals/transition", {
                    "proposal_id": "task-proposal:test", "expected_revision": 2,
                    "action": "propose", "confirmation": "CHANGE SYNTHETIC TASK STATE",
                }),
            )
            states = []
            for path, body in requests:
                request = Request(
                    f"http://{host}:{port}{path}",
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=3) as response:
                    states.append(json.loads(response.read())["state"])
            self.assertEqual(["draft", "draft", "proposed"], states)
            self.assertEqual(["create", "edit", "transition"], [item[0] for item in proposals.calls])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
