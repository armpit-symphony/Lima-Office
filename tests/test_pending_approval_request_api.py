"""Projection, HTTP, and UI checks for pending-only approval requests."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import Request, urlopen

from lima_office.runtime.supervisor_console import build_supervisor_console_state


class PendingApprovalProjectionTests(unittest.TestCase):
    def test_projection_redacts_and_preserves_no_authority(self):
        request = {
            "approval_request_id": "approval-request:test",
            "source_approval_preview_id": "approval-preview:test",
            "task_id": "task-proposal:test",
            "action_class": "synthetic_form_preparation_review",
            "status": "pending_review", "approval_result": "pending",
            "scope_hash": "sha256:" + "a" * 64,
            "record_hash": "sha256:" + "b" * 64,
            "requested_scope": {"external_effect": "none",
                                "allowed_operations": ["review_prepared_form_plan"]},
            "operator_session_binding_id": "operator-session-binding:test",
            "bound_requester_ref": "operator-session-binding:test",
            "approval_result_created": False, "approval_binding_created": False,
            "token_verification_performed": False, "replay_record_created": False,
            "arc_dispatch_allowed": False, "arc_dispatched": False,
            "external_side_effects": False, "expired_for_decision": False,
            "expires_at": "2026-09-08T00:15:00Z", "created_at": "2026-09-08T00:00:00Z",
            "secret": "must-not-appear",
        }
        session = {"runtime_enabled": True, "active": True, "binding": {
            "binding_id": "operator-session-binding:test", "operator_id": "operator-lab:test",
            "auth_method": "local_os_session_attended_lab",
            "assurance_level": "personal_pc_attended_lab", "status": "active",
            "process_bound": True, "survives_process_restart": False,
            "pin_required": False, "mfa_verified": False,
            "production_identity_verified": False, "approval_authority": False,
            "pending_request_creation_allowed": True,
            "issued_at": "2026-09-08T00:00:00Z", "expires_at": "2026-09-08T00:30:00Z",
            "raw_os_username": "must-not-appear",
        }}
        result = build_supervisor_console_state(
            {"mode": "training", "office_integration": {"connected": True}}, {},
            operator_session_state=session,
            pending_approval_request_state={"runtime_enabled": True,
                "request_creation_enabled": True, "decision_runtime_enabled": True,
                "non_authorizing_terminal_results_enabled": True,
                "positive_approval_results_enabled": False,
                "requests": [request]},
        )
        self.assertTrue(result["operator_session"]["active"])
        self.assertFalse(result["operator_session"]["approval_authority"])
        self.assertEqual(1, result["approval_requests"]["pending_count"])
        self.assertTrue(result["approval_requests"]["decision_runtime_enabled"])
        self.assertFalse(result["approval_requests"]["approval_results_enabled"])
        self.assertTrue(
            result["approval_requests"]["non_authorizing_terminal_results_enabled"]
        )
        self.assertTrue(result["approval_requests"]["items"][0]["can_deny"])
        self.assertTrue(result["approval_requests"]["items"][0]["can_cancel"])
        self.assertFalse(result["approval_requests"]["arc_dispatch_enabled"])
        self.assertNotIn("must-not-appear", json.dumps(result))

    def test_ui_has_explicit_controls_and_no_execution_claim(self):
        source = (Path(__file__).resolve().parents[1] / "ui" /
                  "lima_office_supervisor_console.html").read_text(encoding="utf-8")
        for value in ("/api/office/operator-session/bind",
                      "/api/office/approval-requests/create",
                      "/api/office/approval-requests/transition",
                      "BIND ATTENDED LOCAL OPERATOR SESSION",
                      "CREATE PENDING APPROVAL REQUEST",
                      "RECORD NON-AUTHORIZING APPROVAL DECISION",
                      "Deny request", "Cancel my request", "Record expiry"):
            self.assertIn(value, source)
        self.assertIn("not production identity or approval", source)
        self.assertIn("Positive approval, tokens, execution bindings, and Arc dispatch remain disabled", source)
        self.assertNotIn('actionButton("Approve', source)
        self.assertNotIn("setInterval", source)


class PendingApprovalHTTPTests(unittest.TestCase):
    def test_harness_routes_session_and_request_creation(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "_arc_runtime_harness_pending_test", root / "scripts" / "arc-runtime-harness.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeHarness:
            mode = "training"
            def state(self):
                return {"mode": "training", "office_integration": {"connected": True}}

        class FakeSessions:
            def __init__(self): self.calls = []
            def state_summary(self): return {"runtime_enabled": True, "active": False}
            def bind(self, **payload):
                self.calls.append(payload)
                return {"binding_id": "operator-session-binding:test", "status": "active"}

        class FakeRequests:
            def __init__(self): self.calls = []
            def state_summary(self): return {"runtime_enabled": True, "requests": []}
            def create(self, **payload):
                self.calls.append(payload)
                return {"approval_request_id": "approval-request:test", "status": "pending_review"}

        class FakeDecisions:
            def __init__(self): self.calls = []
            def transition(self, **payload):
                self.calls.append(payload)
                return {"request": {"status": "denied"},
                        "result": {"result": "denied"}}

        sessions, requests, decisions = FakeSessions(), FakeRequests(), FakeDecisions()
        server = module.HarnessHTTPServer(
            ("127.0.0.1", 0), FakeHarness(), b"arc", b"office",
            operator_sessions=sessions, pending_approval_requests=requests,
            approval_decisions=decisions)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            host, port = server.server_address
            cases = (("/api/office/operator-session/bind",
                      {"confirmation": "BIND ATTENDED LOCAL OPERATOR SESSION"}, "active"),
                     ("/api/office/approval-requests/create",
                      {"approval_preview_id": "approval-preview:test",
                       "expected_preview_revision": 2,
                       "operator_session_binding_id": "operator-session-binding:test",
                       "confirmation": "CREATE PENDING APPROVAL REQUEST"}, "pending_review"),
                     ("/api/office/approval-requests/transition",
                      {"approval_request_id": "approval-request:test",
                       "expected_request_hash": "sha256:" + "b" * 64,
                       "action": "deny",
                       "operator_session_binding_id": "operator-session-binding:test",
                       "confirmation": "RECORD NON-AUTHORIZING APPROVAL DECISION"}, None))
            states = []
            for path, body, _ in cases:
                req = Request(f"http://{host}:{port}{path}", data=json.dumps(body).encode(),
                              headers={"Content-Type": "application/json"}, method="POST")
                with urlopen(req, timeout=3) as response:
                    response_payload = json.loads(response.read())
                    states.append(response_payload.get("status") or response_payload["result"]["result"])
            self.assertEqual(["active", "pending_review", "denied"], states)
            self.assertEqual(1, len(sessions.calls)); self.assertEqual(1, len(requests.calls))
            self.assertEqual(1, len(decisions.calls))
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
