"""Bounded operator support for the Arc lab; no customer or connector access."""

from __future__ import annotations

from io import BytesIO
import json
import uuid
from typing import Any
import zipfile

from lima_office.guardian.policy import GuardianPolicy
from lima_office.runtime.operator_harness import HarnessBoundaryError, _utc_now


def support_action(harness: Any, operation: str, *, confirmed: bool = False) -> dict:
    if operation not in {"diagnostic_export", "synthetic_history_reset", "service_stop"}:
        raise HarnessBoundaryError("unknown lab support operation")
    with harness._lock, harness.store._lock:
        if harness.mode != "training" and operation != "service_stop":
            raise HarnessBoundaryError("lab support requires training mode")
        requested = harness.store.record_event("lab_support_requested", {"operation": operation})
        decision = GuardianPolicy().decide("lab_support", {
            "tenant_id": str(harness.session.args.tenant_id),
            "customer_context_id": "customer-context-main",
            "execution_mode": "mock_only", "external_effect": "none",
            "evidence_required": True, "evidence_artifact_ids": [requested],
            "operation": operation, "confirmed": confirmed,
            "scope": "synthetic_registration_history", "preserve_sops": True,
        })
        ref = harness.store.record_event("lab_support_decision", {
            "operation": operation, "decision": decision["decision"],
            "guardian_decision_id": decision["decision_id"], "request_ref": requested,
        })
        if decision["decision"] != "allow_with_evidence":
            raise HarnessBoundaryError("Guardian denied lab support operation")
        if operation == "synthetic_history_reset":
            # Archive and clear active practice rows atomically. Preserve SOPs,
            # work queues, unrelated metrics and the append-only audit trail.
            connection = harness.store._connection
            counts = {}
            with connection:
                for table in ("registration_mock_reviews", "registration_practice_attempts"):
                    archive = table + "_archive"
                    connection.execute(f"CREATE TABLE IF NOT EXISTS {archive} AS SELECT * FROM {table} WHERE 0")
                    counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    connection.execute(f"INSERT INTO {archive} SELECT * FROM {table}")
                    connection.execute(f"DELETE FROM {table}")
                event_id = "harness-event:" + uuid.uuid4().hex
                connection.execute("INSERT INTO harness_events VALUES (?, ?, ?, ?)", (
                    event_id, _utc_now(), "synthetic_history_reset_completed",
                    json.dumps({"counts": counts, "decision_ref": ref, "sops_preserved": True}),
                ))
            return {"status": "reset", "archived_counts": counts,
                    "sops_preserved": True, "audit_preserved": True,
                    "evidence_ref": event_id, "guardian_decision_id": decision["decision_id"]}
        return {"status": "allowed", "evidence_ref": ref,
                "guardian_decision_id": decision["decision_id"]}


def diagnostic_bundle(harness: Any, build: dict) -> bytes:
    with harness._lock, harness.store._lock:
        authorization = support_action(harness, "diagnostic_export")
        state = harness.state()
        # Allowlist only: no DB files, paths, credentials, prompts, SOP bodies,
        # operator text, document content, or free-text event payloads.
        diagnostics = {
            "schema_version": "arc-lab-diagnostics-v1", "build": build,
            "mode": state["mode"], "loopback_only": True,
            "registration": harness.store.registration_summary(),
            "reviews": harness.store.registration_review_summary(),
            "sop_count": len(harness.store.gaps()),
            "model_configured": state.get("local_model", {}).get("configured", False),
            "model_ready": state.get("local_model", {}).get("ready", False),
            "external_side_effects": False, "authorization": authorization,
            "redaction": "Event payloads and all free-text content omitted; local metadata only.",
        }
        events = [dict(row) for row in harness.store._connection.execute(
            "SELECT event_id, occurred_at, event_type FROM harness_events ORDER BY rowid"
        ).fetchall()]
        output = BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("diagnostics.json", json.dumps(diagnostics, indent=2))
            bundle.writestr("evidence-index.json", json.dumps(events, indent=2))
        return output.getvalue()
