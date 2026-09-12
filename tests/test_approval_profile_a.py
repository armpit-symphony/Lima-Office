"""Profile A is visible for testing and remains non-authorizing."""

from __future__ import annotations

import unittest
from pathlib import Path

from lima_office.runtime.approval_readiness import profile_a_lab_state
from lima_office.runtime.supervisor_console import build_supervisor_console_state


class ApprovalProfileALabTests(unittest.TestCase):
    def test_profile_a_has_no_authority_flags(self):
        state = profile_a_lab_state()
        self.assertEqual("active_lab_only", state["status"])
        self.assertTrue(state["synthetic_data_only"])
        self.assertTrue(state["upgrade_required_before_customer_use"])
        for field in (
            "customer_or_production_use_allowed", "positive_approval_enabled",
            "approval_result_issuance_enabled", "approval_token_issuance_enabled",
            "approval_binding_enabled", "token_verification_enabled",
            "replay_consumption_enabled", "worker_assignment_enabled",
            "arc_dispatch_enabled", "external_effects_enabled",
        ):
            self.assertFalse(state[field], field)

    def test_console_projects_profile_a_without_authority(self):
        result = build_supervisor_console_state(
            {"office_integration": {"connected": False}},
            {"version": "test", "arc_commit": "test", "source_modified": True},
        )
        profile = result["approval_profile"]
        self.assertEqual("attended_os_session_lab_only", profile["profile_id"])
        self.assertEqual("active_lab_only", profile["status"])
        self.assertFalse(profile["positive_approval_enabled"])
        self.assertFalse(profile["arc_dispatch_enabled"])
        self.assertFalse(profile["external_effects_enabled"])

    def test_console_labels_profile_a_as_lab_only(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "ui"
            / "lima_office_supervisor_console.html"
        ).read_text(encoding="utf-8")
        self.assertIn('id="approval-profile-name"', source)
        self.assertIn('id="approval-profile-status"', source)
        self.assertIn("Blocked until profile B or C", source)
        self.assertIn("cannot approve execution", source)


if __name__ == "__main__":
    unittest.main()
