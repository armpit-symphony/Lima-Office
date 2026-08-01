import copy
import unittest
from unittest import mock

from helpers import EXAMPLES, example, has_jsonschema, validator
from lima_office.runtime.errors import ContractValidationError


class ContractValidatorTests(unittest.TestCase):
    def test_missing_jsonschema_fails_closed(self):
        from lima_office.contracts import ContractLoader
        from lima_office.contracts import validator as validator_module

        def missing(name):
            if name == "jsonschema":
                raise ModuleNotFoundError(name)
            return __import__(name)

        with mock.patch.object(validator_module.importlib, "import_module", side_effect=missing):
            with self.assertRaises(ContractValidationError):
                validator_module.ContractValidator(ContractLoader().load())

    @unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
    def test_valid_examples_validate(self):
        runtime_validator = validator()
        for path in EXAMPLES.glob("*.json"):
            with self.subTest(path=path.name):
                runtime_validator.validate(example(path.name))

    @unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
    def test_invalid_payload_fails(self):
        runtime_validator = validator()
        payload = example("guardian.decision.example.json")
        payload["decision"] = "not-a-decision"
        with self.assertRaises(ContractValidationError):
            runtime_validator.validate(payload)

    @unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
    def test_bad_datetime_format_fails(self):
        runtime_validator = validator()
        payload = copy.deepcopy(example("worker.heartbeat.example.json"))
        payload["producer"]["produced_at"] = "not-a-date"
        with self.assertRaises(ContractValidationError):
            runtime_validator.validate(payload)


if __name__ == "__main__":
    unittest.main()
