import copy
import importlib.util
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.attestation_verifier import evaluate_attestation_metadata
from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.model_routing import classify_model_route


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_attestation_verifier", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class AttestationVerifierPolicyReferenceValuesTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()
        self.now = datetime(2026, 5, 25, 17, 30, tzinfo=UTC)

    def _baseline_inputs(self):
        attestation = copy.deepcopy(example("worker.attestation.attested-metadata-only.example.json"))
        policy = copy.deepcopy(example("attestation.appraisal_policy.active-worker.example.json"))
        policy["required_reference_value_types"] = ["arc_runtime_hash"]
        policy["required_endorsement_types"] = ["sparkpit_operator_placeholder"]
        policy["tenant_id"] = attestation["tenant_id"]
        policy["customer_context_id"] = attestation["customer_context_id"]
        reference = copy.deepcopy(example("attestation.reference_value.active-runtime.example.json"))
        reference["reference_value_type"] = "arc_runtime_hash"
        reference["tenant_id"] = attestation["tenant_id"]
        reference["customer_context_id"] = attestation["customer_context_id"]
        endorsement = copy.deepcopy(example("attestation.endorsement.trusted-placeholder.example.json"))
        endorsement["endorsement_type"] = "sparkpit_operator_placeholder"
        endorsement["tenant_id"] = attestation["tenant_id"]
        endorsement["customer_context_id"] = attestation["customer_context_id"]
        return attestation, policy, [reference], [endorsement]

    def test_new_attestation_reference_appraisal_result_examples_validate(self):
        self.validator.validate(
            example("attestation.reference_value.active-runtime.example.json"),
            "attestation.reference_value",
        )
        self.validator.validate(
            example("attestation.reference_value.revoked-model-bundle.example.json"),
            "attestation.reference_value",
        )
        self.validator.validate(
            example("attestation.endorsement.trusted-placeholder.example.json"),
            "attestation.endorsement",
        )
        self.validator.validate(
            example("attestation.endorsement.revoked.example.json"),
            "attestation.endorsement",
        )
        self.validator.validate(
            example("attestation.appraisal_policy.active-worker.example.json"),
            "attestation.appraisal_policy",
        )
        self.validator.validate(
            example("attestation.appraisal_policy.blocked-mvp.example.json"),
            "attestation.appraisal_policy",
        )
        self.validator.validate(
            example("attestation.result.pass-metadata-only.example.json"),
            "attestation.result",
        )
        self.validator.validate(
            example("attestation.result.fail-quarantine-required.example.json"),
            "attestation.result",
        )
        self.validator.validate(
            example("attestation.result.inconclusive-degraded.example.json"),
            "attestation.result",
        )
        self.validator.validate(
            example("console.alert.attestation-appraisal-failed.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.attestation-appraisal-degraded.example.json"),
            "supervisor.health",
        )

    def test_active_reference_value_requires_approval_and_evidence(self):
        payload = copy.deepcopy(example("attestation.reference_value.active-runtime.example.json"))
        payload["approved_by_ref"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.reference_value")

    def test_revoked_reference_value_fails(self):
        attestation, policy, _, endorsements = self._baseline_inputs()
        revoked = copy.deepcopy(example("attestation.reference_value.revoked-model-bundle.example.json"))
        revoked["reference_value_type"] = "arc_runtime_hash"
        revoked["tenant_id"] = attestation["tenant_id"]
        revoked["customer_context_id"] = attestation["customer_context_id"]
        result = evaluate_attestation_metadata(
            attestation=attestation,
            appraisal_policy=policy,
            reference_values=[revoked],
            endorsements=endorsements,
            now=self.now,
        )
        self.assertIn("reference_value_revoked", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_trusted_endorsement_placeholder_requires_validity_and_evidence(self):
        payload = copy.deepcopy(example("attestation.endorsement.trusted-placeholder.example.json"))
        payload["valid_until"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.endorsement")

    def test_revoked_endorsement_fails_closed(self):
        attestation, policy, refs, _ = self._baseline_inputs()
        revoked = copy.deepcopy(example("attestation.endorsement.revoked.example.json"))
        revoked["endorsement_type"] = "sparkpit_operator_placeholder"
        revoked["tenant_id"] = attestation["tenant_id"]
        revoked["customer_context_id"] = attestation["customer_context_id"]
        result = evaluate_attestation_metadata(
            attestation=attestation,
            appraisal_policy=policy,
            reference_values=refs,
            endorsements=[revoked],
            now=self.now,
        )
        self.assertIn("endorsement_revoked", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_active_appraisal_policy_requires_arrays_evidence_and_approval(self):
        payload = copy.deepcopy(example("attestation.appraisal_policy.active-worker.example.json"))
        payload["required_reference_value_types"] = []
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.appraisal_policy")

    def test_pass_result_requires_refs_evidence_and_expiry(self):
        payload = copy.deepcopy(example("attestation.result.pass-metadata-only.example.json"))
        payload["expires_at"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.result")

    def test_fail_result_requires_reason_and_evidence(self):
        payload = copy.deepcopy(example("attestation.result.fail-quarantine-required.example.json"))
        payload["reason_codes"] = []
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.result")

    def test_inconclusive_result_degrades(self):
        payload = copy.deepcopy(example("attestation.result.inconclusive-degraded.example.json"))
        self.validator.validate(payload, "attestation.result")
        self.assertEqual("degraded", payload["trust_effect"])

    def test_blocked_mvp_cannot_be_trusted(self):
        payload = copy.deepcopy(example("attestation.result.pass-metadata-only.example.json"))
        payload["appraisal_result"] = "blocked_mvp"
        payload["trust_effect"] = "trusted_metadata_only"
        with self.assertRaises(Exception):
            self.validator.validate(payload, "attestation.result")

    def test_missing_reference_value_fails_closed(self):
        attestation, policy, _, endorsements = self._baseline_inputs()
        result = evaluate_attestation_metadata(
            attestation=attestation,
            appraisal_policy=policy,
            reference_values=[],
            endorsements=endorsements,
            now=self.now,
        )
        self.assertIn("reference_value_missing", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_stale_reference_value_fails_closed(self):
        attestation, policy, refs, endorsements = self._baseline_inputs()
        refs[0]["expires_at"] = "2026-01-01T00:00:00Z"
        result = evaluate_attestation_metadata(
            attestation=attestation,
            appraisal_policy=policy,
            reference_values=refs,
            endorsements=endorsements,
            now=self.now,
        )
        self.assertIn("reference_value_stale", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_inactive_appraisal_policy_fails_closed(self):
        attestation, _, refs, endorsements = self._baseline_inputs()
        blocked_policy = copy.deepcopy(example("attestation.appraisal_policy.blocked-mvp.example.json"))
        result = evaluate_attestation_metadata(
            attestation=attestation,
            appraisal_policy=blocked_policy,
            reference_values=refs,
            endorsements=endorsements,
            now=self.now,
        )
        self.assertIn("appraisal_policy_revoked", result["reason_codes"])
        self.assertFalse(result["can_authorize"])

    def test_model_route_with_failed_attestation_appraisal_blocks_privileged_route(self):
        payload = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        payload["risk_tier"] = "high"
        payload["approval_required"] = True
        payload["route_reason_codes"] = ["appraisal_failed"]
        payload["route_status"] = "selected"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_helper_never_accesses_tpm_certs_signatures_network_or_storage(self):
        source = (ROOT / "lima_office" / "runtime" / "attestation_verifier.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("tpm2_", "cryptography", "requests.", "socket.", "sqlite3", "subprocess.")
        for token in banned_tokens:
            self.assertNotIn(token, source)

        attestation, policy, refs, endorsements = self._baseline_inputs()
        result = evaluate_attestation_metadata(
            attestation=attestation,
            appraisal_policy=policy,
            reference_values=refs,
            endorsements=endorsements,
            now=self.now,
        )
        self.assertFalse(result["can_authorize"])

    def test_reason_code_gate_passes_new_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
