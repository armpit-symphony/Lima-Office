import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.trust_posture import classify_trust_posture


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_attestation_update", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class WorkerAttestationSignedUpdateRollbackTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def test_worker_attestation_examples_validate(self):
        self.validator.validate(
            example("worker.attestation.attested-metadata-only.example.json"), "worker.attestation"
        )
        self.validator.validate(
            example("worker.attestation.failed-quarantine-required.example.json"), "worker.attestation"
        )
        self.validator.validate(example("worker.attestation.expired.example.json"), "worker.attestation")

    def test_update_rollback_examples_validate(self):
        self.validator.validate(
            example("update.rollback.policy-bundle-verified.example.json"), "update.rollback"
        )
        self.validator.validate(
            example("update.rollback.model-bundle-blocked-mvp.example.json"), "update.rollback"
        )
        self.validator.validate(
            example("update.rollback.runtime-rollback-required.example.json"), "update.rollback"
        )
        self.validator.validate(example("update.rollback.failed-signature.example.json"), "update.rollback")

    def test_attested_requires_evidence_and_appraisal_refs(self):
        payload = copy.deepcopy(example("worker.attestation.attested-metadata-only.example.json"))
        payload["appraisal_policy_refs"] = []
        with self.assertRaises(Exception):
            self.validator.validate(payload, "worker.attestation")

    def test_failed_attestation_requires_evidence_and_reason_codes(self):
        payload = copy.deepcopy(example("worker.attestation.failed-quarantine-required.example.json"))
        payload["reason_codes"] = []
        with self.assertRaises(Exception):
            self.validator.validate(payload, "worker.attestation")

    def test_expired_attestation_blocks_privileged_metadata_route(self):
        result = classify_trust_posture(
            attestation=copy.deepcopy(example("worker.attestation.expired.example.json")),
            update_record=copy.deepcopy(example("update.rollback.policy-bundle-verified.example.json")),
            privileged_route=True,
        )
        self.assertTrue(result["blocked"])
        self.assertFalse(result["can_authorize"])

    def test_blocked_mvp_attestation_cannot_be_treated_as_trusted(self):
        attestation = copy.deepcopy(example("worker.attestation.expired.example.json"))
        attestation["attestation_status"] = "blocked_mvp"
        attestation["trust_root_status"] = "blocked_mvp"
        attestation["reason_codes"] = ["update_blocked_mvp"]
        result = classify_trust_posture(
            attestation=attestation,
            update_record=copy.deepcopy(example("update.rollback.policy-bundle-verified.example.json")),
            privileged_route=True,
        )
        self.assertTrue(result["blocked"])
        self.assertFalse(result["can_authorize"])

    def test_verified_or_applied_update_requires_signing_and_provenance_metadata(self):
        payload = copy.deepcopy(example("update.rollback.policy-bundle-verified.example.json"))
        payload["signer_ref"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "update.rollback")

    def test_failed_signature_update_fails_closed(self):
        result = classify_trust_posture(
            attestation=copy.deepcopy(example("worker.attestation.attested-metadata-only.example.json")),
            update_record=copy.deepcopy(example("update.rollback.failed-signature.example.json")),
            privileged_route=True,
        )
        self.assertTrue(result["blocked"])
        self.assertFalse(result["can_authorize"])

    def test_rollback_requires_target_reason_and_evidence(self):
        payload = copy.deepcopy(example("update.rollback.runtime-rollback-required.example.json"))
        payload["rollback_target_ref"] = None
        with self.assertRaises(Exception):
            self.validator.validate(payload, "update.rollback")

    def test_model_bundle_blocked_mvp_does_not_authorize_model_route(self):
        result = classify_trust_posture(
            attestation=copy.deepcopy(example("worker.attestation.attested-metadata-only.example.json")),
            update_record=copy.deepcopy(example("update.rollback.model-bundle-blocked-mvp.example.json")),
            privileged_route=True,
        )
        self.assertTrue(result["blocked"])
        self.assertFalse(result["can_authorize"])

    def test_console_and_supervisor_attestation_examples_validate(self):
        self.validator.validate(example("console.alert.attestation-failed.example.json"), "console.alert")
        self.validator.validate(
            example("supervisor.health.attestation-degraded.example.json"),
            "supervisor.health",
        )

    def test_helper_fails_closed_on_missing_privileged_metadata(self):
        with self.assertRaises(PolicyDenyError):
            classify_trust_posture(attestation=None, update_record=None, privileged_route=True)

    def test_reason_code_gate_passes_new_attestation_update_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
