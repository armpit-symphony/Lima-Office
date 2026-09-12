"""Positive-approval readiness remains design-only and non-authorizing."""

from __future__ import annotations

import copy
import unittest

from lima_office.contracts import ContractValidator
from lima_office.runtime.errors import ContractValidationError
from helpers import example


class ApprovalReadinessContractTests(unittest.TestCase):
    def setUp(self):
        self.validator = ContractValidator()
        self.payload = example(
            "approval.readiness.blocked-owner-decision.example.json"
        )

    def test_owner_decision_example_is_blocked_and_non_authorizing(self):
        self.validator.validate(self.payload, "approval.readiness")
        self.assertEqual("design_only", self.payload["assessment_mode"])
        self.assertEqual("blocked_owner_decision", self.payload["status"])
        self.assertTrue(self.payload["owner_decision_required"])
        self.assertFalse(self.payload["implementation_authorized"])
        for field in (
            "approval_result_issuance_enabled", "approval_token_issuance_enabled",
            "approval_binding_enabled", "token_verification_enabled",
            "replay_consumption_enabled", "worker_assignment_enabled",
            "arc_dispatch_enabled", "external_effects_enabled",
        ):
            self.assertFalse(self.payload[field], field)

    def test_any_authority_flag_fails_contract_validation(self):
        fields = (
            "implementation_authorized", "approval_result_issuance_enabled",
            "approval_token_issuance_enabled", "approval_binding_enabled",
            "token_verification_enabled", "replay_consumption_enabled",
            "worker_assignment_enabled", "arc_dispatch_enabled",
            "external_effects_enabled",
        )
        for field in fields:
            with self.subTest(field=field):
                unsafe = copy.deepcopy(self.payload)
                unsafe[field] = True
                with self.assertRaises(ContractValidationError):
                    self.validator.validate(unsafe, "approval.readiness")

    def test_selected_profile_a_remains_blocked_and_non_authorizing(self):
        selected = example(
            "approval.readiness.profile-a-lab-selected.example.json"
        )
        self.validator.validate(selected, "approval.readiness")
        self.assertEqual("blocked_controls_missing", selected["status"])
        self.assertEqual(
            "attended_os_session_lab_only",
            selected["selected_identity_profile"],
        )
        self.assertEqual(
            "single_owner_low_risk_exception",
            selected["selected_separation_profile"],
        )
        self.assertFalse(selected["owner_decision_required"])
        self.assertFalse(selected["implementation_authorized"])
        self.assertFalse(selected["approval_result_issuance_enabled"])
        self.assertFalse(selected["arc_dispatch_enabled"])
        self.assertFalse(selected["external_effects_enabled"])

    def test_blocked_owner_decision_cannot_claim_selected_profile(self):
        unsafe = copy.deepcopy(self.payload)
        unsafe["selected_identity_profile"] = "windows_hello_or_passkey_step_up"
        with self.assertRaises(ContractValidationError):
            self.validator.validate(unsafe, "approval.readiness")

    def test_ready_state_requires_every_design_control_and_no_blockers(self):
        ready = copy.deepcopy(self.payload)
        ready.update({
            "status": "ready_for_implementation_review",
            "selected_identity_profile": "windows_hello_or_passkey_step_up",
            "selected_separation_profile": "single_owner_low_risk_exception",
            "owner_decision_required": False,
            "reason_codes": [],
            "design_complete": True,
        })
        for field in (
            "named_human_identity_selected", "step_up_authenticator_selected",
            "session_ttl_selected", "device_binding_selected", "rbac_mapping_complete",
            "separation_policy_selected", "scope_narrowing_defined",
            "atomic_issuance_defined", "single_use_consumption_defined",
            "durable_replay_store_defined",
        ):
            ready["control_posture"][field] = True
        self.validator.validate(ready, "approval.readiness")
        self.assertFalse(ready["implementation_authorized"])

        ready["control_posture"]["durable_replay_store_defined"] = False
        with self.assertRaises(ContractValidationError):
            self.validator.validate(ready, "approval.readiness")


if __name__ == "__main__":
    unittest.main()
