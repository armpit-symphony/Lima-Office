"""Support controls must preserve SOPs/evidence and export no free text."""
from io import BytesIO
import json
import zipfile

import pytest

from lima_office.runtime.lab_support import diagnostic_bundle, support_action
from lima_office.runtime.operator_harness import HarnessBoundaryError
from lima_office.runtime.operator_ide import OperatorIDEHarness, OperatorIDEStateStore
from test_operator_ide import FakeArcIDE, FakeSession


@pytest.fixture
def harness(tmp_path):
    store = OperatorIDEStateStore(tmp_path / "state.db")
    h = OperatorIDEHarness(FakeSession(tmp_path), store, arc_ide=FakeArcIDE())
    yield h
    store.close()


def test_reset_archives_and_survives_restart(harness):
    h = harness
    h.teach(task_ref="private-name", instruction="PRIVATE SOP TEXT", authored_by_role="private-operator")
    result = h.run_registration_practice_suite()
    attempt = result["results"][0]
    h.review_registration_practice(attempt_id=attempt["attempt_id"], decision="rejected")
    before = h.store._connection.execute("SELECT COUNT(*) FROM harness_events").fetchone()[0]
    with pytest.raises(HarnessBoundaryError):
        support_action(h, "synthetic_history_reset")
    assert h.store.registration_summary()["attempt_count"] == 25
    reset = support_action(h, "synthetic_history_reset", confirmed=True)
    assert reset["sops_preserved"] and reset["audit_preserved"]
    assert h.store.registration_summary()["attempt_count"] == 0
    assert h.store.registration_review_summary()["review_count"] == 0
    assert h.store._connection.execute("SELECT COUNT(*) FROM registration_practice_attempts_archive").fetchone()[0] == 25
    assert h.store._connection.execute("SELECT COUNT(*) FROM harness_events").fetchone()[0] > before
    with pytest.raises(HarnessBoundaryError):
        h.review_registration_practice(attempt_id=attempt["attempt_id"], decision="approved")
    reopened = OperatorIDEStateStore(h.store.path)
    try:
        assert reopened.gaps()[0].instruction == "PRIVATE SOP TEXT"
        assert reopened.registration_summary()["attempt_count"] == 0
    finally:
        reopened.close()


def test_export_excludes_raw_text(harness):
    harness.teach(task_ref="PRIVATE_TASK", instruction="PRIVATE_SOP", authored_by_role="PRIVATE_ROLE")
    harness.store.record_event("sample_event", {"token": "SECRET_TOKEN", "content": "PRIVATE_CONTENT"})
    harness.run_registration_practice_suite()
    data = diagnostic_bundle(harness, {"version": "test", "arc_commit": "a" * 40})
    with zipfile.ZipFile(BytesIO(data)) as bundle:
        assert set(bundle.namelist()) == {"diagnostics.json", "evidence-index.json"}
        decoded = " ".join(bundle.read(name).decode() for name in bundle.namelist())
        for forbidden in ("PRIVATE_TASK", "PRIVATE_SOP", "PRIVATE_ROLE", "PRIVATE_CONTENT", "SECRET_TOKEN", "@example.test"):
            assert forbidden not in decoded
        diagnostics = json.loads(bundle.read("diagnostics.json"))
        assert diagnostics["registration"]["attempt_count"] == 25
        assert diagnostics["authorization"]["guardian_decision_id"]


def test_support_denies_working_mode_and_unknown_operation(harness):
    with pytest.raises(HarnessBoundaryError):
        support_action(harness, "delete_all", confirmed=True)
    harness.set_mode("working")
    with pytest.raises(HarnessBoundaryError):
        diagnostic_bundle(harness, {})


def test_reset_transaction_rolls_back_on_archive_failure(harness):
    harness.run_registration_practice_suite()
    db = harness.store._connection
    db.execute("CREATE TABLE registration_practice_attempts_archive (incompatible TEXT)")
    db.commit()
    with pytest.raises(Exception):
        support_action(harness, "synthetic_history_reset", confirmed=True)
    assert harness.store.registration_summary()["attempt_count"] == 25
