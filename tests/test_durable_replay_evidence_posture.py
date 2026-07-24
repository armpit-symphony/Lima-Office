import copy
import tempfile
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.evidence import EvidenceExportManifestBuilder
from lima_office.guardian import InMemoryReplayStore
from lima_office.runtime.errors import ContractValidationError, CrossContractInvariantError, EvidenceRequiredError, PolicyDenyError
from lima_office.runtime.invariants import (
    assert_evidence_artifact_chain_consistent,
    assert_evidence_export_manifest_consistent,
    assert_replay_store_record_consistent,
)


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class DurableReplayEvidencePostureTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.replay_store = InMemoryReplayStore(self.validator)
        self.manifest_builder = EvidenceExportManifestBuilder(self.validator)

    def replay_record(self, name: str = "replay.store.record.consumed.example.json") -> dict:
        return copy.deepcopy(example(name))

    def guardian_decision(self) -> dict:
        return copy.deepcopy(example("guardian.decision.allowed-one-time.example.json"))

    def approval_binding(self) -> dict:
        return copy.deepcopy(example("approval.binding.bound-valid.example.json"))

    def requested_action(self, **updates) -> dict:
        decision = self.guardian_decision()
        action = {
            "tenant_id": decision["tenant_id"],
            "customer_context_id": decision["customer_context_id"],
            "task_id": decision["bound_task_id"],
            "worker_id": decision["bound_worker_id"],
            "guardian_decision_id": decision["decision_id"],
            "approval_binding_id": decision["approval_binding_id"],
            "binding_id": decision["binding_id"],
            "token_verification_id": decision["token_verification_id"],
            "action_type": decision["bound_action_type"],
            "tool_scope": copy.deepcopy(decision["bound_tool_scope"]),
            "decision_scope_hash": decision["decision_scope_hash"],
            "evidence_required": True,
            "evidence_refs": ["ev-guardian-email-draft-001"],
        }
        action.update(updates)
        return action

    def test_consumed_replay_store_record_passes_metadata_validation(self):
        record = self.replay_record()
        checked = assert_replay_store_record_consistent(
            record,
            requested_action=self.requested_action(),
            guardian_decision=self.guardian_decision(),
            approval_binding=self.approval_binding(),
            for_authorization=False,
        )
        self.assertEqual("consumed", checked["nonce_status"])

    def test_replay_denied_record_requires_evidence_refs(self):
        record = self.replay_record("replay.store.record.replay-denied.example.json")
        record["evidence_refs"] = []
        with self.assertRaises(EvidenceRequiredError):
            assert_replay_store_record_consistent(record, for_authorization=False)

    def test_failed_closed_replay_store_record_blocks_action(self):
        record = self.replay_record("replay.store.record.failed-closed.example.json")
        with self.assertRaises(PolicyDenyError):
            assert_replay_store_record_consistent(record, for_authorization=True)

    def test_nonce_cannot_be_consumed_twice(self):
        record = self.replay_record()
        record["nonce_status"] = "reserved"
        record["atomicity_status"] = "pending"
        record["consumed_at"] = None
        record["replay_record_id"] = "rr-email-draft-reserved-001"
        first = self.replay_store.authorize_first_use(
            record,
            requested_action=self.requested_action(),
            guardian_decision=self.guardian_decision(),
            approval_binding=self.approval_binding(),
        )
        self.assertEqual("consumed", first["nonce_status"])
        with self.assertRaises(PolicyDenyError):
            self.replay_store.authorize_first_use(
                record,
                requested_action=self.requested_action(),
                guardian_decision=self.guardian_decision(),
                approval_binding=self.approval_binding(),
            )

    def test_replay_record_tenant_mismatch_fails(self):
        record = self.replay_record()
        with self.assertRaises(PolicyDenyError):
            assert_replay_store_record_consistent(
                record,
                requested_action=self.requested_action(tenant_id="tenant-other"),
                for_authorization=False,
            )

    def test_replay_record_action_scope_mismatch_fails(self):
        record = self.replay_record()
        mismatched_scope = copy.deepcopy(record["tool_scope"])
        mismatched_scope["resource_refs"] = ["draft-message-ref-other-002"]
        with self.assertRaises(PolicyDenyError):
            assert_replay_store_record_consistent(
                record,
                requested_action=self.requested_action(action_type="file_review", tool_scope=mismatched_scope),
                for_authorization=False,
            )

    def test_denial_path_evidence_artifact_validates(self):
        artifact = copy.deepcopy(example("evidence.artifact.denial-path.example.json"))
        validated = self.validator.validate(artifact, "evidence.artifact")
        checked = assert_evidence_artifact_chain_consistent(validated, expected_tenant_id=artifact["tenant_id"])
        self.assertEqual("denial", checked["artifact_type"])

    def test_evidence_chain_tenant_mismatch_fails(self):
        artifact = copy.deepcopy(example("evidence.artifact.chained-pre-post.example.json"))
        parent = copy.deepcopy(example("evidence.artifact.denial-path.example.json"))
        parent["artifact_id"] = "ev-task-transition-pre-001"
        parent["tenant_id"] = "tenant-other"
        with self.assertRaises(CrossContractInvariantError):
            assert_evidence_artifact_chain_consistent(
                artifact,
                evidence_by_id={"ev-task-transition-pre-001": parent},
            )

    def test_evidence_export_manifest_contains_refs_only(self):
        manifest = copy.deepcopy(example("evidence.export_manifest.prepared-redacted.example.json"))
        evidence_map = {
            "ev-guardian-email-draft-001": copy.deepcopy(example("evidence.artifact.denial-path.example.json")),
            "ev-guardian-replay-valid-001": {
                "artifact_id": "ev-guardian-replay-valid-001",
                "tenant_id": manifest["tenant_id"],
                "raw_content_included": False,
                "secret_material_included": False,
            },
            "ev-approval-result-email-001": {
                "artifact_id": "ev-approval-result-email-001",
                "tenant_id": manifest["tenant_id"],
                "raw_content_included": False,
                "secret_material_included": False,
            },
            "ev-sensitive-payload-ref-001": {
                "artifact_id": "ev-sensitive-payload-ref-001",
                "tenant_id": manifest["tenant_id"],
                "raw_content_included": False,
                "secret_material_included": False,
            },
        }
        for evidence_ref in set(
            manifest.get("included_evidence_refs", [])
            + manifest.get("excluded_evidence_refs", [])
            + manifest.get("evidence_refs", [])
        ):
            evidence_map.setdefault(
                evidence_ref,
                {
                    "artifact_id": evidence_ref,
                    "tenant_id": manifest["tenant_id"],
                    "raw_content_included": False,
                    "secret_material_included": False,
                },
            )
        checked = self.manifest_builder.validate_manifest(manifest, evidence_by_id=evidence_map)
        self.assertGreaterEqual(len(checked["included_evidence_refs"]), 1)

    def test_export_manifest_with_raw_or_secret_content_fails(self):
        manifest = copy.deepcopy(example("evidence.export_manifest.prepared-redacted.example.json"))
        manifest["raw_content_included"] = True
        with self.assertRaises((ContractValidationError, PolicyDenyError)):
            self.manifest_builder.validate_manifest(manifest)

    def test_delete_export_conflict_is_represented_as_denied(self):
        manifest = copy.deepcopy(example("evidence.export_manifest.denied-delete-conflict.example.json"))
        checked = assert_evidence_export_manifest_consistent(manifest)
        self.assertEqual("denied", checked["export_status"])
        self.assertTrue(checked["delete_conflict_refs"])

    def test_replay_store_unavailable_results_in_fail_closed_state(self):
        record = self.replay_record()
        failed = self.replay_store.fail_closed(
            record,
            failure_reason="Replay store unavailable; action failed closed.",
            evidence_refs=["ev-replay-store-unavailable-001"],
        )
        self.assertEqual("failed_closed", failed["atomicity_status"])
        with self.assertRaises(PolicyDenyError):
            assert_replay_store_record_consistent(failed, for_authorization=True)

    def test_no_helper_can_persist_to_disk_or_authorize_real_actions(self):
        record = self.replay_record()
        record["nonce_status"] = "reserved"
        record["atomicity_status"] = "pending"
        record["consumed_at"] = None
        record["action_type"] = "external_send"
        with tempfile.TemporaryDirectory() as tmp:
            before = {path.name for path in Path(tmp).iterdir()}
            with self.assertRaises(PolicyDenyError):
                self.replay_store.authorize_first_use(record, requested_action={"action_type": "external_send"})
            manifest = copy.deepcopy(example("evidence.export_manifest.denied-delete-conflict.example.json"))
            self.manifest_builder.validate_manifest(manifest)
            after = {path.name for path in Path(tmp).iterdir()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
