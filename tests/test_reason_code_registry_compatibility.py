import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import (
    classify_reason_code_set,
    normalize_reason_code,
    validate_reason_codes,
)


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ReasonCodeRegistryCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()

    def test_active_registry_examples_validate(self):
        for name in (
            "reason.code.registry.reconciliation-active.example.json",
            "reason.code.registry.evidence-blocked.example.json",
            "reason.code.registry.blocked-mvp.example.json",
        ):
            self.validator.validate(copy.deepcopy(example(name)), "reason.code.registry")

    def test_deprecated_registry_example_validates_with_replacement_and_alias(self):
        payload = copy.deepcopy(
            example("reason.code.registry.export-delete-deprecated.example.json")
        )
        self.validator.validate(payload, "reason.code.registry")
        self.assertIsNotNone(payload["replaced_by"])
        self.assertGreater(len(payload["aliases"]), 0)

    def test_blocked_reason_code_cannot_authorize(self):
        result = classify_reason_code_set(["blocked_mvp_export_delete_execution"])
        self.assertTrue(result["blocked"])
        self.assertTrue(result["fail_closed"])
        self.assertFalse(result["can_authorize"])

    def test_unknown_reason_code_fails_closed(self):
        with self.assertRaises(PolicyDenyError):
            validate_reason_codes(["not_in_registry"])

    def test_compatibility_add_compatible_validates(self):
        payload = copy.deepcopy(example("reason.code.compatibility.add-compatible.example.json"))
        self.validator.validate(payload, "reason.code.compatibility")

    def test_compatibility_breaking_change_blocked_validates(self):
        payload = copy.deepcopy(
            example("reason.code.compatibility.breaking-change-blocked.example.json")
        )
        self.validator.validate(payload, "reason.code.compatibility")

    def test_deprecated_alias_maps_to_replacement_for_metadata_only(self):
        mapped = normalize_reason_code("export_delete_review_required_legacy")
        self.assertEqual("export_delete_conflict_active", mapped)
        result = classify_reason_code_set(["export_delete_review_required_legacy"])
        self.assertFalse(result["can_authorize"])

    def test_affected_contracts_list_rejects_empty_breaking_change(self):
        payload = copy.deepcopy(
            example("reason.code.compatibility.breaking-change-blocked.example.json")
        )
        payload["affected_contracts"] = []
        with self.assertRaises(Exception):
            self.validator.validate(payload, "reason.code.compatibility")

    def test_helper_never_authorizes_real_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = {path.name for path in Path(tmp).iterdir()}
            result = classify_reason_code_set(["recon_mismatched_token_verification"])
            after = {path.name for path in Path(tmp).iterdir()}
        self.assertEqual(before, after)
        self.assertFalse(result["can_authorize"])

    def test_registry_and_compatibility_examples_taxonomy_version_consistent(self):
        for name in (
            "reason.code.registry.reconciliation-active.example.json",
            "reason.code.registry.evidence-blocked.example.json",
            "reason.code.registry.export-delete-deprecated.example.json",
            "reason.code.registry.blocked-mvp.example.json",
            "reason.code.compatibility.add-compatible.example.json",
            "reason.code.compatibility.deprecate-alias.example.json",
            "reason.code.compatibility.breaking-change-blocked.example.json",
        ):
            payload = copy.deepcopy(example(name))
            self.assertTrue(str(payload["taxonomy_version"]).startswith("taxonomy-reason-v"))


if __name__ == "__main__":
    unittest.main()
