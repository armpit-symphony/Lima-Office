import copy
import socket
import unittest
from unittest.mock import patch

from helpers import example, has_jsonschema, validator
from lima_office.evidence import EvidenceLifecycleSimulator
from lima_office.runtime.errors import (
    EvidenceLifecycleTransitionError,
    EvidenceLifecycleValidationError,
    UnsafeRuntimeActionError,
)


def artifact_payload(*, artifact_id: str, artifact_type: str = "task_transition") -> dict:
    payload = copy.deepcopy(example("evidence.artifact.chained-pre-post.example.json"))
    payload["artifact_id"] = artifact_id
    payload["artifact_type"] = artifact_type
    payload["environment"] = "phase0_lab"
    payload["correlation_id"] = f"corr-{artifact_id}"
    payload["idempotency_key"] = f"idem-{artifact_id}"
    payload["chain_position"] = 1
    payload["parent_evidence_refs"] = []
    payload["previous_artifact_id"] = None
    payload["summary"] = f"Evidence metadata for {artifact_id}."
    if artifact_type != "denial":
        payload["denial_evidence_ref"] = None
        payload["pre_action_evidence_refs"] = []
    return payload


def denial_payload(*, artifact_id: str) -> dict:
    payload = copy.deepcopy(example("evidence.artifact.denial-path.example.json"))
    payload["artifact_id"] = artifact_id
    payload["correlation_id"] = f"corr-{artifact_id}"
    payload["idempotency_key"] = f"idem-{artifact_id}"
    payload["denial_evidence_ref"] = artifact_id
    payload["pre_action_evidence_refs"] = [artifact_id]
    return payload


def failed_closed_payload(*, failure_id: str) -> dict:
    payload = copy.deepcopy(example("evidence.failure.pre-action-blocked.example.json"))
    payload["evidence_failure_id"] = failure_id
    payload["correlation_id"] = f"corr-{failure_id}"
    payload["idempotency_key"] = f"idem-{failure_id}"
    payload["denial_evidence_ref"] = failure_id
    payload["pre_action_evidence_refs"] = [failure_id]
    payload["failure_reason"] = "mock failed-closed evidence posture"
    return payload


def ledger_payload(*, ledger_entry_id: str, entry_type: str = "post_action") -> dict:
    payload = copy.deepcopy(example("evidence.ledger.entry.pre-action.example.json"))
    payload["ledger_entry_id"] = ledger_entry_id
    payload["evidence_id"] = ledger_entry_id
    payload["entry_type"] = entry_type
    payload["correlation_id"] = f"corr-{ledger_entry_id}"
    payload["idempotency_key"] = f"idem-{ledger_entry_id}"
    payload["related_evidence_artifact_ids"] = [ledger_entry_id]
    if entry_type == "replay_denial":
        payload["parent_entry_ids"] = ["ledger-entry-pre-action-parent-001"]
        payload["previous_hash"] = "hash-entry-pre-action-parent-001"
        payload["chain_position"] = 2
    return payload


def export_manifest_payload(*, export_manifest_id: str, exported: bool = False) -> dict:
    if exported:
        payload = copy.deepcopy(example("evidence.export_manifest.exported-redacted-metadata-only.example.json"))
    else:
        payload = copy.deepcopy(example("evidence.export_manifest.prepared-redacted.example.json"))
    payload["export_manifest_id"] = export_manifest_id
    payload["correlation_id"] = f"corr-{export_manifest_id}"
    payload["idempotency_key"] = f"idem-{export_manifest_id}"
    payload["included_evidence_refs"] = [export_manifest_id]
    payload["excluded_evidence_refs"] = []
    payload["evidence_refs"] = [export_manifest_id]
    payload["conflict_evidence_refs"] = []
    payload["related_evidence_artifact_ids"] = [export_manifest_id]
    return payload


def guardian_allow(task_id: str) -> dict:
    payload = copy.deepcopy(example("guardian.decision.allowed-one-time.example.json"))
    payload["decision_id"] = f"gd-{task_id}"
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["request_id"] = f"req-{task_id}"
    payload["valid_for_action_ref"] = f"scope-{task_id}"
    payload["decision_scope_hash"] = f"scope-{task_id}"
    payload["tenant_id"] = "tenant-lab-001"
    payload["customer_context_id"] = "customer-context-main"
    payload["subject"] = {"subject_type": "task", "subject_id": task_id}
    payload["bound_tenant_id"] = "tenant-lab-001"
    payload["bound_task_id"] = task_id
    payload["bound_worker_id"] = "arc-it-helper-01"
    payload["bound_action_type"] = "form_preparation_review"
    payload["action_class"] = "tool_invocation"
    payload["approval_binding_id"] = None
    payload["binding_id"] = None
    payload["approval_chain_id"] = None
    payload["token_verification_id"] = None
    payload["evidence_artifact_id"] = f"ev-{task_id}-guardian"
    payload["evidence_artifact_ids"] = [f"ev-{task_id}-guardian", f"ev-{task_id}-task"]
    payload["evidence_refs"] = [f"ev-{task_id}-guardian", f"ev-{task_id}-task"]
    payload["post_action_evidence_refs"] = [f"ev-{task_id}-guardian"]
    payload["created_at"] = "2026-05-20T00:00:10Z"
    payload["issued_at"] = "2026-05-20T00:00:10Z"
    payload["effective_at"] = "2026-05-20T00:00:10Z"
    payload["expires_at"] = "2026-05-20T00:05:10Z"
    payload["decision_nonce"] = f"nonce-{task_id}"
    payload["replay_status"] = "unused"
    payload["replay_policy"] = "one_time"
    return payload


def binding_valid(task_id: str) -> dict:
    payload = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
    payload["approval_chain_id"] = f"chain-{task_id}"
    payload["binding_id"] = f"bind-{task_id}"
    payload["approval_request_id"] = f"apr-{task_id}"
    payload["approval_result_id"] = f"apres-{task_id}"
    payload["approval_token_id"] = f"apt-{task_id}"
    payload["token_verification_id"] = f"tv-{task_id}"
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["task_id"] = task_id
    payload["tool_invocation_id"] = f"tool-{task_id}"
    payload["worker_id"] = "arc-it-helper-01"
    payload["evidence_refs"] = [f"ev-{task_id}-approval", f"ev-{task_id}-task"]
    payload["created_at"] = "2026-05-18T21:43:10Z"
    payload["checked_at"] = "2026-05-18T21:43:10Z"
    payload["expires_at"] = "2026-05-20T00:10:00Z"
    return payload


def token_valid(task_id: str) -> dict:
    payload = copy.deepcopy(example("token.verification.valid.example.json"))
    payload["token_verification_id"] = f"tv-{task_id}"
    payload["approval_token_id"] = f"apt-{task_id}"
    payload["approval_request_id"] = f"apr-{task_id}"
    payload["task_id"] = task_id
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["evidence_artifact_ids"] = [f"ev-{task_id}-token-verify"]
    return payload


def task_payload(task_id: str, *, status: str = "in_progress", evidence_refs: list[str] | None = None) -> dict:
    payload = copy.deepcopy(example("task.execution.example.json"))
    payload["task_id"] = task_id
    payload["tenant_id"] = "tenant-lab-001"
    payload["customer_context_id"] = "customer-context-main"
    payload["status"] = status
    payload["guardian_decision_id"] = f"gd-{task_id}"
    payload["approval_required"] = False
    payload["assigned_worker_id"] = "arc-it-helper-01"
    payload["evidence_artifact_ids"] = [f"ev-{task_id}-task"] if evidence_refs is None else evidence_refs
    payload["task_scope"]["allowed_actions"] = ["read_health_status", "summarize_diagnostics"]
    payload["task_scope"]["blocked_actions"] = ["run_remediation"]
    payload["execution_mode"] = "mock_only"
    payload["task_class"] = "it_health_check"
    payload["risk_tier"] = "medium"
    payload["approval_chain_id"] = None
    payload["binding_id"] = None
    payload["approval_request_id"] = None
    payload["approval_result_id"] = None
    payload["approval_token_id"] = None
    payload["token_verification_id"] = None
    return payload


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class EvidenceLifecycleSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.simulator = EvidenceLifecycleSimulator(self.validator)

    def test_valid_evidence_examples_validate(self):
        self.validator.validate(example("evidence.artifact.example.json"), "evidence.artifact")
        self.validator.validate(example("evidence.failure.pre-action-blocked.example.json"), "evidence.failure")
        self.validator.validate(example("evidence.ledger.entry.pre-action.example.json"), "evidence.ledger.entry")
        self.validator.validate(
            example("evidence.export_manifest.prepared-redacted.example.json"),
            "evidence.export_manifest",
        )

    def test_registration_must_start_from_planned(self):
        evidence_id = "ev-lifecycle-start-001"
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="ledger_linked")

    def test_planned_pre_post_ledger_path_passes(self):
        evidence_id = "ev-lifecycle-pre-post-001"
        task_id = "task-evidence-pre-post-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(
            evidence_id,
            "pre_action_recorded",
            artifact_payload(artifact_id=evidence_id),
            task_execution=task_payload(task_id, status="in_progress"),
            guardian_decision=guardian_allow(task_id),
        )
        self.simulator.transition(
            evidence_id,
            "post_action_recorded",
            artifact_payload(artifact_id=evidence_id),
            task_execution=task_payload(task_id, status="completed_mock"),
            guardian_decision=guardian_allow(task_id),
        )
        result = self.simulator.transition(evidence_id, "ledger_linked", ledger_payload(ledger_entry_id=evidence_id))
        self.assertEqual("ledger_linked", result["evidence_state"])
        self.assertFalse(result["authorization_allowed"])
        self.assertFalse(result["execution_allowed"])

    def test_planned_denial_ledger_path_passes(self):
        evidence_id = "ev-lifecycle-denial-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))
        result = self.simulator.transition(evidence_id, "ledger_linked", ledger_payload(ledger_entry_id=evidence_id, entry_type="denial"))
        self.assertEqual("ledger_linked", result["evidence_state"])

    def test_planned_replay_denial_ledger_path_passes(self):
        evidence_id = "ev-lifecycle-replay-denial-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        denial = denial_payload(artifact_id=evidence_id)
        denial["linkage_failure_reasons"] = ["nonce_replay_denied"]
        self.simulator.transition(evidence_id, "replay_denial_recorded", denial)
        result = self.simulator.transition(
            evidence_id,
            "ledger_linked",
            ledger_payload(ledger_entry_id=evidence_id, entry_type="replay_denial"),
        )
        self.assertEqual("ledger_linked", result["evidence_state"])

    def test_planned_failed_closed_ledger_path_passes(self):
        evidence_id = "ev-lifecycle-failed-closed-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(
            evidence_id,
            "failed_closed_recorded",
            failed_closed_payload(failure_id=evidence_id),
        )
        result = self.simulator.transition(evidence_id, "ledger_linked", ledger_payload(ledger_entry_id=evidence_id, entry_type="denial"))
        self.assertEqual("ledger_linked", result["evidence_state"])

    def test_ledger_linked_to_export_manifest_planned_passes(self):
        evidence_id = "ev-lifecycle-export-plan-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))
        self.simulator.transition(evidence_id, "ledger_linked", ledger_payload(ledger_entry_id=evidence_id, entry_type="denial"))
        result = self.simulator.transition(
            evidence_id,
            "export_manifest_planned",
            export_manifest_payload(export_manifest_id=evidence_id, exported=False),
        )
        self.assertEqual("export_manifest_planned", result["evidence_state"])

    def test_planned_to_post_action_direct_fails(self):
        evidence_id = "ev-lifecycle-bad-transition-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(evidence_id, "post_action_recorded", artifact_payload(artifact_id=evidence_id))

    def test_same_state_transition_is_rejected_and_does_not_mutate_history(self):
        evidence_id = "ev-lifecycle-same-state-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        before = self.simulator.history(evidence_id)
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(evidence_id, "planned", artifact_payload(artifact_id=evidence_id))
        after = self.simulator.history(evidence_id)
        self.assertEqual(before, after)
        self.assertEqual(1, len(after))

    def test_exported_runtime_state_fails(self):
        evidence_id = "ev-lifecycle-exported-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))
        self.simulator.transition(evidence_id, "ledger_linked", ledger_payload(ledger_entry_id=evidence_id, entry_type="denial"))
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(
                evidence_id,
                "export_manifest_planned",
                export_manifest_payload(export_manifest_id=evidence_id, exported=True),
            )

    def test_deleted_runtime_state_fails(self):
        evidence_id = "ev-lifecycle-delete-runtime-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))
        self.simulator.transition(evidence_id, "ledger_linked", ledger_payload(ledger_entry_id=evidence_id, entry_type="denial"))
        manifest = export_manifest_payload(export_manifest_id=evidence_id, exported=False)
        manifest["delete_review_status"] = "approved"
        manifest["delete_proof_refs"] = ["proof-delete-001"]
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(evidence_id, "export_manifest_planned", manifest)

    def test_raw_content_included_true_fails(self):
        evidence_id = "ev-lifecycle-raw-001"
        payload = artifact_payload(artifact_id=evidence_id)
        payload["raw_content_included"] = True
        with self.assertRaises(EvidenceLifecycleValidationError):
            self.simulator.register(payload, initial_state="planned")

    def test_secret_material_included_true_fails(self):
        evidence_id = "ev-lifecycle-secret-001"
        payload = artifact_payload(artifact_id=evidence_id)
        payload["secret_material_included"] = True
        with self.assertRaises(EvidenceLifecycleValidationError):
            self.simulator.register(payload, initial_state="planned")

    def test_tenant_mismatch_fails(self):
        evidence_id = "ev-lifecycle-tenant-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        mismatched = denial_payload(artifact_id=evidence_id)
        mismatched["tenant_id"] = "tenant-other"
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(evidence_id, "denial_recorded", mismatched)

    def test_cross_tenant_evidence_chain_fails(self):
        self.simulator.register(artifact_payload(artifact_id="ev-chain-parent-001"), initial_state="planned")
        child = artifact_payload(artifact_id="ev-chain-child-001")
        child["tenant_id"] = "tenant-other"
        child["parent_evidence_refs"] = ["ev-chain-parent-001"]
        child["chain_position"] = 2
        child["previous_artifact_id"] = "ev-chain-parent-001"
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.register(child, initial_state="planned")

    def test_unknown_required_denial_ref_fails_closed(self):
        evidence_id = "ev-lifecycle-unknown-denial-ref-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        bad = denial_payload(artifact_id=evidence_id)
        bad["denial_evidence_ref"] = "ev-unknown-denial-001"
        bad["pre_action_evidence_refs"] = ["ev-unknown-denial-001"]
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(evidence_id, "denial_recorded", bad)

    def test_evidence_required_completion_without_evidence_refs_fails(self):
        evidence_id = "ev-lifecycle-evidence-required-001"
        task_id = "task-evidence-required-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(
                evidence_id,
                "post_action_recorded",
                artifact_payload(artifact_id=evidence_id),
                task_execution=task_payload(task_id, status="completed_mock", evidence_refs=[]),
                guardian_decision=guardian_allow(task_id),
            )

    def test_denial_without_reason_or_linkage_fails(self):
        evidence_id = "ev-lifecycle-denial-bad-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        bad = denial_payload(artifact_id=evidence_id)
        bad["linkage_failure_reasons"] = []
        with self.assertRaises(EvidenceLifecycleValidationError):
            self.simulator.transition(evidence_id, "denial_recorded", bad)

    def test_malformed_evidence_refs_fail(self):
        evidence_id = "ev-lifecycle-malformed-ref-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        bad = denial_payload(artifact_id=evidence_id)
        bad["denial_evidence_ref"] = "not-an-evidence-ref"
        with self.assertRaises(EvidenceLifecycleValidationError):
            self.simulator.transition(evidence_id, "denial_recorded", bad)

    def test_state_contract_intent_mismatch_fails(self):
        evidence_id = "ev-lifecycle-state-contract-mismatch-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(
            evidence_id,
            "pre_action_recorded",
            artifact_payload(artifact_id=evidence_id),
            task_execution=task_payload("task-state-contract-mismatch", status="in_progress"),
            guardian_decision=guardian_allow("task-state-contract-mismatch"),
        )
        self.simulator.transition(
            evidence_id,
            "post_action_recorded",
            artifact_payload(artifact_id=evidence_id),
            task_execution=task_payload("task-state-contract-mismatch", status="completed_mock"),
            guardian_decision=guardian_allow("task-state-contract-mismatch"),
        )
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(
                evidence_id,
                "ledger_linked",
                artifact_payload(artifact_id=evidence_id),
            )

    def test_external_placeholder_refs_fail_closed(self):
        evidence_id = "ev-lifecycle-placeholder-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))
        self.simulator.transition(evidence_id, "ledger_linked", ledger_payload(ledger_entry_id=evidence_id, entry_type="denial"))
        manifest = export_manifest_payload(export_manifest_id=evidence_id)
        manifest["excluded_evidence_refs"] = ["ev-placeholder-third-party-001"]
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(evidence_id, "export_manifest_planned", manifest)

    def test_register_can_generate_metadata_only_record_id_when_supplied(self):
        payload = artifact_payload(artifact_id="ev-temp-generated-001")
        payload.pop("artifact_id")
        result = self.simulator.register(payload, initial_state="planned", evidence_id="ev-generated-001")
        self.assertEqual("ev-generated-001", result["evidence_id"])

    def test_history_is_in_memory_only(self):
        evidence_id = "ev-lifecycle-history-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))
        history = self.simulator.history(evidence_id)
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual("planned", history[0]["to_state"])
        self.assertEqual("denial_recorded", history[-1]["to_state"])

    def test_simulator_never_writes_files(self):
        evidence_id = "ev-lifecycle-file-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        with patch("pathlib.Path.write_text", side_effect=AssertionError("unexpected file write")):
            with patch("pathlib.Path.write_bytes", side_effect=AssertionError("unexpected file write")):
                self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))

    def test_simulator_never_calls_network(self):
        evidence_id = "ev-lifecycle-net-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        with patch.object(socket, "create_connection", side_effect=AssertionError("unexpected network call")):
            self.simulator.transition(evidence_id, "denial_recorded", denial_payload(artifact_id=evidence_id))

    def test_simulator_never_performs_export_or_delete_or_authorization(self):
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.export_evidence("ev-001")
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.delete_evidence("ev-001")
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.execute_tools("ev-001")
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.authorize_real_action("ev-001")

    def test_approval_required_metadata_requires_binding_and_token(self):
        evidence_id = "ev-lifecycle-approval-001"
        task_id = "task-evidence-approval-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        task = task_payload(task_id, status="in_progress")
        task["approval_required"] = True
        task["approval_request_id"] = f"apr-{task_id}"
        task["approval_result_id"] = f"apres-{task_id}"
        task["approval_token_id"] = f"apt-{task_id}"
        task["token_verification_id"] = f"tv-{task_id}"
        task["approval_chain_id"] = f"chain-{task_id}"
        task["binding_id"] = f"bind-{task_id}"
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(
                evidence_id,
                "pre_action_recorded",
                artifact_payload(artifact_id=evidence_id),
                task_execution=task,
                guardian_decision=guardian_allow(task_id),
            )

        result = self.simulator.transition(
            evidence_id,
            "pre_action_recorded",
            artifact_payload(artifact_id=evidence_id),
            task_execution=task,
            guardian_decision=guardian_allow(task_id),
            approval_binding=binding_valid(task_id),
            token_verification=token_valid(task_id),
        )
        self.assertEqual("pre_action_recorded", result["evidence_state"])

    def test_rejects_unknown_state(self):
        evidence_id = "ev-lifecycle-unknown-state-001"
        self.simulator.register(artifact_payload(artifact_id=evidence_id), initial_state="planned")
        with self.assertRaises(EvidenceLifecycleTransitionError):
            self.simulator.transition(evidence_id, "exported", denial_payload(artifact_id=evidence_id))

    def test_invalid_payload_type_fails_validation(self):
        with self.assertRaises(EvidenceLifecycleValidationError):
            self.simulator.register("bad payload", initial_state="planned")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
