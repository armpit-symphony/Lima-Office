import copy
import importlib.util
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.attestation_reconciliation import reconcile_attestation_metadata


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_attestation_reconciliation", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class AttestationRevocationReconciliationDrillsTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()
        self.now = datetime(2026, 5, 25, 14, 55, tzinfo=UTC)

    def _baseline(self):
        lineage = copy.deepcopy(example("attestation.result.lineage.current.example.json"))
        authority = copy.deepcopy(example("attestation.authority.verifier-owner-active.example.json"))
        reference = copy.deepcopy(example("attestation.reference_value.active-runtime.example.json"))
        endorsement = copy.deepcopy(example("attestation.endorsement.trusted-placeholder.example.json"))
        appraisal_policy = copy.deepcopy(example("attestation.appraisal_policy.active-worker.example.json"))
        attestation_result = copy.deepcopy(example("attestation.result.pass-metadata-only.example.json"))
        worker_attestation = copy.deepcopy(example("worker.attestation.attested-metadata-only.example.json"))
        worker_lifecycle = copy.deepcopy(example("worker.lifecycle.example.json"))
        worker_heartbeat = copy.deepcopy(example("worker.heartbeat.example.json"))
        device_trust = copy.deepcopy(example("governance.device_trust.operator-managed.example.json"))
        model_route = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        transaction_boundary = copy.deepcopy(
            example("transaction.boundary.guardian-replay-consume.example.json")
        )
        coordinator_event = copy.deepcopy(
            example("transaction.coordinator.event.committed.example.json")
        )
        ledger_entry = copy.deepcopy(example("evidence.ledger.entry.pre-action.example.json"))

        shared_tenant = lineage["tenant_id"]
        shared_customer = lineage["customer_context_id"]
        for payload in (
            authority,
            reference,
            endorsement,
            appraisal_policy,
            attestation_result,
            worker_attestation,
            worker_lifecycle,
            worker_heartbeat,
            device_trust,
            model_route,
            transaction_boundary,
            coordinator_event,
            ledger_entry,
        ):
            payload["tenant_id"] = shared_tenant
            payload["customer_context_id"] = shared_customer
            if "taxonomy_version" in payload:
                payload["taxonomy_version"] = lineage["taxonomy_version"]
        worker_lifecycle["lifecycle_state"] = "active"

        model_route["route_status"] = "denied"
        model_route["risk_tier"] = "high"
        model_route["route_reason_codes"] = ["attestation_revocation_pending"]
        model_route["evidence_refs"] = ["ev-model-route-safe-001"]
        model_route["policy_refs"] = ["policy.model.routing.phase1a"]
        transaction_boundary["transaction_status"] = "failed_closed"
        transaction_boundary["failure_reason"] = "attestation_reconciliation_drift"
        transaction_boundary["reason_codes"] = ["attestation_reconciliation_drift"]
        transaction_boundary["evidence_refs"] = ["ev-txn-safe-001"]
        coordinator_event["event_status"] = "failed"
        coordinator_event["event_type"] = "transaction_failed_closed"
        coordinator_event["failure_reason"] = "attestation_reconciliation_drift"
        coordinator_event["reason_codes"] = ["attestation_reconciliation_drift"]
        coordinator_event["evidence_refs"] = ["ev-coord-safe-001"]
        attestation_result["trust_effect"] = "trusted_metadata_only"
        attestation_result["appraisal_result"] = "pass"
        attestation_result["expires_at"] = "2026-05-25T16:55:00Z"
        lineage["trust_effect"] = "trusted_metadata_only"
        lineage["lineage_status"] = "current"
        lineage["revocation_propagation_status"] = "not_required"
        lineage["evidence_refs"] = ["ev-lineage-safe-001"]

        return {
            "lineage": lineage,
            "authorities": [authority],
            "reference_values": [reference],
            "endorsements": [endorsement],
            "appraisal_policy": appraisal_policy,
            "attestation_result": attestation_result,
            "worker_attestation": worker_attestation,
            "worker_lifecycle": worker_lifecycle,
            "worker_heartbeat": worker_heartbeat,
            "device_trust": device_trust,
            "model_routes": [model_route],
            "transaction_boundaries": [transaction_boundary],
            "coordinator_events": [coordinator_event],
            "ledger_entries": [ledger_entry],
        }

    def test_reconciliation_examples_validate(self):
        self.validator.validate(
            example("attestation.reconciliation.reconciled.example.json"),
            "attestation.reconciliation",
        )
        self.validator.validate(
            example("attestation.reconciliation.reference-revoked-drift.example.json"),
            "attestation.reconciliation",
        )
        self.validator.validate(
            example("attestation.reconciliation.quarantine-required.example.json"),
            "attestation.reconciliation",
        )
        self.validator.validate(
            example("attestation.reconciliation.failed-closed-cross-tenant.example.json"),
            "attestation.reconciliation",
        )
        self.validator.validate(
            example("console.alert.attestation-reconciliation-drift.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.attestation-reconciliation-blocked.example.json"),
            "supervisor.health",
        )

    def test_valid_reconciled_metadata_passes_as_metadata_only(self):
        args = self._baseline()
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertEqual("reconciled", result["reconciliation_status"])
        self.assertEqual([], result["drift_classes"])
        self.assertFalse(result["can_authorize"])

    def test_revoked_reference_with_current_lineage_fails(self):
        args = self._baseline()
        args["reference_values"][0]["reference_status"] = "revoked"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertIn("reference_value_revoked_but_lineage_current", result["drift_classes"])
        self.assertIn("trusted_result_with_revoked_reference", result["reason_codes"])

    def test_revoked_endorsement_with_trusted_result_fails(self):
        args = self._baseline()
        args["endorsements"][0]["endorsement_status"] = "revoked"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertIn("endorsement_revoked_but_result_trusted", result["drift_classes"])
        self.assertIn("trusted_result_with_revoked_endorsement", result["reason_codes"])

    def test_revoked_appraisal_policy_with_selected_model_route_fails(self):
        args = self._baseline()
        args["appraisal_policy"]["policy_status"] = "revoked"
        args["model_routes"][0]["route_status"] = "selected"
        args["model_routes"][0]["risk_tier"] = "high"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertIn("appraisal_policy_revoked_but_route_selected", result["drift_classes"])
        self.assertIn("appraisal_policy_revoked_but_active", result["reason_codes"])

    def test_expired_result_with_active_worker_fails(self):
        args = self._baseline()
        args["attestation_result"]["expires_at"] = "2026-05-25T13:00:00Z"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertIn("attestation_result_expired_but_worker_active", result["drift_classes"])

    def test_revocation_pending_blocks_privileged_model_route_metadata(self):
        args = self._baseline()
        args["lineage"]["revocation_propagation_status"] = "pending"
        args["model_routes"][0]["route_status"] = "selected"
        args["model_routes"][0]["risk_tier"] = "high"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertEqual("revocation_pending", result["reconciliation_status"])
        self.assertIn("revocation_pending_but_privileged_route_selected", result["drift_classes"])
        self.assertIn("attestation_revocation_not_propagated", result["reason_codes"])

    def test_quarantine_required_but_worker_active_fails(self):
        args = self._baseline()
        args["lineage"]["lineage_status"] = "quarantine_required"
        args["worker_lifecycle"]["worker_state"] = "active"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertEqual("quarantine_required", result["reconciliation_status"])
        self.assertIn("quarantine_required_but_worker_active", result["drift_classes"])

    def test_selected_model_route_with_untrusted_lineage_fails(self):
        args = self._baseline()
        args["lineage"]["lineage_status"] = "revoked"
        args["lineage"]["trust_effect"] = "revoked"
        args["model_routes"][0]["route_status"] = "selected"
        args["model_routes"][0]["risk_tier"] = "high"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertIn("model_route_selected_with_untrusted_lineage", result["drift_classes"])

    def test_committed_transaction_with_revoked_attestation_fails(self):
        args = self._baseline()
        args["lineage"]["lineage_status"] = "revoked"
        args["lineage"]["trust_effect"] = "revoked"
        args["transaction_boundaries"][0]["transaction_status"] = "committed"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertIn("transaction_committed_with_revoked_attestation", result["drift_classes"])

    def test_missing_revocation_evidence_fails(self):
        args = self._baseline()
        args["lineage"]["lineage_status"] = "revoked"
        args["lineage"]["evidence_refs"] = []
        args["attestation_result"]["evidence_refs"] = []
        args["transaction_boundaries"][0]["evidence_refs"] = []
        args["coordinator_events"][0]["evidence_refs"] = []
        args["model_routes"][0]["evidence_refs"] = []
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertEqual("failed_closed", result["reconciliation_status"])
        self.assertIn("evidence_missing_for_revocation", result["drift_classes"])

    def test_cross_tenant_attestation_linkage_fails(self):
        args = self._baseline()
        args["reference_values"][0]["tenant_id"] = "tenant_other"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertEqual("failed_closed", result["reconciliation_status"])
        self.assertIn("cross_tenant_attestation_linkage", result["drift_classes"])

    def test_revoked_verifier_authority_fails(self):
        args = self._baseline()
        args["authorities"][0]["authority_status"] = "revoked"
        args["model_routes"][0]["route_status"] = "selected"
        args["model_routes"][0]["risk_tier"] = "high"
        result = reconcile_attestation_metadata(**args, now=self.now)
        self.assertIn("verifier_authority_revoked_but_appraisal_active", result["drift_classes"])
        self.assertIn("verifier_authority_conflict", result["reason_codes"])

    def test_helper_never_verifies_tpm_certs_signatures_network_storage(self):
        source = (ROOT / "lima_office" / "runtime" / "attestation_reconciliation.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("tpm2_", "cryptography", "requests.", "socket.", "sqlite3", "subprocess.")
        for token in banned_tokens:
            self.assertNotIn(token, source)
        result = reconcile_attestation_metadata(**self._baseline(), now=self.now)
        self.assertFalse(result["can_authorize"])

    def test_reason_code_gate_passes_new_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
