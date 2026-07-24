import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.invariants import assert_evidence_export_manifest_consistent
from lima_office.runtime.taxonomy import classify_export_delete_conflict, validate_reason_codes


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class GovernanceExportDeleteTaxonomyTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()

    def test_taxonomy_reason_codes_are_recognized(self):
        codes = [
            "export_delete_conflict_active",
            "recon_mismatched_approval_binding",
            "blocked_mvp_authorization_attempt",
        ]
        normalized = validate_reason_codes(codes)
        self.assertEqual(sorted(codes), normalized)

    def test_unknown_reason_code_fails(self):
        with self.assertRaises(PolicyDenyError):
            validate_reason_codes(["unknown_reason_code"])

    def test_export_delete_review_examples_validate(self):
        for name in (
            "governance.export_delete_review.export-approved-redacted.example.json",
            "governance.export_delete_review.delete-conflict-denied.example.json",
            "governance.export_delete_review.blocked-mvp.example.json",
        ):
            self.validator.validate(copy.deepcopy(example(name)), "governance.export_delete_review")

    def test_delete_conflict_denied_example_validates(self):
        payload = copy.deepcopy(example("governance.export_delete_review.delete-conflict-denied.example.json"))
        self.validator.validate(payload, "governance.export_delete_review")
        result = classify_export_delete_conflict(payload)
        self.assertTrue(result["conflict_detected"])
        self.assertFalse(result["can_authorize"])

    def test_blocked_mvp_export_delete_cannot_be_completed(self):
        payload = copy.deepcopy(example("governance.export_delete_review.blocked-mvp.example.json"))
        payload["export_review_status"] = "exported"
        with self.assertRaises(Exception):
            self.validator.validate(payload, "governance.export_delete_review")

    def test_export_manifest_with_raw_or_secret_content_fails(self):
        manifest = copy.deepcopy(example("evidence.export_manifest.exported-redacted-metadata-only.example.json"))
        manifest["raw_content_included"] = True
        with self.assertRaises(Exception):
            self.validator.validate(manifest, "evidence.export_manifest")

        manifest = copy.deepcopy(example("evidence.export_manifest.exported-redacted-metadata-only.example.json"))
        manifest["secret_material_included"] = True
        with self.assertRaises(Exception):
            self.validator.validate(manifest, "evidence.export_manifest")

    def test_exported_manifest_requires_redaction_applied_or_not_required(self):
        manifest = copy.deepcopy(example("evidence.export_manifest.exported-redacted-metadata-only.example.json"))
        self.validator.validate(manifest, "evidence.export_manifest")

        manifest["redaction_status"] = "pending"
        with self.assertRaises(Exception):
            self.validator.validate(manifest, "evidence.export_manifest")

    def test_conflict_detected_requires_evidence_refs(self):
        payload = copy.deepcopy(example("governance.export_delete_review.delete-conflict-denied.example.json"))
        payload["conflict_evidence_refs"] = []
        with self.assertRaises(Exception):
            self.validator.validate(payload, "governance.export_delete_review")

    def test_preservation_hold_conflict_blocks_delete(self):
        payload = copy.deepcopy(example("governance.export_delete_review.delete-conflict-denied.example.json"))
        payload["delete_review_status"] = "approved"
        payload["delete_proof_refs"] = ["proof-delete-001"]
        with self.assertRaises(Exception):
            self.validator.validate(payload, "governance.export_delete_review")

    def test_failed_closed_export_delete_requires_evidence_refs(self):
        payload = copy.deepcopy(example("governance.audit_export.export-denied.example.json"))
        payload["status"] = "failed_closed"
        payload["reason_codes"] = ["evidence_failed_closed_required"]
        payload["evidence_refs"] = []
        with self.assertRaises(Exception):
            self.validator.validate(payload, "governance.audit_export")

    def test_manifest_invariant_conflict_requires_refs(self):
        manifest = copy.deepcopy(example("evidence.export_manifest.blocked-delete-conflict.example.json"))
        checked = assert_evidence_export_manifest_consistent(manifest)
        self.assertEqual("blocked_mvp", checked["export_status"])

        manifest["delete_conflict_refs"] = []
        with self.assertRaises(Exception):
            assert_evidence_export_manifest_consistent(manifest)

    def test_helper_does_not_persist_or_authorize_real_action(self):
        payload = copy.deepcopy(example("governance.export_delete_review.delete-conflict-denied.example.json"))
        with tempfile.TemporaryDirectory() as tmp:
            before = {path.name for path in Path(tmp).iterdir()}
            result = classify_export_delete_conflict(payload)
            after = {path.name for path in Path(tmp).iterdir()}
        self.assertEqual(before, after)
        self.assertFalse(result["can_authorize"])


if __name__ == "__main__":
    unittest.main()
