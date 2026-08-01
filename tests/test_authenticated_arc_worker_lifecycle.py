"""Authenticated Arc worker registration, heartbeat, and durability tests."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest import mock

from helpers import example
from lima_office.contracts import ContractLoader, ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.runtime.errors import (
    WorkerChannelAuthenticationError,
    WorkerEndpointUnavailableError,
    WorkerStateError,
)
from lima_office.supervisor import (
    AuthenticatedArcWorkerClient,
    AuthenticatedWorkerLifecycleService,
    WorkerChannel,
    WorkerRegistry,
)


FIXED_TIME = datetime(2026, 7, 25, 5, 0, tzinfo=timezone.utc)
SHARED_KEY = bytes.fromhex("11" * 32)


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.headers = {"Content-Length": str(len(self._encoded))}

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int) -> bytes:
        return self._encoded[:size]


class AuthenticatedArcWorkerLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.validator = ContractValidator(ContractLoader().load())
        self.supervisor_store = SQLiteEvidenceStore(
            self.root / "supervisor.db",
            self.validator,
        )
        self.worker_store = SQLiteEvidenceStore(
            self.root / "worker-channel.db",
            self.validator,
        )
        self.addCleanup(self.worker_store.close)
        self.addCleanup(self.supervisor_store.close)
        channel_args: dict[str, Any] = {
            "tenant_id": "tenant-lab-001",
            "customer_context_id": "customer-context-main",
            "worker_id": "arc-worker-001",
            "key_id": "lab-key-001",
            "shared_key": SHARED_KEY,
            "validator": self.validator,
            "policy_version": "policy-phase0-v1",
            "clock": lambda: FIXED_TIME,
        }
        self.supervisor_channel = WorkerChannel(
            **channel_args,
            evidence_store=self.supervisor_store,
        )
        self.worker_channel = WorkerChannel(
            **channel_args,
            evidence_store=self.worker_store,
        )
        self.registry = WorkerRegistry()
        self.lifecycle = AuthenticatedWorkerLifecycleService(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            policy_version="policy-phase0-v1",
            validator=self.validator,
            registry=self.registry,
            evidence_store=self.supervisor_store,
            clock=lambda: FIXED_TIME,
        )
        self.client = AuthenticatedArcWorkerClient(
            base_url="http://127.0.0.1:8765",
            channel=self.supervisor_channel,
            validator=self.validator,
        )
        self.heartbeat_sequence = 0
        self.heartbeat_reported_at = "2026-07-25T05:00:00Z"

    def _urlopen(self, request: Any, timeout: float) -> _Response:
        self.assertEqual(timeout, 2.0)
        body = json.loads(request.data)
        path = request.full_url.rsplit("/", 1)[-1]
        request_types = {
            "registration": "registration_challenge",
            "heartbeat": "heartbeat_challenge",
        }
        response_types = {
            "registration": "registration",
            "heartbeat": "heartbeat",
        }
        self.worker_channel.verify(
            body["envelope"],
            body["payload"],
            expected_message_type=request_types[path],
            expected_sender_component="supervisor",
        )
        if path == "registration":
            payload = self._registration()
        else:
            payload = self._heartbeat()
        envelope = self.worker_channel.sign(
            payload,
            message_type=response_types[path],
            sender_component="worker",
        )
        return _Response({"envelope": envelope, "payload": payload})

    def _registration(self) -> dict[str, Any]:
        payload = example("worker.registration.example.json")
        return copy.deepcopy(payload)

    def _heartbeat(self) -> dict[str, Any]:
        self.heartbeat_sequence += 1
        payload = example("worker.heartbeat.example.json")
        payload["worker_id"] = "arc-worker-001"
        payload["boot_id"] = "boot-lab-001"
        payload["heartbeat_sequence"] = self.heartbeat_sequence
        payload["heartbeat_id"] = f"heartbeat:arc-worker-001:{self.heartbeat_sequence}"
        payload["idempotency_key"] = (
            f"heartbeat:arc-worker-001:{self.heartbeat_sequence}"
        )
        payload["guardian_decision_id"] = "guardian:not_invoked_for_heartbeat"
        payload["producer"]["produced_at"] = "2026-07-25T05:00:00Z"
        payload["reported_at"] = self.heartbeat_reported_at
        payload["supervisor_received_at"] = "2026-07-25T04:59:00Z"
        payload["heartbeat_due_at"] = "2026-07-25T05:01:00Z"
        payload["heartbeat_age_seconds"] = 999
        return payload

    def test_registration_heartbeat_and_restart_restore_are_durable(self) -> None:
        with mock.patch(
            "lima_office.supervisor.worker_client.urllib_request.urlopen",
            side_effect=self._urlopen,
        ):
            registered = self.lifecycle.register(self.client)
            heartbeat = self.lifecycle.heartbeat(self.client)

        self.assertTrue(registered.authenticated)
        self.assertEqual("lab-key-001", registered.channel_identity_ref)
        self.assertEqual("healthy", heartbeat.state)
        self.assertEqual(1, heartbeat.last_heartbeat_sequence)
        self.assertEqual("2026-07-25T05:00:00Z", heartbeat.last_heartbeat_at)
        self.assertEqual(0, heartbeat.heartbeat["heartbeat_age_seconds"])
        self.assertEqual(
            "2026-07-25T05:00:00Z",
            heartbeat.heartbeat["supervisor_received_at"],
        )
        self.assertEqual(
            ["worker_registration"],
            [
                event["event_type"]
                for event in self.supervisor_store.events_for_request(
                    "registration:arc-worker-001:boot-lab-001",
                    "tenant-lab-001",
                )
            ],
        )
        self.assertEqual(
            ["worker_heartbeat"],
            [
                event["event_type"]
                for event in self.supervisor_store.events_for_request(
                    "heartbeat:arc-worker-001:1",
                    "tenant-lab-001",
                )
            ],
        )

        restored_registry = WorkerRegistry()
        restored_service = AuthenticatedWorkerLifecycleService(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            policy_version="policy-phase0-v1",
            validator=self.validator,
            registry=restored_registry,
            evidence_store=self.supervisor_store,
            clock=lambda: FIXED_TIME,
        )
        restored = restored_service.restore()

        self.assertEqual(1, len(restored))
        self.assertEqual("arc-worker-001", restored[0].worker_id)
        self.assertEqual("healthy", restored[0].state)
        self.assertTrue(restored[0].authenticated)
        self.assertEqual(1, restored[0].last_heartbeat_sequence)
        self.assertEqual(
            "2026-07-25T05:00:00Z",
            restored[0].last_heartbeat_at,
        )

    def test_stale_heartbeat_state_and_evidence_are_persisted(self) -> None:
        with mock.patch(
            "lima_office.supervisor.worker_client.urllib_request.urlopen",
            side_effect=self._urlopen,
        ):
            self.lifecycle.register(self.client)
            self.heartbeat_reported_at = "2026-07-25T04:56:59Z"
            with self.assertRaisesRegex(
                WorkerStateError,
                "stale heartbeat",
            ):
                self.lifecycle.heartbeat(self.client)

        record = self.registry.get("arc-worker-001")
        self.assertEqual("offline", record.state)
        persisted = self.supervisor_store.worker_records(
            "tenant-lab-001"
        )
        self.assertEqual("offline", persisted[0]["state"])
        events = self.supervisor_store.events_for_request(
            "heartbeat:arc-worker-001:1",
            "tenant-lab-001",
        )
        self.assertEqual("blocked", events[-1]["outcome"])
        self.assertEqual(["worker_stale"], events[-1]["reason_codes"])

    def test_authenticated_response_replay_is_rejected_durably(self) -> None:
        payload = self._registration()
        envelope = self.worker_channel.sign(
            payload,
            message_type="registration",
            sender_component="worker",
            message_id="message-replay-001",
            nonce="nonce-replay-0001",
        )

        self.supervisor_channel.verify(
            envelope,
            payload,
            expected_message_type="registration",
            expected_sender_component="worker",
        )
        with self.assertRaises(WorkerChannelAuthenticationError):
            self.supervisor_channel.verify(
                envelope,
                payload,
                expected_message_type="registration",
                expected_sender_component="worker",
            )

    def test_tampered_registration_fails_before_registry_or_evidence(self) -> None:
        payload = self._registration()
        envelope = self.worker_channel.sign(
            payload,
            message_type="registration",
            sender_component="worker",
        )
        payload["tenant_id"] = "tenant-other"

        with self.assertRaises(WorkerChannelAuthenticationError):
            self.supervisor_channel.verify(
                envelope,
                payload,
                expected_message_type="registration",
                expected_sender_component="worker",
            )
        self.assertEqual(0, self.registry.summary()["worker_count"])
        self.assertEqual([], self.supervisor_store.worker_records("tenant-lab-001"))

    def test_non_loopback_worker_addresses_are_rejected(self) -> None:
        for base_url in (
            "http://8.8.8.8:8765",
            "http://192.168.1.8:8765",
        ):
            with self.subTest(base_url=base_url), self.assertRaises(
                WorkerChannelAuthenticationError
            ):
                AuthenticatedArcWorkerClient(
                    base_url=base_url,
                    channel=self.supervisor_channel,
                    validator=self.validator,
                )

    def test_worker_timeout_has_a_distinct_fail_closed_error(self) -> None:
        with mock.patch(
            "lima_office.supervisor.worker_client.urllib_request.urlopen",
            side_effect=TimeoutError("private timeout detail"),
        ), self.assertRaises(WorkerEndpointUnavailableError) as caught:
            self.client.request_heartbeat()

        self.assertEqual(
            "Arc worker endpoint is unavailable",
            str(caught.exception),
        )
        self.assertNotIn("private timeout detail", str(caught.exception))

    def test_heartbeat_identity_and_future_time_fail_closed(self) -> None:
        wrong_customer = self._heartbeat()
        wrong_customer["customer_context_id"] = "customer-context-other"
        with self.assertRaises(WorkerStateError):
            self.lifecycle._normalize_heartbeat(wrong_customer)

        future = self._heartbeat()
        future["reported_at"] = "2026-07-25T05:00:01Z"
        with self.assertRaises(WorkerStateError):
            self.lifecycle._normalize_heartbeat(future)

    def test_channel_keys_are_not_persisted_in_worker_records(self) -> None:
        with mock.patch(
            "lima_office.supervisor.worker_client.urllib_request.urlopen",
            side_effect=self._urlopen,
        ):
            self.lifecycle.register(self.client)

        serialized = json.dumps(
            self.supervisor_store.worker_records("tenant-lab-001"),
            sort_keys=True,
        )
        self.assertNotIn(SHARED_KEY.hex(), serialized)
        self.assertNotIn("shared_key", serialized)
        self.assertIn("lab-key-001", serialized)


if __name__ == "__main__":
    unittest.main()
