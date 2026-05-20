import unittest

from lima_office.runtime.errors import WorkerStateError
from lima_office.supervisor import WorkerRegistry


class WorkerRegistryTests(unittest.TestCase):
    def test_registers_mock_worker(self):
        registry = WorkerRegistry()
        worker = registry.register_mock_worker(
            worker_id="arc-file-clerk-01",
            tenant_id="tenant-lab-001",
            role="file_clerk_arc_worker",
            capabilities=["document_read", "file_organize"],
        )
        self.assertEqual("registered", worker.state)

    def test_rejects_more_than_eight_workers_config(self):
        with self.assertRaises(WorkerStateError):
            WorkerRegistry(max_workers=9)

    def test_rejects_second_tenant(self):
        registry = WorkerRegistry()
        registry.register_mock_worker(
            worker_id="arc-1",
            tenant_id="tenant-a",
            role="general_office_arc_worker",
            capabilities=["document_read"],
        )
        with self.assertRaises(WorkerStateError):
            registry.register_mock_worker(
                worker_id="arc-2",
                tenant_id="tenant-b",
                role="general_office_arc_worker",
                capabilities=["document_read"],
            )

    def test_rejects_unknown_capability(self):
        with self.assertRaises(WorkerStateError):
            WorkerRegistry().register_mock_worker(
                worker_id="arc-1",
                tenant_id="tenant-lab-001",
                role="general_office_arc_worker",
                capabilities=["unrestricted_network"],
            )

    def test_quarantined_and_revoked_workers_not_assignable(self):
        registry = WorkerRegistry()
        registry.register_mock_worker(
            worker_id="arc-1",
            tenant_id="tenant-lab-001",
            role="general_office_arc_worker",
            capabilities=["document_read"],
        )
        registry.quarantine("arc-1", "test")
        with self.assertRaises(WorkerStateError):
            registry.require_assignable("arc-1", "tenant-lab-001")

    def test_terminal_state_cannot_reactivate(self):
        registry = WorkerRegistry()
        registry.register_mock_worker(
            worker_id="arc-1",
            tenant_id="tenant-lab-001",
            role="general_office_arc_worker",
            capabilities=["document_read"],
        )
        registry.quarantine("arc-1", "test")
        with self.assertRaises(WorkerStateError):
            registry.update_state("arc-1", "healthy", "not_allowed")
        registry.revoke("arc-1", "test")
        with self.assertRaises(WorkerStateError):
            registry.require_assignable("arc-1", "tenant-lab-001")


if __name__ == "__main__":
    unittest.main()
