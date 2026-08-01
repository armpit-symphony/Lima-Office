"""Authenticated foreground operator-to-Supervisor boundary tests."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
from typing import Any
import unittest
from urllib import error as urllib_error
from urllib import request as urllib_request

from lima_office.contracts import ContractLoader, ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.runtime.errors import OperatorChannelAuthenticationError
from lima_office.supervisor.operator_channel import OperatorChannel
from lima_office.supervisor.operator_service import (
    OperatorControlPlaneService,
    build_supervisor_operator_server,
)


NOW = "2026-07-26T01:00:00Z"


class _FakeControlPlane:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def submit(self, request: dict[str, Any]) -> dict[str, Any]:
        self.requests.append(dict(request))
        return {
            "request_id": request["request_id"],
            "tenant_id": request["tenant_id"],
            "actor_id": request["actor_id"],
            "worker_id": request["worker_id"],
            "status": "acknowledged",
            "classification_authority": "supervisor_server_derived",
            "action_category": "informational",
            "guardian": {
                "decision_id": "guardian-decision-001",
                "decision": "allow_with_evidence",
                "approval_required": False,
                "policy_version": "guardian-policy-lab-v1",
                "policy_snapshot_hash": "sha256:" + "1" * 64,
                "request_binding": "sha256:" + "2" * 64,
                "expires_at": "2026-07-26T01:05:00Z",
            },
            "lima": {
                "decision_id": "lima-decision-001",
                "status": "allowed_dry_run",
                "allowed": True,
                "requires_approval": False,
                "risk_level": "low",
                "reason_codes": [],
                "source_policy": "guardian_core.policy",
                "executable": False,
                "execution_allowed": False,
                "side_effects_allowed": False,
            },
            "assignment": {
                "assignment_id": "assignment-001",
                "status": "acknowledged",
            },
            "reason_codes": [],
            "evidence": [
                {
                    "event_id": "event-001",
                    "event_type": "request_received",
                    "outcome": "received",
                    "reason_codes": [],
                    "created_at": NOW,
                }
            ],
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }


def _request() -> dict[str, Any]:
    return {
        "contract_name": "operator.control_plane.request",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "taxonomy_version": "taxonomy-recon-v1",
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "environment": "phase0_lab",
        "correlation_id": "corr:operator-request-001",
        "causation_id": None,
        "idempotency_key": "idem-operator-request-001",
        "producer": {"component": "operator_client", "produced_at": NOW},
        "policy_version": "guardian-policy-lab-v1",
        "request_id": "operator-request-001",
        "actor_id": "operator-lab-001",
        "action": "safe_read",
        "resource_type": "worker_status",
        "resource_id": "arc-worker-001",
        "worker_id": "arc-worker-001",
        "runtime_authority_blocked": True,
        "executable": False,
        "execution_allowed": False,
        "side_effects_allowed": False,
    }


def _body(channel: OperatorChannel, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "envelope": channel.sign(
            payload,
            message_type="operator_request",
            sender_component="operator_client",
        ),
        "payload": payload,
    }


class SupervisorOperatorBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.validator = ContractValidator(ContractLoader().load())
        self.store = SQLiteEvidenceStore(
            Path(self.temporary.name) / "evidence.db",
            self.validator,
        )
        self.channel = OperatorChannel(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            actor_id="operator-lab-001",
            key_id="operator-key-001",
            shared_key=b"o" * 32,
            validator=self.validator,
            evidence_store=self.store,
            clock=lambda: datetime(2026, 7, 26, 1, 0, tzinfo=timezone.utc),
        )
        self.control_plane = _FakeControlPlane()
        self.service = OperatorControlPlaneService(
            channel=self.channel,
            validator=self.validator,
            control_plane=self.control_plane,  # type: ignore[arg-type]
        )

    def tearDown(self) -> None:
        self.store.close()
        self.temporary.cleanup()

    def test_authenticated_request_injects_bound_identity_and_returns_evidence(
        self,
    ) -> None:
        response = self.service.handle(_body(self.channel, _request()))
        payload = response["payload"]
        self.channel.verify(
            response["envelope"],
            payload,
            expected_message_type="operator_response",
            expected_sender_component="supervisor",
        )
        self.assertEqual(
            self.control_plane.requests,
            [
                {
                    "request_id": "operator-request-001",
                    "tenant_id": "tenant-lab-001",
                    "actor_id": "operator-lab-001",
                    "action": "safe_read",
                    "resource_type": "worker_status",
                    "resource_id": "arc-worker-001",
                    "worker_id": "arc-worker-001",
                    "idempotency_key": "idem-operator-request-001",
                }
            ],
        )
        self.assertEqual(
            payload["classification_authority"],
            "supervisor_server_derived",
        )
        self.assertEqual(payload["status"], "acknowledged")
        self.assertEqual(
            payload["evidence"][0]["event_type"],
            "request_received",
        )
        self.assertTrue(payload["runtime_authority_blocked"])
        self.assertFalse(payload["executable"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["side_effects_allowed"])

    def test_actor_and_signature_mismatches_fail_closed(self) -> None:
        payload = _request()
        payload["actor_id"] = "operator-other"
        with self.assertRaises(OperatorChannelAuthenticationError):
            self.service.handle(_body(self.channel, payload))

        payload = _request()
        body = _body(self.channel, payload)
        body["envelope"]["signature"] = "0" * 64
        with self.assertRaises(OperatorChannelAuthenticationError):
            self.service.handle(body)
        self.assertEqual(self.control_plane.requests, [])

    def test_replayed_operator_envelope_is_rejected_before_control_plane(
        self,
    ) -> None:
        body = _body(self.channel, _request())
        self.service.handle(body)
        with self.assertRaises(OperatorChannelAuthenticationError):
            self.service.handle(body)
        self.assertEqual(len(self.control_plane.requests), 1)

    def test_client_cannot_supply_classification_or_execution_authority(
        self,
    ) -> None:
        payload = _request()
        payload["action_category"] = "informational"
        with self.assertRaises(Exception):
            self.service.handle(_body(self.channel, payload))

        payload = _request()
        payload["execution_allowed"] = True
        with self.assertRaises(Exception):
            self.service.handle(_body(self.channel, payload))
        self.assertEqual(self.control_plane.requests, [])

    def test_supervisor_server_rejects_non_loopback_bind(self) -> None:
        with self.assertRaisesRegex(
            OperatorChannelAuthenticationError,
            "loopback-only",
        ):
            build_supervisor_operator_server(
                host="0.0.0.0",
                port=0,
                service=self.service,
            )

    def test_http_authentication_failure_is_publicly_redacted(self) -> None:
        server = build_supervisor_operator_server(
            host="127.0.0.1",
            port=0,
            service=self.service,
        )
        payload = _request()
        request_body = _body(self.channel, payload)
        request_body["envelope"]["signature"] = "0" * 64
        encoded = json.dumps(request_body).encode("utf-8")
        request = urllib_request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/operator/preflight",
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            with self.assertRaises(urllib_error.HTTPError) as caught:
                urllib_request.urlopen(request, timeout=2)
            response_body = json.loads(caught.exception.read())
            thread.join(timeout=2)
        finally:
            server.server_close()

        self.assertEqual(
            response_body,
            {
                "status": "authentication_failed",
                "runtime_authority_blocked": True,
                "executable": False,
                "execution_allowed": False,
                "side_effects_allowed": False,
            },
        )
        self.assertNotIn("signature", json.dumps(response_body))
        self.assertEqual(self.control_plane.requests, [])

    def test_legacy_action_hash_uniqueness_migrates_without_losing_history(
        self,
    ) -> None:
        path = Path(self.temporary.name) / "legacy.db"
        connection = sqlite3.connect(path)
        connection.executescript(
            """
            CREATE TABLE control_plane_requests (
                request_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (tenant_id, idempotency_key),
                UNIQUE (tenant_id, request_hash)
            );
            INSERT INTO control_plane_requests VALUES (
                'request-legacy-001',
                'tenant-lab-001',
                'idem-legacy-001',
                'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                '2026-07-26T01:00:00Z'
            );
            """
        )
        connection.close()

        migrated = SQLiteEvidenceStore(path, self.validator)
        migrated.close()
        reopened = sqlite3.connect(path)
        try:
            rows = reopened.execute(
                "SELECT request_id FROM control_plane_requests ORDER BY request_id"
            ).fetchall()
            reopened.execute(
                "INSERT INTO control_plane_requests VALUES (?, ?, ?, ?, ?, ?)",
                (
                    "request-fresh-002",
                    "tenant-lab-001",
                    "idem-fresh-002",
                    "sha256:" + "a" * 64,
                    "sha256:" + "c" * 64,
                    "2026-07-26T01:01:00Z",
                ),
            )
            reopened.commit()
        finally:
            reopened.close()
        self.assertEqual(rows, [("request-legacy-001",)])


if __name__ == "__main__":
    unittest.main()
