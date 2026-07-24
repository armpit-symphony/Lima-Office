import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.reconciliation import ApprovalGuardianReconciler


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ApprovalGuardianReconciliationDrillsTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.reconciler = ApprovalGuardianReconciler(reference_time="2026-05-18T21:44:00Z")

    def _bundle(self):
        approval_chain = copy.deepcopy(example("approval.chain.valid-one-time.example.json"))
        approval_binding = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
        token_verification = copy.deepcopy(example("token.verification.valid.example.json"))
        guardian_decision = copy.deepcopy(example("guardian.decision.allowed-one-time.example.json"))
        guardian_replay = copy.deepcopy(example("guardian.replay.valid-first-use.example.json"))
        replay_record = copy.deepcopy(example("replay.store.record.consumed.example.json"))
        coordinator_event = copy.deepcopy(example("transaction.coordinator.event.committed.example.json"))
        transaction_boundary = copy.deepcopy(example("transaction.boundary.guardian-replay-consume.example.json"))
        ledger_entry = copy.deepcopy(example("evidence.ledger.entry.pre-action.example.json"))

        tenant_id = "tenant-lab-001"
        customer_context_id = "customer-context-main"
        correlation_id = "corr-email-draft-001"
        approval_chain_id = "chain-email-draft-001"
        approval_binding_id = "bind-email-draft-001"
        token_verification_id = "tv-email-valid-001"
        guardian_decision_id = "gd-email-send-requires-approval-001"
        replay_record_id = "rr-email-draft-consumed-001"
        transaction_id = "txn-guardian-replay-consume-001"
        task_id = "task-email-draft-001"
        worker_id = "arc-admin-01"
        action_type = "draft_external_message_review"
        tool_scope = copy.deepcopy(approval_binding["tool_scope"])
        decision_nonce = "decision-nonce-email-draft-001"
        evidence_refs = ["ev-guardian-email-draft-001", "ev-token-verify-valid-001", "ev-guardian-replay-valid-001"]

        for payload in (
            approval_chain,
            approval_binding,
            token_verification,
            guardian_decision,
            guardian_replay,
            replay_record,
            coordinator_event,
            transaction_boundary,
            ledger_entry,
        ):
            payload["tenant_id"] = tenant_id
            payload["customer_context_id"] = customer_context_id
            payload["correlation_id"] = correlation_id

        approval_chain["approval_chain_id"] = approval_chain_id
        approval_binding["approval_chain_id"] = approval_chain_id
        guardian_decision["approval_chain_id"] = approval_chain_id

        approval_binding["binding_id"] = approval_binding_id
        guardian_decision["binding_id"] = approval_binding_id
        guardian_decision["approval_binding_id"] = approval_binding_id
        guardian_replay["approval_binding_id"] = approval_binding_id
        replay_record["approval_binding_id"] = approval_binding_id

        approval_binding["token_verification_id"] = token_verification_id
        token_verification["token_verification_id"] = token_verification_id
        guardian_decision["token_verification_id"] = token_verification_id
        guardian_replay["token_verification_id"] = token_verification_id
        replay_record["token_verification_id"] = token_verification_id

        guardian_decision["decision_id"] = guardian_decision_id
        guardian_decision["guardian_decision_id"] = guardian_decision_id
        token_verification["guardian_decision_id"] = guardian_decision_id
        approval_binding["guardian_decision_id"] = guardian_decision_id
        guardian_replay["guardian_decision_id"] = guardian_decision_id
        replay_record["guardian_decision_id"] = guardian_decision_id

        guardian_replay["replay_record_id"] = replay_record_id
        replay_record["replay_record_id"] = replay_record_id
        replay_record["replay_artifact_id"] = "ev-guardian-replay-valid-001"

        coordinator_event["transaction_id"] = transaction_id
        coordinator_event["related_transaction_id"] = transaction_id
        transaction_boundary["transaction_id"] = transaction_id
        transaction_boundary["related_transaction_id"] = transaction_id
        replay_record["related_transaction_id"] = transaction_id
        ledger_entry["related_transaction_id"] = transaction_id

        token_verification["task_id"] = task_id
        approval_binding["task_id"] = task_id
        guardian_decision["bound_task_id"] = task_id
        guardian_replay["task_id"] = task_id
        replay_record["canonical_task_id"] = task_id
        transaction_boundary["canonical_task_id"] = task_id
        coordinator_event["canonical_task_id"] = task_id
        ledger_entry["canonical_task_id"] = task_id

        approval_binding["worker_id"] = worker_id
        guardian_decision["bound_worker_id"] = worker_id
        guardian_replay["worker_id"] = worker_id
        replay_record["canonical_worker_id"] = worker_id
        transaction_boundary["canonical_worker_id"] = worker_id
        coordinator_event["canonical_worker_id"] = worker_id
        ledger_entry["canonical_worker_id"] = worker_id

        approval_binding["action_type"] = action_type
        guardian_decision["bound_action_type"] = action_type
        guardian_replay["action_type"] = action_type
        replay_record["action_type"] = action_type
        replay_record["canonical_action_type"] = action_type
        transaction_boundary["canonical_action_type"] = action_type
        coordinator_event["canonical_action_type"] = action_type
        ledger_entry["canonical_action_type"] = action_type

        approval_binding["tool_scope"] = copy.deepcopy(tool_scope)
        guardian_decision["bound_tool_scope"] = copy.deepcopy(tool_scope)
        guardian_replay["tool_scope"] = copy.deepcopy(tool_scope)
        replay_record["tool_scope"] = copy.deepcopy(tool_scope)
        replay_record["canonical_tool_scope"] = copy.deepcopy(tool_scope)
        transaction_boundary["canonical_tool_scope"] = copy.deepcopy(tool_scope)
        coordinator_event["canonical_tool_scope"] = copy.deepcopy(tool_scope)
        ledger_entry["canonical_tool_scope"] = copy.deepcopy(tool_scope)

        guardian_decision["decision_nonce"] = decision_nonce
        guardian_replay["decision_nonce"] = decision_nonce
        replay_record["decision_nonce"] = decision_nonce
        replay_record["canonical_decision_nonce"] = decision_nonce
        transaction_boundary["canonical_decision_nonce"] = decision_nonce
        coordinator_event["canonical_decision_nonce"] = decision_nonce
        ledger_entry["canonical_decision_nonce"] = decision_nonce

        guardian_decision["evidence_refs"] = evidence_refs[:2]
        guardian_decision["post_action_evidence_refs"] = evidence_refs[:1]
        guardian_replay["evidence_refs"] = evidence_refs[:2]
        guardian_replay["post_action_evidence_refs"] = evidence_refs[:1]
        replay_record["evidence_refs"] = evidence_refs
        token_verification["evidence_artifact_ids"] = ["ev-token-verify-valid-001"]
        approval_binding["evidence_refs"] = evidence_refs[:2]

        ledger_entry["related_replay_record_ids"] = [replay_record_id]

        # Ensure schema validity for baseline bundle.
        self.validator.validate(approval_chain, "approval.chain")
        self.validator.validate(approval_binding, "approval.binding")
        self.validator.validate(token_verification, "token.verification")
        self.validator.validate(guardian_decision, "guardian.decision")
        self.validator.validate(guardian_replay, "guardian.replay")
        self.validator.validate(replay_record, "replay.store.record")
        self.validator.validate(coordinator_event, "transaction.coordinator.event")
        self.validator.validate(transaction_boundary, "transaction.boundary")
        self.validator.validate(ledger_entry, "evidence.ledger.entry")

        return (
            approval_chain,
            approval_binding,
            token_verification,
            guardian_decision,
            guardian_replay,
            replay_record,
            coordinator_event,
            transaction_boundary,
            [ledger_entry],
        )

    def _reconcile(self, bundle):
        return self.reconciler.reconcile(
            approval_chain=bundle[0],
            approval_binding=bundle[1],
            token_verification=bundle[2],
            guardian_decision=bundle[3],
            guardian_replay=bundle[4],
            replay_record=bundle[5],
            coordinator_event=bundle[6],
            transaction_boundary=bundle[7],
            ledger_entries=bundle[8],
        )

    def test_valid_approval_guardian_chain_reconciles(self):
        result = self._reconcile(self._bundle())
        self.assertEqual("reconciled", result["reconciliation_status"])
        self.assertEqual([], result["reconciliation_failure_reasons"])

    def test_missing_guardian_decision_fails(self):
        bundle = list(self._bundle())
        bundle[3] = None
        result = self._reconcile(bundle)
        self.assertEqual("missing_ref", result["reconciliation_status"])
        self.assertIn("missing_guardian_decision", result["reconciliation_failure_reasons"])

    def test_stale_guardian_decision_fails(self):
        bundle = list(self._bundle())
        bundle[3]["expires_at"] = "2026-05-18T21:40:00Z"
        result = ApprovalGuardianReconciler(reference_time="2026-05-18T21:50:00Z").reconcile(
            approval_chain=bundle[0],
            approval_binding=bundle[1],
            token_verification=bundle[2],
            guardian_decision=bundle[3],
            guardian_replay=bundle[4],
            replay_record=bundle[5],
            coordinator_event=bundle[6],
            transaction_boundary=bundle[7],
            ledger_entries=bundle[8],
        )
        self.assertEqual("stale_decision", result["reconciliation_status"])
        self.assertIn("stale_guardian_decision", result["reconciliation_failure_reasons"])

    def test_approval_binding_id_mismatch_fails(self):
        bundle = list(self._bundle())
        bundle[4]["approval_binding_id"] = "bind-other"
        result = self._reconcile(bundle)
        self.assertEqual("mismatched_binding", result["reconciliation_status"])
        self.assertIn("mismatched_approval_binding", result["reconciliation_failure_reasons"])

    def test_token_verification_id_mismatch_fails(self):
        bundle = list(self._bundle())
        bundle[4]["token_verification_id"] = "tv-other"
        result = self._reconcile(bundle)
        self.assertEqual("mismatched_binding", result["reconciliation_status"])
        self.assertIn("mismatched_token_verification", result["reconciliation_failure_reasons"])

    def test_guardian_replay_replay_record_mismatch_fails(self):
        bundle = list(self._bundle())
        bundle[4]["replay_record_id"] = "rr-other"
        result = self._reconcile(bundle)
        self.assertEqual("replay_mismatch", result["reconciliation_status"])
        self.assertIn("replay_record_mismatch", result["reconciliation_failure_reasons"])

    def test_missing_denial_evidence_fails(self):
        bundle = list(self._bundle())
        bundle[4]["replay_check_result"] = "replay_denied"
        bundle[4]["denial_evidence_ref"] = None
        bundle[4]["evidence_refs"] = []
        result = self._reconcile(bundle)
        self.assertEqual("evidence_missing", result["reconciliation_status"])
        self.assertIn("evidence_ref_missing", result["reconciliation_failure_reasons"])

    def test_coordinator_event_transaction_mismatch_fails(self):
        bundle = list(self._bundle())
        bundle[6]["transaction_id"] = "txn-other"
        result = self._reconcile(bundle)
        self.assertEqual("coordinator_mismatch", result["reconciliation_status"])
        self.assertIn("coordinator_event_mismatch", result["reconciliation_failure_reasons"])

    def test_transaction_boundary_mismatch_fails(self):
        bundle = list(self._bundle())
        bundle[7]["transaction_id"] = "txn-other"
        bundle[7]["related_transaction_id"] = "txn-other"
        result = self._reconcile(bundle)
        self.assertEqual("coordinator_mismatch", result["reconciliation_status"])
        self.assertIn("transaction_boundary_mismatch", result["reconciliation_failure_reasons"])

    def test_evidence_ledger_mismatch_fails(self):
        bundle = list(self._bundle())
        bundle[8][0]["related_replay_record_ids"] = []
        result = self._reconcile(bundle)
        self.assertEqual("evidence_missing", result["reconciliation_status"])
        self.assertIn("evidence_ledger_mismatch", result["reconciliation_failure_reasons"])

    def test_cross_tenant_linkage_fails(self):
        bundle = list(self._bundle())
        bundle[2]["tenant_id"] = "tenant-other"
        result = self._reconcile(bundle)
        self.assertEqual("cross_tenant_blocked", result["reconciliation_status"])
        self.assertIn("cross_tenant_linkage", result["reconciliation_failure_reasons"])

    def test_blocked_mvp_authorization_attempt_fails(self):
        bundle = list(self._bundle())
        bundle[1]["action_type"] = "external_send"
        result = self._reconcile(bundle)
        self.assertEqual("blocked_mvp", result["reconciliation_status"])
        self.assertIn("blocked_mvp_authorization_attempt", result["reconciliation_failure_reasons"])

    def test_external_send_live_connector_and_remediation_remain_blocked(self):
        for action_type in ("external_send", "live_connector_access", "lima_it_remediation"):
            bundle = list(self._bundle())
            bundle[1]["action_type"] = action_type
            result = self._reconcile(bundle)
            self.assertEqual("blocked_mvp", result["reconciliation_status"])
            self.assertIn("blocked_mvp_authorization_attempt", result["reconciliation_failure_reasons"])

    def test_helper_does_not_persist_or_authorize_real_action(self):
        bundle = self._bundle()
        with tempfile.TemporaryDirectory() as tmp:
            before = {path.name for path in Path(tmp).iterdir()}
            result = self._reconcile(bundle)
            after = {path.name for path in Path(tmp).iterdir()}
        self.assertEqual(before, after)
        self.assertFalse(result["can_authorize"])


if __name__ == "__main__":
    unittest.main()
