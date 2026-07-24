import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.attestation_lineage import evaluate_attestation_lineage
from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.model_routing import classify_model_route


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_attestation_lineage", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class DurableAttestationResultLineageTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def _active_authority(self) -> dict:
        return copy.deepcopy(example("attestation.authority.verifier-owner-active.example.json"))

    def test_lineage_examples_validate(self):
        self.validator.validate(
            example("attestation.result.lineage.current.example.json"),
            "attestation.result.lineage",
        )
        self.validator.validate(
            example("attestation.result.lineage.revoked-propagation-pending.example.json"),
            "attestation.result.lineage",
        )
        self.validator.validate(
            example("attestation.result.lineage.quarantine-required.example.json"),
            "attestation.result.lineage",
        )

    def test_authority_examples_validate(self):
        self.validator.validate(
            example("attestation.authority.verifier-owner-active.example.json"),
            "attestation.authority",
        )
        self.validator.validate(
            example("attestation.authority.reference-value-approver-active.example.json"),
            "attestation.authority",
        )
        self.validator.validate(
            example("attestation.authority.revoked.example.json"),
            "attestation.authority",
        )

    def test_current_lineage_requires_refs_evidence_and_expiry(self):
        payload = copy.deepcopy(example("attestation.result.lineage.current.example.json"))
        payload["expires_at"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.result.lineage")

    def test_revoked_lineage_fails_closed(self):
        lineage = copy.deepcopy(example("attestation.result.lineage.revoked-propagation-pending.example.json"))
        authority = self._active_authority()
        result = evaluate_attestation_lineage(lineage=lineage, authorities=[authority], privileged_context=True)
        self.assertTrue(result["fail_closed"])
        self.assertIn("attestation_lineage_revoked", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_conflicted_lineage_fails_closed(self):
        lineage = copy.deepcopy(example("attestation.result.lineage.current.example.json"))
        lineage["lineage_status"] = "conflicted"
        lineage["trust_effect"] = "degraded"
        lineage["reason_codes"] = ["attestation_lineage_conflicted"]
        self.validator.validate(lineage, "attestation.result.lineage")
        result = evaluate_attestation_lineage(
            lineage=lineage,
            authorities=[self._active_authority()],
            privileged_context=True,
        )
        self.assertTrue(result["fail_closed"])
        self.assertFalse(result["can_authorize"])

    def test_quarantine_required_needs_worker_lifecycle_ref_and_evidence(self):
        payload = copy.deepcopy(example("attestation.result.lineage.quarantine-required.example.json"))
        payload["worker_lifecycle_ref"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.result.lineage")

    def test_active_authority_requires_mfa_device_evidence_and_approval(self):
        payload = copy.deepcopy(example("attestation.authority.verifier-owner-active.example.json"))
        payload["approved_at"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.authority")

    def test_revoked_authority_fails_closed(self):
        lineage = copy.deepcopy(example("attestation.result.lineage.current.example.json"))
        authority = copy.deepcopy(example("attestation.authority.revoked.example.json"))
        result = evaluate_attestation_lineage(lineage=lineage, authorities=[authority], privileged_context=True)
        self.assertTrue(result["fail_closed"])
        self.assertIn("verifier_authority_revoked", result["reason_codes"])

    def test_missing_verifier_authority_fails_closed(self):
        lineage = copy.deepcopy(example("attestation.result.lineage.current.example.json"))
        authority = copy.deepcopy(example("attestation.authority.reference-value-approver-active.example.json"))
        result = evaluate_attestation_lineage(lineage=lineage, authorities=[authority], privileged_context=True)
        self.assertTrue(result["fail_closed"])
        self.assertIn("verifier_authority_missing", result["reason_codes"])

    def test_pending_revocation_propagation_blocks_privileged_context(self):
        lineage = copy.deepcopy(example("attestation.result.lineage.revoked-propagation-pending.example.json"))
        result = evaluate_attestation_lineage(
            lineage=lineage,
            authorities=[self._active_authority()],
            privileged_context=True,
        )
        self.assertTrue(result["fail_closed"])
        self.assertIn("revocation_propagation_pending", result["reason_codes"])

    def test_pending_revocation_reason_blocks_model_route_selection(self):
        route = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        route["route_reason_codes"] = ["revocation_propagation_pending"]
        route["route_status"] = "selected"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(route)

    def test_blocked_mvp_authority_cannot_approve_trust_decisions(self):
        payload = copy.deepcopy(example("attestation.authority.verifier-owner-active.example.json"))
        payload["authority_status"] = "blocked_mvp"
        payload["authority_type"] = "blocked_mvp"
        payload["allowed_authority_actions"] = ["accept_attestation_result"]
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.authority")

    def test_quarantine_clearance_requires_sod_metadata(self):
        authority = copy.deepcopy(example("attestation.authority.verifier-owner-active.example.json"))
        authority["allowed_authority_actions"] = ["clear_worker_quarantine"]
        authority["separation_of_duties_required"] = False
        with self.assertRaises(Exception):
            self.validator.validate(authority, "attestation.authority")

    def test_console_and_supervisor_lineage_alert_examples_validate(self):
        self.validator.validate(
            example("console.alert.attestation-revocation-propagation.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.attestation-lineage-blocked.example.json"),
            "supervisor.health",
        )

    def test_helper_never_verifies_tpm_certs_signatures_or_storage(self):
        source = (ROOT / "lima_office" / "runtime" / "attestation_lineage.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("tpm2_", "cryptography", "requests.", "socket.", "sqlite3", "subprocess.")
        for token in banned_tokens:
            self.assertNotIn(token, source)

        result = evaluate_attestation_lineage(
            lineage=copy.deepcopy(example("attestation.result.lineage.current.example.json")),
            authorities=[self._active_authority()],
            privileged_context=True,
        )
        self.assertFalse(result["can_authorize"])

    def test_reason_code_gate_passes_new_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
