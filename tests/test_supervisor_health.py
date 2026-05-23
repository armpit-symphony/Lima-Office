import unittest

from helpers import guardian_allow_decision, has_jsonschema, task_example, validator
from lima_office.evidence import EvidenceWriter
from lima_office.guardian import GuardianPolicy
from lima_office.supervisor import SupervisorHealthReporter, TaskQueue, WorkerRegistry


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class SupervisorHealthTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()

    def make_registry(self):
        registry = WorkerRegistry()
        registry.register_mock_worker(
            worker_id="arc-it-helper-01",
            tenant_id="tenant-lab-001",
            role="it_helper_arc_worker",
            capabilities=["it_diagnostics_read_only"],
        )
        return registry

    def bound_decision(self, task):
        decision = guardian_allow_decision()
        decision["decision_id"] = task["guardian_decision_id"]
        decision["tenant_id"] = task["tenant_id"]
        decision["customer_context_id"] = task["customer_context_id"]
        decision["subject"] = {"subject_type": "task", "subject_id": task["task_id"]}
        return decision

    def test_supervisor_health_reports_healthy_and_validates(self):
        registry = self.make_registry()
        registry.update_state("arc-it-helper-01", "healthy", "test")
        writer = EvidenceWriter(self.validator)
        queue = TaskQueue(registry, self.validator, evidence_writer=writer)
        task = task_example()
        task["status"] = "in_progress"
        decision = self.bound_decision(task)
        queue.enqueue(task, decision)
        artifact = writer.write_artifact(
            artifact_type="task_transition",
            subject_id=task["task_id"],
            action="read_only_diagnostic",
            guardian_decision_id=decision["decision_id"],
        )
        queue.complete_mock(task["task_id"], [artifact["artifact_id"]])

        health = SupervisorHealthReporter(self.validator).build(
            registry=registry,
            task_queue=queue,
            evidence_writer=writer,
        )

        self.assertEqual("supervisor.health", health["contract_name"])
        self.assertEqual("healthy", health["health_status"])
        self.assertEqual(0, health["denied_action_count"])
        self.validator.validate(health, "supervisor.health")

    def test_supervisor_health_reports_degraded_for_stale_heartbeat(self):
        registry = self.make_registry()
        registry.get("arc-it-helper-01").heartbeat = {"heartbeat_age_seconds": 999}
        writer = EvidenceWriter(self.validator)

        health = SupervisorHealthReporter(self.validator).build(
            registry=registry,
            evidence_writer=writer,
        )

        self.assertEqual("degraded", health["health_status"])
        self.assertIn("worker_stale", health["reasons"])
        self.validator.validate(health, "supervisor.health")

    def test_supervisor_health_reports_blocked_for_denied_guardian_decision(self):
        registry = self.make_registry()
        denied = GuardianPolicy().decide("remediation")

        health = SupervisorHealthReporter(self.validator).build(
            registry=registry,
            guardian_decisions=[denied],
        )

        self.assertEqual("blocked", health["health_status"])
        self.assertIn("guardian_denied", health["reasons"])
        self.validator.validate(health, "supervisor.health")

    def test_supervisor_health_omits_raw_customer_content_and_secrets(self):
        registry = self.make_registry()
        health = SupervisorHealthReporter(self.validator).build(registry=registry)
        encoded = repr(health)

        self.assertFalse(health["raw_customer_content_present"])
        self.assertFalse(health["secret_material_present"])
        self.assertNotIn("customer email body", encoded.lower())
        self.assertNotIn("api_key", encoded.lower())
        self.assertNotIn("password", encoded.lower())


if __name__ == "__main__":
    unittest.main()
