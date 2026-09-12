"""Safety tests for the business-owner Supervisor Console projection."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import urlopen
from urllib.request import Request

from lima_office.runtime.supervisor_console import (
    build_supervisor_console_state,
    codex_subscription_readiness,
)


class CodexSubscriptionReadinessTests(unittest.TestCase):
    def test_reports_profile_and_cli_without_exposing_credentials(self):
        with tempfile.TemporaryDirectory(prefix="lima-office-codex-") as raw:
            root = Path(raw)
            (root / "auth.json").write_text(
                '{"tokens":{"access_token":"must-not-appear"}}',
                encoding="utf-8",
            )

            result = codex_subscription_readiness(
                codex_home=root,
                codex_cli="codex-test",
            )

        self.assertEqual("profile_detected", result["status"])
        self.assertTrue(result["auth_profile_detected"])
        self.assertTrue(result["cli_detected"])
        self.assertFalse(result["credentials_exposed"])
        self.assertFalse(result["live_invocation_enabled"])
        self.assertFalse(result["tools_enabled"])
        encoded = json.dumps(result)
        self.assertNotIn("must-not-appear", encoded)
        self.assertNotIn("auth.json", encoded)

    def test_requires_both_profile_and_cli_for_detected_posture(self):
        with tempfile.TemporaryDirectory(prefix="lima-office-codex-") as raw:
            root = Path(raw)
            result = codex_subscription_readiness(
                codex_home=root,
                codex_cli="codex-test",
            )
        self.assertEqual("sign_in_needed", result["status"])


class SupervisorConsoleStateTests(unittest.TestCase):
    def test_projection_is_non_executing_and_uses_cached_inventory_only(self):
        state = {
            "mode": "training",
            "training_progress": {"attempts": 25, "open_gaps": 2},
            "registration_practice": {"attempt_count": 25, "review_count": 5},
            "operator_ide": {"tasks": [{"sensitive": "not projected"}], "pending_approvals": []},
            "office_integration": {
                "connected": True,
                "classification_authority": "supervisor_server_derived",
                "inventory": {
                    "workers": [
                        {
                            "worker_id": "arc-worker-001",
                            "worker_role": "general_office_arc_worker",
                            "state": "healthy",
                            "eligible": True,
                            "secret": "must-not-appear",
                        }
                    ]
                },
            },
            "recent_evidence": [
                {
                    "event_id": "evidence:1",
                    "occurred_at": "2026-09-06T00:00:00Z",
                    "event_type": "office_worker_inventory_refreshed",
                    "payload": {"raw": "must-not-appear"},
                }
            ],
        }
        with tempfile.TemporaryDirectory(prefix="lima-office-codex-") as raw:
            result = build_supervisor_console_state(
                state,
                {"version": "test", "arc_commit": "a" * 40, "source_modified": False},
                codex_home=Path(raw),
                codex_cli="codex-test",
            )

        self.assertEqual("ready", result["status"])
        self.assertFalse(result["supervisor"]["automatic_refresh"])
        self.assertFalse(result["supervisor"]["execution_allowed"])
        self.assertFalse(result["supervisor"]["side_effects_allowed"])
        self.assertFalse(result["work"]["dispatch_enabled"])
        self.assertFalse(result["helper"]["runtime_enabled"])
        self.assertEqual(1, result["workers"]["count"])
        self.assertTrue(result["workers"]["inventory_refreshed"])
        self.assertFalse(result["evidence"]["raw_payloads_included"])
        encoded = json.dumps(result)
        self.assertNotIn("must-not-appear", encoded)
        self.assertNotIn("sensitive", encoded)

    def test_missing_inventory_is_not_reported_as_healthy_empty_fleet(self):
        with tempfile.TemporaryDirectory(prefix="lima-office-codex-") as raw:
            result = build_supervisor_console_state(
                {
                    "mode": "training",
                    "office_integration": {"connected": True, "inventory": None},
                },
                {},
                codex_home=Path(raw),
                codex_cli="codex-test",
            )
        self.assertFalse(result["workers"]["inventory_refreshed"])
        self.assertEqual(0, result["workers"]["count"])

    def test_malformed_counts_and_labels_fail_to_safe_values(self):
        with tempfile.TemporaryDirectory(prefix="lima-office-codex-") as raw:
            result = build_supervisor_console_state(
                {
                    "office_integration": {
                        "connected": True,
                        "classification_authority": {"unexpected": "object"},
                    },
                    "training_progress": {"attempts": "twenty-five", "open_gaps": -3},
                },
                {"version": {"unexpected": "object"}},
                codex_home=Path(raw),
                codex_cli="codex-test",
            )
        self.assertEqual(0, result["training"]["attempts"])
        self.assertEqual(0, result["training"]["open_gaps"])
        self.assertEqual("development", result["build"]["version"])
        self.assertEqual(
            "supervisor_server_derived",
            result["supervisor"]["classification_authority"],
        )


class SupervisorConsoleAssetTests(unittest.TestCase):
    def test_ui_is_local_only_and_model_send_is_disabled(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "ui" / "lima_office_supervisor_console.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("LIMA OFFICE", source)
        self.assertIn('fetch("/api/office/state"', source)
        self.assertIn('fetch("/api/office/workers"', source)
        self.assertNotIn("https://", source)
        self.assertNotIn("http://", source)
        self.assertIn('fetch("/api/office/conversation"', source)
        self.assertIn("READ-ONLY SUPERVISOR TURN", source)
        self.assertIn('fetch("/api/office/helper/review"', source)
        self.assertIn("RUN SYNTHETIC HELPER REVIEW", source)
        self.assertIn("No customer data or external action", source)
        self.assertIn("Do not enter customer personal data", source)
        self.assertNotIn("setInterval", source)


class SupervisorConsoleHTTPIntegrationTests(unittest.TestCase):
    def test_harness_serves_console_and_redacted_state_on_loopback(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "arc-runtime-harness.py"
        spec = importlib.util.spec_from_file_location("_arc_runtime_harness_test", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeHarness:
            def state(self):
                return {
                    "mode": "training",
                    "office_integration": {"connected": True, "inventory": None},
                    "recent_evidence": [{"payload": {"secret": "must-not-appear"}}],
                }

        server = module.HarnessHTTPServer(
            ("127.0.0.1", 0),
            FakeHarness(),
            b"arc-ui",
            b"lima-office-ui",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with urlopen(f"http://{host}:{port}/office", timeout=3) as response:
                self.assertEqual(b"lima-office-ui", response.read())
                self.assertEqual("no-store", response.headers["Cache-Control"])
            with urlopen(f"http://{host}:{port}/api/office/state", timeout=3) as response:
                payload = json.loads(response.read())
            self.assertEqual("business_owner_supervisor_console", payload["surface"])
            self.assertFalse(payload["supervisor"]["execution_allowed"])
            self.assertNotIn("must-not-appear", json.dumps(payload))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_harness_routes_attended_conversation_to_bounded_service(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "arc-runtime-harness.py"
        spec = importlib.util.spec_from_file_location("_arc_runtime_harness_conversation_test", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeHarness:
            mode = "training"
            def state(self):
                return {"mode": "training", "office_integration": {"connected": True}}

        class FakeConversation:
            def state_summary(self):
                return {"enabled": True, "mode": "one_turn_transient"}
            def turn(self, **payload):
                return {"status": "completed", "response_text": payload["message"]}

        service = FakeConversation()
        server = module.HarnessHTTPServer(
            ("127.0.0.1", 0), FakeHarness(), b"arc", b"office", service
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            body = json.dumps(
                {
                    "message": "Synthetic test",
                    "confirmation": "READ-ONLY SUPERVISOR TURN",
                    "data_classification": "internal",
                }
            ).encode("utf-8")
            request = Request(
                f"http://{host}:{port}/api/office/conversation",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=3) as response:
                payload = json.loads(response.read())
            self.assertEqual("completed", payload["status"])
            self.assertEqual("Synthetic test", payload["response_text"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_harness_routes_fixed_synthetic_review_to_helper(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "arc-runtime-harness.py"
        spec = importlib.util.spec_from_file_location("_arc_runtime_harness_helper_test", script)
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
            def review_registration(self, **payload):
                return {"status": "completed", "scenario_id": payload["scenario_id"]}

        helper = FakeHelper()
        server = module.HarnessHTTPServer(
            ("127.0.0.1", 0), FakeHarness(), b"arc", b"office", None, helper
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            request = Request(
                f"http://{host}:{port}/api/office/helper/review",
                data=json.dumps({"scenario_id": "missing-phone", "confirmation": "RUN SYNTHETIC HELPER REVIEW"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=3) as response:
                payload = json.loads(response.read())
            self.assertEqual("completed", payload["status"])
            self.assertEqual("missing-phone", payload["scenario_id"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
