import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.linkage import CrossContractLinkageValidator


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class CrossContractLinkageHardeningTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.linkage = CrossContractLinkageValidator()

    def _aligned_bundle(
        self,
        *,
        tenant_id: str = "tenant-lab-001",
        customer_context_id: str = "customer-context-main",
        correlation_id: str = "corr-linkage-001",
        idempotency_key: str = "idem-linkage-001",
        transaction_id: str = "txn-linkage-001",
        decision_nonce: str = "decision-nonce-linkage-001",
    ) -> tuple[dict, dict, dict, list[dict], dict[str, dict], dict]:
        coordinator = copy.deepcopy(example("transaction.coordinator.event.committed.example.json"))
        boundary = copy.deepcopy(example("transaction.boundary.guardian-replay-consume.example.json"))
        replay = copy.deepcopy(example("replay.store.record.consumed.example.json"))
        ledger = [copy.deepcopy(example("evidence.ledger.entry.pre-action.example.json"))]
        artifact = copy.deepcopy(example("evidence.artifact.chained-pre-post.example.json"))
        manifest = copy.deepcopy(example("evidence.export_manifest.prepared-redacted.example.json"))

        artifact_id = artifact["artifact_id"]
        ledger_entry_id = ledger[0]["ledger_entry_id"]
        replay_record_id = replay["replay_record_id"]

        payloads = [coordinator, boundary, replay, ledger[0], artifact, manifest]
        for payload in payloads:
            payload["tenant_id"] = tenant_id
            payload["customer_context_id"] = customer_context_id
            payload["correlation_id"] = correlation_id
            payload["idempotency_key"] = idempotency_key
            if "canonical_tenant_id" in payload:
                payload["canonical_tenant_id"] = tenant_id
            if "canonical_correlation_id" in payload:
                payload["canonical_correlation_id"] = correlation_id
            if "canonical_idempotency_key" in payload:
                payload["canonical_idempotency_key"] = idempotency_key

        coordinator["transaction_id"] = transaction_id
        coordinator["related_transaction_id"] = transaction_id
        coordinator["related_replay_record_ids"] = [replay_record_id]
        coordinator["related_ledger_entry_ids"] = [ledger_entry_id]
        coordinator["related_evidence_artifact_ids"] = [artifact_id]
        coordinator["canonical_decision_nonce"] = decision_nonce
        coordinator["canonical_action_type"] = replay["action_type"]
        coordinator["canonical_tool_scope"] = copy.deepcopy(replay["tool_scope"])
        coordinator["canonical_worker_id"] = "arc-admin-01"
        coordinator["canonical_task_id"] = "task-email-draft-001"
        coordinator["linkage_status"] = "linked"
        coordinator["linkage_failure_reasons"] = []

        boundary["transaction_id"] = transaction_id
        boundary["related_transaction_id"] = transaction_id
        boundary["related_replay_record_ids"] = [replay_record_id]
        boundary["related_ledger_entry_ids"] = [ledger_entry_id]
        boundary["related_evidence_artifact_ids"] = [artifact_id]
        boundary["canonical_decision_nonce"] = decision_nonce
        boundary["canonical_action_type"] = replay["action_type"]
        boundary["canonical_tool_scope"] = copy.deepcopy(replay["tool_scope"])
        boundary["canonical_worker_id"] = "arc-admin-01"
        boundary["canonical_task_id"] = "task-email-draft-001"
        boundary["linkage_status"] = "linked"
        boundary["linkage_failure_reasons"] = []

        replay["decision_nonce"] = decision_nonce
        replay["canonical_decision_nonce"] = decision_nonce
        replay["related_transaction_id"] = transaction_id
        replay["related_coordinator_event_ids"] = [coordinator["coordinator_event_id"]]
        replay["related_ledger_entry_ids"] = [ledger_entry_id]
        replay["related_evidence_artifact_ids"] = [artifact_id]
        replay["canonical_action_type"] = replay["action_type"]
        replay["canonical_tool_scope"] = copy.deepcopy(replay["tool_scope"])
        replay["canonical_worker_id"] = "arc-admin-01"
        replay["canonical_task_id"] = "task-email-draft-001"
        replay["linkage_status"] = "linked"
        replay["linkage_failure_reasons"] = []

        ledger[0]["related_transaction_id"] = transaction_id
        ledger[0]["related_coordinator_event_ids"] = [coordinator["coordinator_event_id"]]
        ledger[0]["related_replay_record_ids"] = [replay_record_id]
        ledger[0]["related_ledger_entry_ids"] = [ledger_entry_id]
        ledger[0]["related_evidence_artifact_ids"] = [artifact_id]
        ledger[0]["canonical_decision_nonce"] = decision_nonce
        ledger[0]["canonical_action_type"] = replay["action_type"]
        ledger[0]["canonical_worker_id"] = "arc-admin-01"
        ledger[0]["canonical_task_id"] = "task-email-draft-001"
        ledger[0]["linkage_status"] = "linked"
        ledger[0]["linkage_failure_reasons"] = []

        artifact["related_transaction_id"] = transaction_id
        artifact["related_coordinator_event_ids"] = [coordinator["coordinator_event_id"]]
        artifact["related_replay_record_ids"] = [replay_record_id]
        artifact["related_ledger_entry_ids"] = [ledger_entry_id]
        artifact["related_evidence_artifact_ids"] = [artifact_id]
        artifact["canonical_decision_nonce"] = decision_nonce
        artifact["canonical_action_type"] = replay["action_type"]
        artifact["canonical_tool_scope"] = copy.deepcopy(replay["tool_scope"])
        artifact["canonical_worker_id"] = "arc-admin-01"
        artifact["canonical_task_id"] = "task-email-draft-001"
        artifact["linkage_status"] = "linked"
        artifact["linkage_failure_reasons"] = []

        manifest["related_transaction_id"] = transaction_id
        manifest["related_coordinator_event_ids"] = [coordinator["coordinator_event_id"]]
        manifest["related_replay_record_ids"] = [replay_record_id]
        manifest["related_ledger_entry_ids"] = [ledger_entry_id]
        manifest["related_evidence_artifact_ids"] = [artifact_id]
        manifest["related_export_manifest_ids"] = [manifest["export_manifest_id"]]
        manifest["included_evidence_refs"] = [artifact_id]
        manifest["excluded_evidence_refs"] = []
        manifest["evidence_refs"] = [artifact_id]
        manifest["canonical_decision_nonce"] = decision_nonce
        manifest["canonical_action_type"] = "export_manifest_prepare"
        manifest["canonical_worker_id"] = None
        manifest["canonical_task_id"] = "task-email-draft-001"
        manifest["linkage_status"] = "linked"
        manifest["linkage_failure_reasons"] = []

        evidence_artifacts = {artifact_id: artifact}
        return coordinator, boundary, replay, ledger, evidence_artifacts, manifest

    def _validate_contracts(self, coordinator, boundary, replay, ledger_entries, evidence_artifacts, manifest):
        self.validator.validate(coordinator, "transaction.coordinator.event")
        self.validator.validate(boundary, "transaction.boundary")
        self.validator.validate(replay, "replay.store.record")
        for entry in ledger_entries:
            self.validator.validate(entry, "evidence.ledger.entry")
        for artifact in evidence_artifacts.values():
            self.validator.validate(artifact, "evidence.artifact")
        self.validator.validate(manifest, "evidence.export_manifest")

    def test_valid_chain_passes(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        self._validate_contracts(coordinator, boundary, replay, ledger, evidence_artifacts, manifest)
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
            expected_nonce="decision-nonce-linkage-001",
        )
        self.assertEqual("linked", result["linkage_status"])
        self.assertEqual([], result["failure_reasons"])
        self.assertEqual(result["failure_reasons"], result["linkage_failure_reasons"])

    def test_coordinator_wrong_transaction_id_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        coordinator["transaction_id"] = "txn-other"
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("coordinator_transaction_mismatch", result["linkage_failure_reasons"])

    def test_transaction_replay_cross_tenant_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        replay["tenant_id"] = "tenant-other"
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("replay_record_tenant_mismatch", result["linkage_failure_reasons"])

    def test_replay_wrong_nonce_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        replay["decision_nonce"] = "decision-nonce-other"
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
            expected_nonce="decision-nonce-linkage-001",
        )
        self.assertIn("replay_nonce_mismatch", result["linkage_failure_reasons"])

    def test_replay_action_scope_mismatch_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        replay["canonical_action_type"] = "file_review"
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("replay_action_type_mismatch", result["linkage_failure_reasons"])

    def test_ledger_wrong_tenant_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        ledger[0]["tenant_id"] = "tenant-other"
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("ledger_tenant_mismatch", result["linkage_failure_reasons"])

    def test_ledger_parent_chain_mismatch_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        ledger[0]["chain_position"] = 2
        ledger[0]["previous_hash"] = "hash-parent-unknown"
        ledger[0]["parent_entry_ids"] = ["ledger-entry-missing-parent"]
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("ledger_parent_missing", result["linkage_failure_reasons"])

    def test_evidence_artifact_raw_content_true_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        only_artifact = next(iter(evidence_artifacts.values()))
        only_artifact["raw_content_included"] = True
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("artifact_raw_content_included", result["linkage_failure_reasons"])

    def test_export_manifest_non_evidence_ref_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        manifest["included_evidence_refs"] = ["not-evidence-ref"]
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("manifest_included_non_evidence_ref", result["linkage_failure_reasons"])

    def test_export_manifest_cross_tenant_ref_fails(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        artifact_id = next(iter(evidence_artifacts.keys()))
        evidence_artifacts[artifact_id]["tenant_id"] = "tenant-other"
        manifest["included_evidence_refs"] = [artifact_id]
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("manifest_cross_tenant_evidence_ref", result["linkage_failure_reasons"])

    def test_delete_export_conflict_is_blocked_status(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        manifest["export_status"] = "denied"
        manifest["delete_conflict_refs"] = ["conflict-delete-export-001"]
        manifest["prepared_at"] = None
        manifest["exported_at"] = None
        manifest["hash_manifest_ref"] = None
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertEqual("blocked_mvp", result["linkage_status"])

    def test_reconciliation_drift_detected(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        coordinator["event_type"] = "transaction_failed_closed"
        coordinator["transaction_status"] = "failed_closed"
        coordinator["event_status"] = "failed"
        coordinator["failure_reason"] = "failed closed for drift test"
        coordinator["linkage_status"] = "drift_detected"
        coordinator["linkage_failure_reasons"] = ["forced_failed_closed_for_drift"]
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("reconciliation_drift_terminal_state", result["linkage_failure_reasons"])

    def test_duplicate_idempotency_key_same_tenant_detected(self):
        bundle_1 = self._aligned_bundle(transaction_id="txn-linkage-001")
        bundle_2 = self._aligned_bundle(transaction_id="txn-linkage-002")
        self.linkage.validate_chain(
            coordinator_event=bundle_1[0],
            transaction_boundary=bundle_1[1],
            replay_record=bundle_1[2],
            ledger_entries=bundle_1[3],
            evidence_artifacts=bundle_1[4],
            export_manifest=bundle_1[5],
        )
        result = self.linkage.validate_chain(
            coordinator_event=bundle_2[0],
            transaction_boundary=bundle_2[1],
            replay_record=bundle_2[2],
            ledger_entries=bundle_2[3],
            evidence_artifacts=bundle_2[4],
            export_manifest=bundle_2[5],
        )
        self.assertIn("duplicate_idempotency_key_same_tenant", result["linkage_failure_reasons"])

    def test_same_idempotency_key_different_tenant_is_isolated(self):
        bundle_1 = self._aligned_bundle(tenant_id="tenant-lab-001", transaction_id="txn-linkage-001")
        bundle_2 = self._aligned_bundle(tenant_id="tenant-lab-002", transaction_id="txn-linkage-002")
        self.linkage.validate_chain(
            coordinator_event=bundle_1[0],
            transaction_boundary=bundle_1[1],
            replay_record=bundle_1[2],
            ledger_entries=bundle_1[3],
            evidence_artifacts=bundle_1[4],
            export_manifest=bundle_1[5],
        )
        result = self.linkage.validate_chain(
            coordinator_event=bundle_2[0],
            transaction_boundary=bundle_2[1],
            replay_record=bundle_2[2],
            ledger_entries=bundle_2[3],
            evidence_artifacts=bundle_2[4],
            export_manifest=bundle_2[5],
        )
        self.assertNotIn("duplicate_idempotency_key_same_tenant", result["linkage_failure_reasons"])

    def test_canonical_tenant_mismatch_is_detected(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        boundary["canonical_tenant_id"] = "tenant-other"
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
        )
        self.assertIn("transaction_boundary_canonical_tenant_mismatch", result["linkage_failure_reasons"])
        self.assertEqual("mismatched_tenant", result["linkage_status"])

    def test_guardian_and_binding_optional_linkage_checks(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        guardian_decision = copy.deepcopy(example("guardian.decision.allowed-one-time.example.json"))
        approval_binding = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
        for payload in (guardian_decision, approval_binding):
            payload["tenant_id"] = coordinator["tenant_id"]
            payload["customer_context_id"] = coordinator["customer_context_id"]
            payload["correlation_id"] = coordinator["correlation_id"]
            payload["idempotency_key"] = coordinator["idempotency_key"]
        guardian_decision["decision_nonce"] = replay["decision_nonce"]
        guardian_decision["bound_action_type"] = replay["action_type"]
        guardian_decision["bound_tool_scope"] = copy.deepcopy(replay["tool_scope"])
        guardian_decision["approval_binding_id"] = replay["approval_binding_id"]
        approval_binding["binding_id"] = replay["approval_binding_id"]
        approval_binding["bound_action_type"] = replay["action_type"]
        approval_binding["bound_tool_scope"] = copy.deepcopy(replay["tool_scope"])

        guardian_decision["bound_action_type"] = "file_review"
        result = self.linkage.validate_chain(
            coordinator_event=coordinator,
            transaction_boundary=boundary,
            replay_record=replay,
            ledger_entries=ledger,
            evidence_artifacts=evidence_artifacts,
            export_manifest=manifest,
            guardian_decision=guardian_decision,
            approval_binding=approval_binding,
        )
        self.assertIn("guardian_action_type_mismatch", result["linkage_failure_reasons"])

    def test_helper_does_not_persist_or_authorize_real_action(self):
        coordinator, boundary, replay, ledger, evidence_artifacts, manifest = self._aligned_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            before = {path.name for path in Path(tmp).iterdir()}
            result = self.linkage.validate_chain(
                coordinator_event=coordinator,
                transaction_boundary=boundary,
                replay_record=replay,
                ledger_entries=ledger,
                evidence_artifacts=evidence_artifacts,
                export_manifest=manifest,
            )
            after = {path.name for path in Path(tmp).iterdir()}
        self.assertEqual(before, after)
        self.assertFalse(result["can_authorize"])


if __name__ == "__main__":
    unittest.main()
