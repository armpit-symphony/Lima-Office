import unittest

from helpers import has_jsonschema, validator
from lima_office.evidence import EvidenceWriter
from lima_office.runtime.errors import EvidenceRequiredError, EvidenceWriteError


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class EvidenceWriterTests(unittest.TestCase):
    def setUp(self):
        self.writer = EvidenceWriter(validator())

    def test_writes_metadata_only_artifact(self):
        artifact = self.writer.write_artifact(
            artifact_type="task_transition",
            subject_id="task-it-health-001",
            action="read_only_diagnostic",
            guardian_decision_id="gd-it-health-001",
        )
        self.assertEqual("evidence.artifact", artifact["contract_name"])
        self.assertFalse(artifact["storage_ref"]["secret_material_present"])
        self.writer.require_evidence([artifact["artifact_id"]])

    def test_missing_evidence_ref_fails_closed(self):
        with self.assertRaises(EvidenceRequiredError):
            self.writer.require_evidence([])

    def test_action_evidence_requires_guardian_link(self):
        with self.assertRaises(EvidenceWriteError):
            self.writer.write_artifact(
                artifact_type="task_transition",
                subject_id="task-it-health-001",
                action="read_only_diagnostic",
                guardian_decision_id=None,
            )

    def test_summary_rejects_secret_like_content(self):
        with self.assertRaises(EvidenceWriteError):
            self.writer.write_artifact(
                artifact_type="task_transition",
                subject_id="task-it-health-001",
                action="read_only_diagnostic",
                guardian_decision_id="gd-it-health-001",
                summary="api_key: should-not-appear",
            )

    def test_write_failure_blocks_pre_action_path(self):
        writer = EvidenceWriter(validator(), fail_writes=True)
        with self.assertRaises(EvidenceWriteError):
            writer.write_artifact(
                artifact_type="task_transition",
                subject_id="task-it-health-001",
                action="read_only_diagnostic",
                guardian_decision_id="gd-it-health-001",
            )
        self.assertEqual(1, len(writer.failures))
        failure = next(iter(writer.failures.values()))
        self.assertTrue(failure["pre_action_blocked"])
        self.assertTrue(failure["action_blocked"])


if __name__ == "__main__":
    unittest.main()
