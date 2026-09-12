"""Projection, HTTP, and UI tests for tokenless approval previews."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import Request, urlopen

from lima_office.runtime.supervisor_console import build_supervisor_console_state


class ApprovalPreviewProjectionTests(unittest.TestCase):
    def test_projection_is_bounded_and_preserves_no_authority_flags(self):
        preview = {
            "approval_preview_id": "approval-preview:test",
            "revision": 1,
            "source_proposal_id": "task-proposal:test",
            "source_proposal_revision": 3,
            "source_proposal_state": "accepted_for_future_approval",
            "source_proposal_hash": "sha256:" + "a" * 64,
            "state": "preview_ready",
            "review_outcome": "pending",
            "preview_scope": {
                "requested_action_class": "form_preparation_review",
                "external_effect": "none",
                "resource_refs": ["task-proposal:test"],
                "allowed_operations": ["review_prepared_form_plan"],
                "prohibited_operations": ["issue_approval_token", "dispatch_arc"],
                "data_classification": "synthetic_fixture_only",
                "risk_tier": "low",
                "scope_hash": "sha256:" + "b" * 64,
                "max_uses": 0,
            },
            "approver_requirements": {
                "approver_roles": ["business_owner"],
                "identity_binding_required": True,
                "identity_binding_status": "not_bound_in_preview",
                "fresh_intent_required": True,
                "separation_of_duties_review_required": True,
            },
            "real_approval_request_created": False,
            "approval_result_created": False,
            "approval_token_issued": False,
            "approval_binding_created": False,
            "token_verification_performed": False,
            "replay_record_created": False,
            "assigned_worker_id": None,
            "arc_dispatch_allowed": False,
            "arc_dispatched": False,
            "source_current": True,
            "expired_for_review": False,
            "review_available": True,
            "preview_expires_at": "2026-09-07T18:15:00Z",
            "secret": "must-not-appear",
        }
        result = build_supervisor_console_state(
            {"mode": "training", "office_integration": {"connected": True}},
            {},
            approval_preview_state={"runtime_enabled": True, "previews": [preview]},
        )
        projected = result["approval_previews"]
        self.assertTrue(projected["runtime_enabled"])
        self.assertTrue(projected["preview_only"])
        self.assertEqual(1, projected["ready_count"])
        self.assertFalse(projected["real_approval_requests_enabled"])
        self.assertFalse(projected["approval_tokens_enabled"])
        self.assertFalse(projected["arc_dispatch_enabled"])
        self.assertNotIn("must-not-appear", json.dumps(result))

    def test_ui_contains_preview_routes_and_no_authority_language(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "ui" / "lima_office_supervisor_console.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("/api/office/approval-previews/create", source)
        self.assertIn("/api/office/approval-previews/transition", source)
        self.assertIn("CREATE TOKENLESS APPROVAL PREVIEW", source)
        self.assertIn("CHANGE TOKENLESS APPROVAL PREVIEW STATE", source)
        self.assertIn("not an approval request or result", source)
        self.assertIn("Mark reviewed — no authority", source)
        self.assertNotIn("setInterval", source)


class ApprovalPreviewHTTPTests(unittest.TestCase):
    def test_harness_routes_create_and_transition(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "arc-runtime-harness.py"
        spec = importlib.util.spec_from_file_location("_arc_runtime_harness_preview_test", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeHarness:
            mode = "training"
            def state(self):
                return {"mode": "training", "office_integration": {"connected": True}}

        class FakePreviews:
            def __init__(self):
                self.calls = []
            def state_summary(self):
                return {"runtime_enabled": True, "previews": []}
            def create_from_proposal(self, **payload):
                self.calls.append(("create", payload))
                return {"state": "preview_ready", "revision": 1}
            def transition(self, **payload):
                self.calls.append(("transition", payload))
                return {"state": "reviewed_no_authority", "revision": 2}

        previews = FakePreviews()
        server = module.HarnessHTTPServer(
            ("127.0.0.1", 0), FakeHarness(), b"arc", b"office",
            approval_previews=previews,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            requests = (
                ("/api/office/approval-previews/create", {
                    "proposal_id": "task-proposal:test",
                    "expected_proposal_revision": 3,
                    "confirmation": "CREATE TOKENLESS APPROVAL PREVIEW",
                }),
                ("/api/office/approval-previews/transition", {
                    "approval_preview_id": "approval-preview:test",
                    "expected_revision": 1,
                    "action": "review",
                    "confirmation": "CHANGE TOKENLESS APPROVAL PREVIEW STATE",
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
            self.assertEqual(["preview_ready", "reviewed_no_authority"], states)
            self.assertEqual(["create", "transition"], [item[0] for item in previews.calls])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
