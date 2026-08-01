import unittest

from helpers import has_jsonschema, heartbeat_example, validator
from lima_office.runtime.errors import WorkerStateError
from lima_office.supervisor import HeartbeatService, WorkerRegistry


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class HeartbeatTests(unittest.TestCase):
    def setUp(self):
        self.registry = WorkerRegistry()
        self.registry.register_mock_worker(
            worker_id="arc-file-clerk-01",
            tenant_id="tenant-lab-001",
            role="file_clerk_arc_worker",
            capabilities=["document_read", "file_organize"],
        )
        self.service = HeartbeatService(self.registry, validator())

    def test_accepts_valid_heartbeat(self):
        heartbeat = self.service.accept(heartbeat_example())
        self.assertEqual("worker.heartbeat", heartbeat["contract_name"])
        self.assertEqual("healthy", self.registry.get("arc-file-clerk-01").state)

    def test_unknown_worker_heartbeat_denied(self):
        payload = heartbeat_example()
        payload["worker_id"] = "arc-unknown"
        with self.assertRaises(WorkerStateError):
            self.service.accept(payload)

    def test_wrong_tenant_heartbeat_denied(self):
        payload = heartbeat_example()
        payload["tenant_id"] = "tenant-other"
        with self.assertRaises(WorkerStateError):
            self.service.accept(payload)

    def test_stale_heartbeat_blocks_assignment(self):
        payload = heartbeat_example()
        payload["heartbeat_age_seconds"] = 999
        with self.assertRaises(WorkerStateError):
            self.service.accept(payload)
        with self.assertRaises(WorkerStateError):
            self.registry.require_assignable("arc-file-clerk-01", "tenant-lab-001")

    def test_evidence_writer_failure_quarantines_worker(self):
        payload = heartbeat_example()
        payload["evidence_writer_status"] = "failed"
        payload["health_state"] = "quarantined"
        payload["lifecycle_state"] = "quarantined"
        payload["quarantine_reason"] = "evidence_writer_failed"
        payload["risk_tier"] = "blocked"
        payload["last_evidence_error_code"] = "ledger_unavailable"
        payload["operator_action_required"] = True
        payload["evidence_failure_id"] = "ef-heartbeat-evidence-failed-001"
        payload["runbook_ref"] = "docs/runbooks/evidence-writer-failure.md"
        with self.assertRaises(WorkerStateError):
            self.service.accept(payload)
        self.assertEqual("quarantined", self.registry.get("arc-file-clerk-01").state)

    def test_guardian_unreachable_quarantines_worker(self):
        payload = heartbeat_example()
        payload["guardian_reachability"] = "unreachable"
        payload["health_state"] = "degraded"
        payload["missed_heartbeat_count"] = 1
        with self.assertRaises(WorkerStateError):
            self.service.accept(payload)
        self.assertEqual("quarantined", self.registry.get("arc-file-clerk-01").state)


if __name__ == "__main__":
    unittest.main()
