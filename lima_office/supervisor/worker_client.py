"""Supervisor-side client for an authenticated non-executing Arc worker."""

from __future__ import annotations

from datetime import datetime, timezone
import ipaddress
import json
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlparse
from uuid import uuid4

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import (
    WorkerChannelAuthenticationError,
    WorkerEndpointUnavailableError,
)

from .arc_worker import ArcWorkerPreviewEndpoint
from .worker_channel import WorkerChannel


MAX_RESPONSE_BYTES = 256 * 1024


class AuthenticatedArcWorkerClient(ArcWorkerPreviewEndpoint):
    """Call one explicit Arc endpoint; never route tools, models, or execution."""

    def __init__(
        self,
        *,
        base_url: str,
        channel: WorkerChannel,
        validator: ContractValidator,
        timeout_seconds: float = 2.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.channel = channel
        self.validator = validator
        self.timeout_seconds = timeout_seconds
        self._validate_lab_url(self.base_url)

    def request_registration(self) -> dict[str, Any]:
        challenge = self._challenge()
        response = self._post(
            "/v1/registration",
            challenge,
            request_type="registration_challenge",
            response_type="registration",
        )
        return self.validator.validate(response, "worker.registration")

    def request_heartbeat(self) -> dict[str, Any]:
        challenge = self._challenge()
        response = self._post(
            "/v1/heartbeat",
            challenge,
            request_type="heartbeat_challenge",
            response_type="heartbeat",
        )
        return self.validator.validate(response, "worker.heartbeat")

    def acknowledge_preview(
        self,
        assignment: dict[str, Any],
    ) -> dict[str, Any]:
        assignment = self.validator.validate(
            assignment,
            "worker.assignment.preview",
        )
        self._assert_non_executing(assignment)
        response = self._post(
            "/v1/assignment-preview",
            assignment,
            request_type="assignment_preview",
            response_type="assignment_acknowledgement",
        )
        response = self.validator.validate(
            response,
            "worker.assignment.preview",
        )
        self._assert_non_executing(response)
        if response["assignment_id"] != assignment["assignment_id"]:
            raise WorkerChannelAuthenticationError(
                "Arc acknowledgement assignment binding mismatch"
            )
        return response

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        request_type: str,
        response_type: str,
    ) -> dict[str, Any]:
        envelope = self.channel.sign(
            payload,
            message_type=request_type,
            sender_component="supervisor",
        )
        encoded = json.dumps(
            {"envelope": envelope, "payload": payload},
            sort_keys=True,
        ).encode("utf-8")
        request = urllib_request.Request(
            self.base_url + path,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                content_length = int(
                    response.headers.get("Content-Length", MAX_RESPONSE_BYTES)
                )
                if content_length < 1 or content_length > MAX_RESPONSE_BYTES:
                    raise WorkerChannelAuthenticationError(
                        "Arc response size is invalid"
                    )
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except (
            OSError,
            ValueError,
            urllib_error.HTTPError,
            urllib_error.URLError,
        ) as exc:
            raise WorkerEndpointUnavailableError(
                "Arc worker endpoint is unavailable"
            ) from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise WorkerChannelAuthenticationError("Arc response is too large")
        try:
            body = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkerChannelAuthenticationError(
                "Arc response is not valid JSON"
            ) from exc
        if (
            not isinstance(body, dict)
            or set(body) != {"envelope", "payload"}
            or not isinstance(body["envelope"], dict)
            or not isinstance(body["payload"], dict)
        ):
            raise WorkerChannelAuthenticationError(
                "Arc response shape is invalid"
            )
        self.channel.verify(
            body["envelope"],
            body["payload"],
            expected_message_type=response_type,
            expected_sender_component="worker",
        )
        return dict(body["payload"])

    @staticmethod
    def _challenge() -> dict[str, Any]:
        return {
            "challenge_id": f"challenge:{uuid4().hex}",
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }

    @staticmethod
    def _assert_non_executing(payload: dict[str, Any]) -> None:
        if payload.get("runtime_authority_blocked") is not True:
            raise WorkerChannelAuthenticationError(
                "Arc preview must block runtime authority"
            )
        if any(
            payload.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise WorkerChannelAuthenticationError(
                "Arc preview cannot authorize execution"
            )

    @staticmethod
    def _validate_lab_url(base_url: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme != "http" or parsed.username or parsed.password:
            raise WorkerChannelAuthenticationError(
                "Arc lab endpoint must be credential-free HTTP metadata transport"
            )
        if not parsed.hostname or parsed.query or parsed.fragment:
            raise WorkerChannelAuthenticationError("Arc lab endpoint URL is invalid")
        if parsed.hostname == "localhost":
            return
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError as exc:
            raise WorkerChannelAuthenticationError(
                "Arc lab endpoint must use a literal loopback address"
            ) from exc
        if not address.is_loopback:
            raise WorkerChannelAuthenticationError(
                "Arc lab endpoint is loopback-only until trusted private-LAN "
                "transport is approved"
            )
