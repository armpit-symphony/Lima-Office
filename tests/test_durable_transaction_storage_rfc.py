import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.evidence import EvidenceExportManifestBuilder
from lima_office.guardian import InMemoryReplayStore
from lima_office.runtime.errors import ContractValidationError


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class DurableTransactionStorageRFCTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()

    def transaction_example(self, name: str) -> dict:
        return copy.deepcopy(example(name))

    def ledger_example(self, name: str) -> dict:
        return copy.deepcopy(example(name))

    def test_transaction_boundary_examples_validate(self):
        names = [
            "transaction.boundary.guardian-replay-consume.example.json",
            "transaction.boundary.failed-closed.example.json",
            "transaction.boundary.export-manifest-prepare.example.json",
        ]
        for name in names:
            payload = self.transaction_example(name)
            with self.subTest(name=name):
                validated = self.validator.validate(payload, "transaction.boundary")
                self.assertEqual("transaction.boundary", validated["contract_name"])

    def test_evidence_ledger_examples_validate(self):
        names = [
            "evidence.ledger.entry.pre-action.example.json",
            "evidence.ledger.entry.replay-denial.example.json",
            "evidence.ledger.entry.export-manifest.example.json",
            "evidence.ledger.entry.rollback.example.json",
        ]
        for name in names:
            payload = self.ledger_example(name)
            with self.subTest(name=name):
                validated = self.validator.validate(payload, "evidence.ledger.entry")
                self.assertEqual("evidence.ledger.entry", validated["contract_name"])

    def test_transaction_failed_closed_requires_failure_reason_and_evidence(self):
        payload = self.transaction_example("transaction.boundary.failed-closed.example.json")
        payload["failure_reason"] = None
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.boundary")

        payload = self.transaction_example("transaction.boundary.failed-closed.example.json")
        payload["evidence_refs"] = []
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.boundary")

    def test_committed_transaction_requires_committed_at(self):
        payload = self.transaction_example("transaction.boundary.guardian-replay-consume.example.json")
        payload["committed_at"] = None
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.boundary")

    def test_rolled_back_transaction_requires_rolled_back_at(self):
        payload = self.transaction_example("transaction.boundary.guardian-replay-consume.example.json")
        payload["transaction_status"] = "rolled_back"
        payload["committed_at"] = None
        payload["rolled_back_at"] = None
        payload["failure_reason"] = "rolled back after precondition mismatch"
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.boundary")

    def test_ledger_entry_raw_content_included_must_be_false(self):
        payload = self.ledger_example("evidence.ledger.entry.pre-action.example.json")
        payload["raw_content_included"] = True
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "evidence.ledger.entry")

    def test_ledger_entry_secret_material_included_must_be_false(self):
        payload = self.ledger_example("evidence.ledger.entry.pre-action.example.json")
        payload["secret_material_included"] = True
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "evidence.ledger.entry")

    def test_ledger_hash_fields_are_metadata_only(self):
        payload = self.ledger_example("evidence.ledger.entry.replay-denial.example.json")
        validated = self.validator.validate(payload, "evidence.ledger.entry")
        self.assertTrue(validated["content_hash"])
        self.assertTrue(validated["entry_hash"])
        self.assertIn(validated["hash_algorithm"], {"sha256", "sha512"})
        payload["raw_payload"] = "forbidden"
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "evidence.ledger.entry")

    def test_export_manifest_transaction_is_refs_only(self):
        payload = self.transaction_example("transaction.boundary.export-manifest-prepare.example.json")
        validated = self.validator.validate(payload, "transaction.boundary")
        self.assertIn("build_refs_only_manifest", validated["required_operations"])
        payload["raw_payload"] = "not-allowed"
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.boundary")

    def test_no_helper_authorizes_real_storage_or_disk_write(self):
        replay_store = InMemoryReplayStore(self.validator)
        manifest_builder = EvidenceExportManifestBuilder(self.validator)
        replay_record = copy.deepcopy(example("replay.store.record.failed-closed.example.json"))
        manifest = copy.deepcopy(example("evidence.export_manifest.prepared-redacted.example.json"))

        with tempfile.TemporaryDirectory() as tmp:
            before = {p.name for p in Path(tmp).iterdir()}
            replay_store.fail_closed(
                replay_record,
                failure_reason="Mock-only fail-closed replay state.",
                evidence_refs=["ev-mock-failed-closed-001"],
            )
            manifest_builder.validate_manifest(manifest)
            after = {p.name for p in Path(tmp).iterdir()}

        self.assertEqual(before, after)
        self.assertTrue(replay_store.records)


if __name__ == "__main__":
    unittest.main()
