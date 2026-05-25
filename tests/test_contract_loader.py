import tempfile
import unittest
from pathlib import Path

from lima_office.contracts import ContractLoader
from lima_office.runtime.errors import ContractLoadError


class ContractLoaderTests(unittest.TestCase):
    def test_loads_all_v1_schemas(self):
        loader = ContractLoader().load()
        self.assertEqual(57, len(loader.schema_keys))
        self.assertIn("approval.binding", loader.contract_names)
        self.assertIn("approval.chain", loader.contract_names)
        self.assertIn("transaction.boundary", loader.contract_names)
        self.assertIn("transaction.coordinator.event", loader.contract_names)
        self.assertIn("evidence.ledger.entry", loader.contract_names)
        self.assertIn("replay.store.record", loader.contract_names)
        self.assertIn("evidence.export_manifest", loader.contract_names)
        self.assertIn("guardian.decision", loader.contract_names)
        self.assertIn("guardian.replay", loader.contract_names)
        self.assertIn("worker.deployment", loader.contract_names)
        self.assertIn("worker.attestation", loader.contract_names)
        self.assertIn("attestation.reference_value", loader.contract_names)
        self.assertIn("attestation.endorsement", loader.contract_names)
        self.assertIn("attestation.appraisal_policy", loader.contract_names)
        self.assertIn("attestation.result", loader.contract_names)
        self.assertIn("attestation.result.lineage", loader.contract_names)
        self.assertIn("attestation.authority", loader.contract_names)
        self.assertIn("attestation.reconciliation", loader.contract_names)
        self.assertIn("connector.readiness", loader.contract_names)
        self.assertIn("connector.scope_review", loader.contract_names)
        self.assertIn("connector.provider_profile", loader.contract_names)
        self.assertIn("connector.revocation_drill", loader.contract_names)
        self.assertIn("update.rollback", loader.contract_names)
        self.assertIn("governance.identity", loader.contract_names)
        self.assertIn("governance.rbac_matrix", loader.contract_names)
        self.assertIn("governance.session_policy", loader.contract_names)
        self.assertIn("governance.device_trust", loader.contract_names)
        self.assertIn("governance.update_record", loader.contract_names)
        self.assertIn("governance.export_delete_review", loader.contract_names)
        self.assertIn("reason.code.registry", loader.contract_names)
        self.assertIn("reason.code.compatibility", loader.contract_names)
        self.assertIn("console.view", loader.contract_names)
        self.assertIn("console.alert", loader.contract_names)
        self.assertIn("console.action", loader.contract_names)
        self.assertIn("supervisor.health", loader.contract_names)
        self.assertEqual("guardian.decision", loader.resolve_key("guardian.decision.schema.json"))
        self.assertEqual("guardian.replay", loader.resolve_key("guardian.replay.schema.json"))

    def test_unknown_schema_fails_closed(self):
        loader = ContractLoader().load()
        with self.assertRaises(ContractLoadError):
            loader.get_schema("missing.contract")

    def test_missing_schema_dir_fails_closed(self):
        with self.assertRaises(ContractLoadError):
            ContractLoader(Path("does-not-exist")).load()

    def test_bad_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.schema.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ContractLoadError):
                ContractLoader(path.parent).load()

    def test_contract_name_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrong.schema.json"
            path.write_text(
                '{"type":"object","properties":{"contract_name":{"const":"other"}}}',
                encoding="utf-8",
            )
            with self.assertRaises(ContractLoadError):
                ContractLoader(path.parent).load()


if __name__ == "__main__":
    unittest.main()
