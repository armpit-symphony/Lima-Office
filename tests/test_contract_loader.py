import tempfile
import unittest
from pathlib import Path

from lima_office.contracts import ContractLoader
from lima_office.runtime.errors import ContractLoadError


class ContractLoaderTests(unittest.TestCase):
    def test_loads_all_v1_schemas(self):
        loader = ContractLoader().load()
        self.assertEqual(19, len(loader.schema_keys))
        self.assertIn("guardian.decision", loader.contract_names)
        self.assertEqual("guardian.decision", loader.resolve_key("guardian.decision.schema.json"))

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
