"""Authenticated transport for the lab operator-to-Supervisor boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from typing import Any
from uuid import uuid4

from lima_office.contracts.validator import ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.runtime.errors import OperatorChannelAuthenticationError

from .worker_channel import canonical_json, payload_hash


MESSAGE_TYPES = {"operator_request", "operator_response"}


class OperatorChannel:
    """Sign and verify short-lived requests for one authenticated lab operator."""

    def __init__(
        self,
        *,
        tenant_id: str,
        customer_context_id: str,
        actor_id: str,
        key_id: str,
        shared_key: bytes,
        validator: ContractValidator,
        evidence_store: SQLiteEvidenceStore,
        policy_version: str = "guardian-policy-lab-v1",
        clock: Callable[[], datetime] | None = None,
        ttl_seconds: int = 60,
    ) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (tenant_id, customer_context_id, actor_id, key_id)
        ):
            raise OperatorChannelAuthenticationError(
                "tenant, customer context, actor, and key identities are required"
            )
        if not isinstance(shared_key, bytes) or len(shared_key) < 32:
            raise OperatorChannelAuthenticationError(
                "lab operator key must contain at least 32 bytes"
            )
        if ttl_seconds < 1 or ttl_seconds > 120:
            raise OperatorChannelAuthenticationError(
                "operator message TTL must be between 1 and 120 seconds"
            )
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.actor_id = actor_id
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
            raise OperatorChannelAuthenticationError(
                "unsupported operator message type"
            )
        if sender_component not in {"operator_client", "supervisor"}:
            raise OperatorChannelAuthenticationError(
                "unsupported operator channel sender"
            )
        issued_at = self._utc(self.clock())
        expires_at = self._utc(
            self.clock() + timedelta(seconds=self.ttl_seconds)
        )
        identity = message_id or f"operator-msg:{uuid4().hex}"
        envelope = {
            "contract_name": "operator.channel.envelope",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr:{identity}",
            "causation_id": None,
            "idempotency_key": f"operator-channel:{identity}",
            "producer": {
                "component": sender_component,
                "produced_at": issued_at,
            },
            "policy_version": self.policy_version,
            "message_id": identity,
            "actor_id": self.actor_id,
            "message_type": message_type,
            "key_id": self.key_id,
            "nonce": nonce or uuid4().hex,
            "payload_hash": payload_hash(payload),
            "signature_algorithm": "hmac-sha256",
            "issued_at": issued_at,
            "expires_at": expires_at,
        }
        envelope["signature"] = self._signature(envelope)
        return self.validator.validate(envelope, "operator.channel.envelope")

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
                "operator.channel.envelope",
            )
        except Exception as exc:
            raise OperatorChannelAuthenticationError(
                "operator channel envelope is invalid"
            ) from exc
        expected = {
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "actor_id": self.actor_id,
            "key_id": self.key_id,
            "message_type": expected_message_type,
            "policy_version": self.policy_version,
        }
        if any(candidate.get(key) != value for key, value in expected.items()):
            raise OperatorChannelAuthenticationError(
                "operator channel identity or message binding mismatch"
            )
        if candidate["producer"]["component"] != expected_sender_component:
            raise OperatorChannelAuthenticationError(
                "operator channel sender binding mismatch"
            )
        if candidate["payload_hash"] != payload_hash(payload):
            raise OperatorChannelAuthenticationError(
                "operator channel payload hash mismatch"
            )

        issued = self._parse_time(candidate["issued_at"])
        expires = self._parse_time(candidate["expires_at"])
        now = self.clock().astimezone(timezone.utc)
        if expires <= now:
            raise OperatorChannelAuthenticationError(
                "operator channel message expired"
            )
        if issued > now + timedelta(seconds=5):
            raise OperatorChannelAuthenticationError(
                "operator channel message issued in the future"
            )
        if expires - issued > timedelta(seconds=120):
            raise OperatorChannelAuthenticationError(
                "operator channel message lifetime is too broad"
            )

        if not hmac.compare_digest(
            candidate["signature"],
            self._signature(candidate),
        ):
            raise OperatorChannelAuthenticationError(
                "operator channel signature mismatch"
            )
        try:
            self.evidence_store.reserve_operator_message(candidate)
        except Exception as exc:
            raise OperatorChannelAuthenticationError(
                "authenticated operator channel replay or evidence failure"
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
            raise OperatorChannelAuthenticationError(
                "operator channel timestamp is invalid"
            ) from exc
