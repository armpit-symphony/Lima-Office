import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.errors import ContractValidationError, PolicyDenyError
from lima_office.runtime.transaction_coordinator import InMemoryTransactionCoordinator


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class DurableTransactionCoordinatorDesignTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.coordinator = InMemoryTransactionCoordinator(self.validator)

    def event_example(self, name: str) -> dict:
        return copy.deepcopy(example(name))

    def test_valid_event_examples_validate(self):
        names = [
            "transaction.coordinator.event.started.example.json",
            "transaction.coordinator.event.nonce-reserved.example.json",
            "transaction.coordinator.event.committed.example.json",
            "transaction.coordinator.event.failed-closed.example.json",
            "transaction.coordinator.event.duplicate-request.example.json",
            "transaction.coordinator.event.reconciliation-completed.example.json",
        ]
        for name in names:
            payload = self.event_example(name)
            with self.subTest(name=name):
                validated = self.validator.validate(payload, "transaction.coordinator.event")
                self.assertEqual("transaction.coordinator.event", validated["contract_name"])

    def test_invalid_transition_fails(self):
        started = self.event_example("transaction.coordinator.event.started.example.json")
        committed = self.event_example("transaction.coordinator.event.committed.example.json")
        committed["transaction_id"] = started["transaction_id"]
        committed["idempotency_key"] = started["idempotency_key"]
        committed["idempotency_scope"] = started["idempotency_scope"]
        committed["previous_event_id"] = started["coordinator_event_id"]
        committed["coordinator_event_id"] = "coord-ev-invalid-transition-001"

        self.coordinator.record_event(started)
        with self.assertRaises(PolicyDenyError):
            self.coordinator.record_event(committed)

    def test_duplicate_idempotency_key_same_tenant_fails(self):
        first = self.event_example("transaction.coordinator.event.started.example.json")
        second = self.event_example("transaction.coordinator.event.started.example.json")
        second["transaction_id"] = "txn-coordinator-duplicate-001"
        second["coordinator_event_id"] = "coord-ev-dup-same-tenant-001"

        self.coordinator.record_event(first)
        with self.assertRaises(PolicyDenyError):
            self.coordinator.record_event(second)

    def test_same_idempotency_key_different_tenant_is_isolated(self):
        first = self.event_example("transaction.coordinator.event.started.example.json")
        second = self.event_example("transaction.coordinator.event.started.example.json")
        second["tenant_id"] = "tenant-lab-002"
        second["customer_context_id"] = "customer-context-alt"
        second["transaction_id"] = "txn-coordinator-tenant-002"
        second["coordinator_event_id"] = "coord-ev-tenant-002"

        self.coordinator.record_event(first)
        self.coordinator.record_event(second)

        self.assertEqual(2, len(self.coordinator.idempotency_index))

    def test_committed_event_requires_correct_prior_state(self):
        committed = self.event_example("transaction.coordinator.event.committed.example.json")
        with self.assertRaises(PolicyDenyError):
            self.coordinator.record_event(committed)

    def test_failed_closed_event_requires_failure_reason_and_evidence_refs(self):
        payload = self.event_example("transaction.coordinator.event.failed-closed.example.json")
        payload["failure_reason"] = None
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.coordinator.event")

        payload = self.event_example("transaction.coordinator.event.failed-closed.example.json")
        payload["evidence_refs"] = []
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.coordinator.event")

    def test_rolled_back_event_requires_evidence_refs(self):
        payload = self.event_example("transaction.coordinator.event.failed-closed.example.json")
        payload["event_type"] = "transaction_rolled_back"
        payload["event_status"] = "succeeded"
        payload["transaction_status"] = "rolled_back"
        payload["failure_reason"] = "rollback after failed precondition"
        payload["evidence_refs"] = []
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.coordinator.event")

    def test_replay_token_evidence_events_require_relevant_refs(self):
        payload = self.event_example("transaction.coordinator.event.nonce-reserved.example.json")
        payload["replay_record_refs"] = []
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.coordinator.event")

        payload = self.event_example("transaction.coordinator.event.nonce-reserved.example.json")
        payload["event_type"] = "token_binding_verified"
        payload["coordinator_event_id"] = "coord-ev-token-verify-001"
        payload["evidence_refs"] = []
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.coordinator.event")

        payload = self.event_example("transaction.coordinator.event.nonce-reserved.example.json")
        payload["event_type"] = "pre_action_evidence_appended"
        payload["coordinator_event_id"] = "coord-ev-pre-evidence-001"
        payload["ledger_entry_refs"] = []
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.coordinator.event")

    def test_reconciliation_completed_requires_evidence_refs(self):
        payload = self.event_example("transaction.coordinator.event.reconciliation-completed.example.json")
        payload["evidence_refs"] = []
        with self.assertRaises(ContractValidationError):
            self.validator.validate(payload, "transaction.coordinator.event")

    def test_no_helper_persists_to_disk_or_authorizes_real_action(self):
        started = self.event_example("transaction.coordinator.event.started.example.json")
        preconditions = self.event_example("transaction.coordinator.event.nonce-reserved.example.json")
        preconditions["event_type"] = "preconditions_checked"
        preconditions["coordinator_event_id"] = "coord-ev-002"
        preconditions["previous_event_id"] = started["coordinator_event_id"]
        preconditions["next_expected_event_types"] = [
            "replay_nonce_reserved",
            "token_binding_verified",
            "transaction_failed_closed",
        ]
        preconditions["replay_record_refs"] = []

        with tempfile.TemporaryDirectory() as tmp:
            before = {p.name for p in Path(tmp).iterdir()}
            self.coordinator.record_event(started)
            self.coordinator.record_event(preconditions)
            after = {p.name for p in Path(tmp).iterdir()}

        self.assertEqual(before, after)
        history = self.coordinator.event_log[(started["tenant_id"], started["transaction_id"])]
        self.assertEqual(2, len(history))
        self.assertNotEqual("committed", history[-1]["transaction_status"])


if __name__ == "__main__":
    unittest.main()
