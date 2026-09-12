import unittest
from pathlib import Path

from lima_office.guardian import GuardianPolicy


class FailClosedTests(unittest.TestCase):
    def test_no_live_connector_behavior_exists(self):
        decision = GuardianPolicy().decide("connector_live_access")
        self.assertEqual("deny", decision["decision"])

        runtime_root = Path(__file__).resolve().parents[1] / "lima_office"
        runtime_files = list(runtime_root.rglob("*.py"))
        source = "\n".join(path.read_text(encoding="utf-8") for path in runtime_files)
        forbidden_imports = ("import requests", "import smtplib", "import socket", "selenium")
        for forbidden in forbidden_imports:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

        subprocess_importers = [
            path.relative_to(runtime_root).as_posix()
            for path in runtime_files
            if "import subprocess" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            ["runtime/supervisor_conversation.py"],
            subprocess_importers,
        )
        conversation_source = (
            runtime_root / "runtime" / "supervisor_conversation.py"
        ).read_text(encoding="utf-8")
        for required_guardrail in (
            '"--sandbox",\n            "read-only"',
            '"--ephemeral"',
            'features.shell_tool=false',
            'features.multi_agent=false',
            'web_search="disabled"',
            'tools.web_search=false',
            'tools.view_image=false',
        ):
            with self.subTest(required_guardrail=required_guardrail):
                self.assertIn(required_guardrail, conversation_source)

    def test_privileged_schema_action_override_denied(self):
        decision = GuardianPolicy().decide(
            "read_only_diagnostic",
            {
                "tenant_id": "tenant-lab-001",
                "customer_context_id": "customer-context-main",
                "execution_mode": "mock_only",
                "external_effect": "none",
                "evidence_required": True,
                "schema_action_class": "outbound_message",
            },
        )
        self.assertEqual("deny", decision["decision"])


if __name__ == "__main__":
    unittest.main()
