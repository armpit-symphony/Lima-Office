import copy
import socket
import unittest
from unittest.mock import patch

from helpers import example, has_jsonschema, validator
from lima_office.runtime.errors import (
    UnsafeRuntimeActionError,
    WorkerLifecycleTransitionError,
    WorkerLifecycleValidationError,
)
from lima_office.supervisor import WorkerLifecycleSimulator


def deployment_payload(state: str = "provisioned") -> dict:
    payload = copy.deepcopy(example("worker.deployment.lightweight.example.json"))
    payload["worker_id"] = "arc-file-01"
    payload["tenant_id"] = "tenant-lab-001"
    payload["lifecycle_state"] = state
    payload["environment"] = "phase0_lab"
    payload["reason_codes"] = []
    payload["attestation_status"] = "not_required_phase0"
    payload["trust_root_status"] = "software_only_placeholder"
    payload["blocked_reason"] = None
    payload["security_reviewer_ref"] = None
    payload["attestation_result_ref"] = None
    payload["privileged_task_metadata_allowed"] = False
    payload["install_state"] = "enrolled_mock"
    payload["risk_tier"] = "low"
    if state == "provisioned":
        payload["install_state"] = "preflight_ready"
    if state == "quarantined":
        payload["install_state"] = "quarantined"
        payload["blocked_reason"] = "quarantine_triggered"
        payload["security_reviewer_ref"] = "security-reviewer-001"
        payload["risk_tier"] = "high"
        payload["privileged_task_metadata_allowed"] = False
    if state == "revoked":
        payload["install_state"] = "blocked"
        payload["blocked_reason"] = "revoked"
        payload["risk_tier"] = "blocked"
        payload["privileged_task_metadata_allowed"] = False
    if state == "reenrollment_pending":
        payload["install_state"] = "blocked"
        payload["blocked_reason"] = "reenrollment_pending"
        payload["risk_tier"] = "blocked"
    if state == "retired":
        payload["install_state"] = "retired"
        payload["risk_tier"] = "low"
    return payload


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class WorkerLifecycleSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.simulator = WorkerLifecycleSimulator(self.validator)

    def test_valid_lifecycle_examples_validate(self):
        self.validator.validate(example("worker.lifecycle.example.json"), "worker.lifecycle")
        self.validator.validate(example("worker.deployment.lightweight.example.json"), "worker.deployment")

    def test_provisioned_to_enrolled_to_active_passes(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        result = self.simulator.transition(deployment_payload("active"))
        self.assertEqual("active", result["lifecycle_state"])
        self.assertFalse(result["authorization_allowed"])

    def test_active_to_degraded_to_active_passes(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("active"))
        self.simulator.transition(deployment_payload("degraded"))
        result = self.simulator.transition(deployment_payload("active"))
        self.assertEqual("active", result["lifecycle_state"])

    def test_active_to_quarantined_passes(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("active"))
        result = self.simulator.transition(deployment_payload("quarantined"))
        self.assertEqual("quarantined", result["lifecycle_state"])

    def test_quarantined_reenrollment_path_to_active_passes(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("active"))
        self.simulator.transition(deployment_payload("quarantined"))
        self.simulator.transition(deployment_payload("reenrollment_pending"))
        self.simulator.transition(deployment_payload("enrolled"))
        result = self.simulator.transition(deployment_payload("active"))
        self.assertEqual("active", result["lifecycle_state"])

    def test_active_to_revoked_passes(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("active"))
        result = self.simulator.transition(deployment_payload("revoked"))
        self.assertEqual("revoked", result["lifecycle_state"])

    def test_active_to_retired_passes(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("active"))
        result = self.simulator.transition(deployment_payload("retired"))
        self.assertEqual("retired", result["lifecycle_state"])

    def test_revoked_to_active_fails(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("active"))
        self.simulator.transition(deployment_payload("revoked"))
        with self.assertRaises(WorkerLifecycleTransitionError):
            self.simulator.transition(deployment_payload("active"))

    def test_retired_to_active_fails(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("retired"))
        with self.assertRaises(WorkerLifecycleTransitionError):
            self.simulator.transition(deployment_payload("active"))

    def test_quarantined_to_active_direct_fails(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        self.simulator.transition(deployment_payload("active"))
        self.simulator.transition(deployment_payload("quarantined"))
        with self.assertRaises(WorkerLifecycleTransitionError):
            self.simulator.transition(deployment_payload("active"))

    def test_blocked_mvp_to_active_fails(self):
        blocked = deployment_payload("provisioned")
        blocked["environment"] = "blocked_mvp"
        self.simulator.register(blocked)
        blocked_enrolled = deployment_payload("enrolled")
        blocked_enrolled["environment"] = "blocked_mvp"
        self.simulator.transition(blocked_enrolled)
        blocked_active = deployment_payload("active")
        blocked_active["environment"] = "blocked_mvp"
        with self.assertRaises(WorkerLifecycleTransitionError):
            self.simulator.transition(blocked_active)

    def test_unknown_worker_fails(self):
        with self.assertRaises(WorkerLifecycleTransitionError):
            self.simulator.transition(deployment_payload("enrolled"))

    def test_tenant_mismatch_fails(self):
        self.simulator.register(deployment_payload("provisioned"))
        mismatched = deployment_payload("enrolled")
        mismatched["tenant_id"] = "tenant-other"
        with self.assertRaises(WorkerLifecycleTransitionError):
            self.simulator.transition(mismatched)

    def test_attestation_failed_blocks_active(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        blocked = deployment_payload("active")
        blocked["attestation_status"] = "failed"
        blocked["attestation_result_ref"] = "att-result-ref-001"
        blocked["install_state"] = "blocked"
        blocked["risk_tier"] = "blocked"
        blocked["reason_codes"] = ["attestation_failed"]
        with self.assertRaises(WorkerLifecycleValidationError):
            self.simulator.transition(blocked)

    def test_device_untrusted_blocks_active(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        blocked = deployment_payload("active")
        blocked["reason_codes"] = ["device_untrusted"]
        with self.assertRaises(WorkerLifecycleTransitionError):
            self.simulator.transition(blocked)

    def test_history_is_in_memory_only(self):
        self.simulator.register(deployment_payload("provisioned"))
        self.simulator.transition(deployment_payload("enrolled"))
        history = self.simulator.history("arc-file-01")
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual("provisioned", history[0]["to_state"])
        self.assertEqual("enrolled", history[-1]["to_state"])

    def test_simulator_never_writes_files(self):
        self.simulator.register(deployment_payload("provisioned"))
        with patch("pathlib.Path.write_text", side_effect=AssertionError("unexpected file write")):
            with patch("pathlib.Path.write_bytes", side_effect=AssertionError("unexpected file write")):
                self.simulator.transition(deployment_payload("enrolled"))

    def test_simulator_never_calls_network(self):
        self.simulator.register(deployment_payload("provisioned"))
        with patch.object(socket, "create_connection", side_effect=AssertionError("unexpected network call")):
            self.simulator.transition(deployment_payload("enrolled"))

    def test_simulator_never_authorizes_real_actions(self):
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.authorize_real_action("task", worker_id="arc-file-01")


if __name__ == "__main__":
    unittest.main()
