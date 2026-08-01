"""Authenticated transport primitives for the lab Supervisor/Arc boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from typing import Any
from uuid import uuid4

from lima_office.contracts.validator import ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.runtime.errors import WorkerChannelAuthenticationError


MESSAGE_TYPES = {
    "registration_challenge",
    "registration",
    "heartbeat_challenge",
    "heartbeat",
    "assignment_preview",
    "assignment_acknowledgement",
}


def canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def payload_hash(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()


class WorkerChannel:
    """Sign and verify one worker's short-lived, metadata-only messages."""

    def __init__(
        self,
        *,
        tenant_id: str,
        customer_context_id: str,
        worker_id: str,
        key_id: str,
        shared_key: bytes,
        validator: ContractValidator,
        evidence_store: SQLiteEvidenceStore,
        policy_version: str = "policy-phase0-v1",
        clock: Callable[[], datetime] | None = None,
        ttl_seconds: int = 60,
    ) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (tenant_id, customer_context_id, worker_id, key_id)
        ):
            raise WorkerChannelAuthenticationError(
                "tenant, customer context, worker, and key identities are required"
            )
        if not isinstance(shared_key, bytes) or len(shared_key) < 32:
            raise WorkerChannelAuthenticationError(
                "lab channel key must contain at least 32 bytes"
            )
        if ttl_seconds < 1 or ttl_seconds > 120:
            raise WorkerChannelAuthenticationError(
                "channel message TTL must be between 1 and 120 seconds"
            )
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.worker_id = worker_id
        self.key_id = key_id
        self._shared_key = shared_key
        self.validator = validator
        self.evidence_store = evidence_store
        self.policy_version = policy_version
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.ttl_seconds = ttl_seconds

    def sign(
        self,
        payload: Mapping[str, Any],
        *,
        message_type: str,
        sender_component: str,
        message_id: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        if message_type not in MESSAGE_TYPES:
            raise WorkerChannelAuthenticationError(
                "unsupported channel message type"
            )
        if sender_component not in {"supervisor", "worker"}:
            raise WorkerChannelAuthenticationError("unsupported channel sender")
        issued_at = self._utc(self.clock())
        expires_at = self._utc(
            self.clock() + timedelta(seconds=self.ttl_seconds)
        )
        identity = message_id or f"msg:{uuid4().hex}"
        envelope = {
            "contract_name": "worker.channel.envelope",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{identity}",
            "causation_id": None,
            "idempotency_key": f"channel:{identity}",
            "producer": {
                "component": sender_component,
                "produced_at": issued_at,
            },
            "policy_version": self.policy_version,
            "message_id": identity,
            "worker_id": self.worker_id,
            "message_type": message_type,
            "key_id": self.key_id,
            "nonce": nonce or uuid4().hex,
            "payload_hash": payload_hash(payload),
            "signature_algorithm": "hmac-sha256",
            "issued_at": issued_at,
            "expires_at": expires_at,
        }
        envelope["signature"] = self._signature(envelope)
        return self.validator.validate(envelope, "worker.channel.envelope")

    def verify(
        self,
        envelope: Mapping[str, Any],
        payload: Mapping[str, Any],
        *,
        expected_message_type: str,
        expected_sender_component: str,
    ) -> dict[str, Any]:
        try:
            candidate = self.validator.validate(
                dict(envelope),
                "worker.channel.envelope",
            )
        except Exception as exc:
            raise WorkerChannelAuthenticationError(
                "worker channel envelope is invalid"
            ) from exc
        expected = {
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "worker_id": self.worker_id,
            "key_id": self.key_id,
            "message_type": expected_message_type,
        }
        if any(candidate.get(key) != value for key, value in expected.items()):
            raise WorkerChannelAuthenticationError(
                "worker channel identity or message binding mismatch"
            )
        if candidate["producer"]["component"] != expected_sender_component:
            raise WorkerChannelAuthenticationError(
                "worker channel sender binding mismatch"
            )
        if candidate["payload_hash"] != payload_hash(payload):
            raise WorkerChannelAuthenticationError(
                "worker channel payload hash mismatch"
            )

        issued = self._parse_time(candidate["issued_at"])
        expires = self._parse_time(candidate["expires_at"])
        now = self.clock().astimezone(timezone.utc)
        if expires <= now:
            raise WorkerChannelAuthenticationError("worker channel message expired")
        if issued > now + timedelta(seconds=5):
            raise WorkerChannelAuthenticationError(
                "worker channel message issued in the future"
            )
        if expires - issued > timedelta(seconds=120):
            raise WorkerChannelAuthenticationError(
                "worker channel message lifetime is too broad"
            )

        supplied = candidate["signature"]
        expected_signature = self._signature(candidate)
        if not hmac.compare_digest(supplied, expected_signature):
            raise WorkerChannelAuthenticationError(
                "worker channel signature mismatch"
            )
        try:
            self.evidence_store.reserve_channel_message(candidate)
        except Exception as exc:
            raise WorkerChannelAuthenticationError(
                "authenticated worker channel replay or evidence failure"
            ) from exc
        return candidate

    def _signature(self, envelope: Mapping[str, Any]) -> str:
        unsigned = {
            key: value for key, value in envelope.items() if key != "signature"
        }
        return hmac.new(
            self._shared_key,
            canonical_json(unsigned),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _utc(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_time(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except (TypeError, ValueError) as exc:
            raise WorkerChannelAuthenticationError(
                "worker channel timestamp is invalid"
            ) from exc
