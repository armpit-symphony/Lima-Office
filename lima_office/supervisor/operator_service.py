"""Foreground authenticated operator endpoint for the lab Supervisor."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.errors import OperatorChannelAuthenticationError

from .control_plane import SupervisorControlPlane
from .operator_channel import OperatorChannel
from .worker_registry import WorkerRecord


logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 256 * 1024


class OperatorControlPlaneService:
    """Authenticate one operator and synchronously run the governed path."""

    def __init__(
        self,
        *,
        channel: OperatorChannel,
        validator: ContractValidator,
        control_plane: SupervisorControlPlane,
    ) -> None:
        self.channel = channel
        self.validator = validator
        self.control_plane = control_plane

    def handle(self, body: Mapping[str, Any]) -> dict[str, Any]:
        request = self._authenticate_and_validate(
            body,
            contract_name="operator.control_plane.request",
        )
        result = self.control_plane.submit(
            {
                "request_id": request["request_id"],
                "tenant_id": self.channel.tenant_id,
                "actor_id": self.channel.actor_id,
                "action": request["action"],
                "resource_type": request["resource_type"],
                "resource_id": request["resource_id"],
                "worker_id": request["worker_id"],
                "idempotency_key": request["idempotency_key"],
            }
        )
        return self._signed(self._response(request, result))

    def handle_inventory(self, body: Mapping[str, Any]) -> dict[str, Any]:
        """Refresh server-owned worker status through Guardian and LIMA."""

        request = self._authenticate_and_validate(
            body,
            contract_name="operator.worker_inventory.request",
        )
        records = self.control_plane.registry.records()
        if records:
            results = self.control_plane.submit_many(
                {
                    "request_id": request["request_id"],
                    "tenant_id": self.channel.tenant_id,
                    "actor_id": self.channel.actor_id,
                    "action": "status",
                    "resource_type": "worker_status",
                    "resource_id": "supervisor_worker_inventory",
                    "worker_id": records[0].worker_id,
                    "idempotency_key": request["idempotency_key"],
                },
                [record.worker_id for record in records],
            )["results"]
        else:
            results = []
        return self._signed(
            self._inventory_response(request, records, results)
        )

    def _authenticate_and_validate(
        self,
        body: Mapping[str, Any],
        *,
        contract_name: str,
    ) -> dict[str, Any]:
        if (
            not isinstance(body, Mapping)
            or set(body) != {"envelope", "payload"}
            or not isinstance(body["envelope"], Mapping)
            or not isinstance(body["payload"], Mapping)
        ):
            raise OperatorChannelAuthenticationError(
                "operator request shape is invalid"
            )
        payload = dict(body["payload"])
        self.channel.verify(
            body["envelope"],
            payload,
            expected_message_type="operator_request",
            expected_sender_component="operator_client",
        )
        request = self.validator.validate(
            payload,
            contract_name,
        )
        self._assert_request_binding(request)
        return request

    def _signed(self, response: dict[str, Any]) -> dict[str, Any]:
        return {
            "envelope": self.channel.sign(
                response,
                message_type="operator_response",
                sender_component="supervisor",
            ),
            "payload": response,
        }

    def _assert_request_binding(self, request: dict[str, Any]) -> None:
        expected = {
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "actor_id": self.channel.actor_id,
            "policy_version": self.channel.policy_version,
        }
        if any(request.get(key) != value for key, value in expected.items()):
            raise OperatorChannelAuthenticationError(
                "operator request identity or policy binding mismatch"
            )
        if request["producer"]["component"] != "operator_client":
            raise OperatorChannelAuthenticationError(
                "operator request producer binding mismatch"
            )
        if request.get("runtime_authority_blocked") is not True:
            raise OperatorChannelAuthenticationError(
                "operator request must block runtime authority"
            )
        if any(
            request.get(field) is not False
            for field in ("executable", "execution_allowed", "side_effects_allowed")
        ):
            raise OperatorChannelAuthenticationError(
                "operator request cannot authorize execution"
            )

    def _response(
        self,
        request: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        assignment = result.get("assignment")
        if not isinstance(assignment, Mapping):
            assignment = None
        evidence = []
        for event in result.get("evidence") or []:
            if not isinstance(event, Mapping):
                continue
            evidence.append(
                {
                    "event_id": str(event["event_id"]),
                    "event_type": str(event["event_type"]),
                    "outcome": str(event["outcome"]),
                    "reason_codes": [
                        str(code) for code in event.get("reason_codes") or []
                    ],
                    "created_at": str(event["created_at"]),
                }
            )
        now = self._now()
        response = {
            "contract_name": "operator.control_plane.response",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": request["correlation_id"],
            "causation_id": request["request_id"],
            "idempotency_key": f"response:{request['idempotency_key']}",
            "producer": {"component": "supervisor", "produced_at": now},
            "policy_version": self.channel.policy_version,
            "request_id": result["request_id"],
            "actor_id": result["actor_id"],
            "worker_id": result["worker_id"],
            "status": result["status"],
            "classification_authority": "supervisor_server_derived",
            "action_category": result["action_category"],
            "guardian": result.get("guardian"),
            "lima": result.get("lima"),
            "assignment_id": (
                str(assignment["assignment_id"]) if assignment is not None else None
            ),
            "assignment_status": (
                str(assignment["status"]) if assignment is not None else None
            ),
            "evidence": evidence,
            "reason_codes": [str(code) for code in result.get("reason_codes") or []],
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }
        return self.validator.validate(
            response,
            "operator.control_plane.response",
        )

    def _inventory_response(
        self,
        request: dict[str, Any],
        records: tuple[WorkerRecord, ...],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        governed = all(
            isinstance(result.get("guardian"), Mapping)
            and isinstance(result.get("lima"), Mapping)
            and result["lima"].get("source_policy") == "guardian_core.policy"
            for result in results
        )
        if results and not governed:
            workers: list[dict[str, Any]] = []
            status = "denied"
            reason_codes = ["recon_missing_guardian_decision"]
        else:
            workers = [
                self._inventory_worker(record, result)
                for record, result in zip(records, results, strict=True)
            ]
            status = (
                "healthy"
                if workers and all(worker["eligible"] for worker in workers)
                else "degraded_read_only"
            )
            reason_codes = sorted(
                {
                    code
                    for worker in workers
                    for code in worker["reason_codes"]
                }
            )
        evidence_refs = sorted(
            {
                reference
                for worker in workers
                for reference in worker["evidence_refs"]
            }
        )
        response = {
            "contract_name": "operator.worker_inventory.response",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "taxonomy_version": "taxonomy-recon-v1",
            "tenant_id": self.channel.tenant_id,
            "customer_context_id": self.channel.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": request["correlation_id"],
            "causation_id": request["request_id"],
            "idempotency_key": f"response:{request['idempotency_key']}",
            "producer": {"component": "supervisor", "produced_at": self._now()},
            "policy_version": self.channel.policy_version,
            "request_id": request["request_id"],
            "actor_id": self.channel.actor_id,
            "status": status,
            "classification_authority": "supervisor_server_derived",
            "worker_count": len(workers),
            "workers": workers,
            "evidence_refs": evidence_refs,
            "reason_codes": reason_codes,
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }
        return self.validator.validate(
            response,
            "operator.worker_inventory.response",
        )

    @staticmethod
    def _inventory_worker(
        record: WorkerRecord,
        result: Mapping[str, Any],
    ) -> dict[str, Any]:
        guardian = result["guardian"]
        lima = result["lima"]
        assignment = result.get("assignment")
        evidence_refs = sorted(
            str(event["event_id"])
            for event in result.get("evidence") or []
            if isinstance(event, Mapping) and event.get("event_id")
        )
        eligible = (
            record.authenticated
            and record.can_accept_task()
            and result.get("status") == "acknowledged"
            and isinstance(assignment, Mapping)
            and assignment.get("status") == "acknowledged"
        )
        return {
            "worker_id": record.worker_id,
            "role": record.role,
            "capabilities": sorted(record.capabilities),
            "state": record.state,
            "authenticated": record.authenticated,
            "eligible": eligible,
            "worker_version": record.worker_version,
            "last_heartbeat_at": record.last_heartbeat_at,
            "control_plane_status": result["status"],
            "guardian_decision_id": guardian["decision_id"],
            "lima_decision_id": lima["decision_id"],
            "lima_status": lima["status"],
            "assignment_status": (
                str(assignment["status"])
                if isinstance(assignment, Mapping)
                else None
            ),
            "evidence_refs": evidence_refs,
            "reason_codes": [
                str(code) for code in result.get("reason_codes") or []
            ],
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class _OperatorRequestHandler(BaseHTTPRequestHandler):
    server: "SupervisorOperatorServer"

    def do_POST(self) -> None:
        handlers = {
            "/v1/operator/preflight": self.server.operator_service.handle,
            "/v1/operator/workers": self.server.operator_service.handle_inventory,
        }
        handler = handlers.get(self.path)
        if handler is None:
            self._reply(HTTPStatus.NOT_FOUND, self._failed_closed("not_found"))
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        if content_length < 1 or content_length > MAX_REQUEST_BYTES:
            self._reply(
                HTTPStatus.BAD_REQUEST,
                self._failed_closed("invalid_request"),
            )
            return
        try:
            raw = self.rfile.read(content_length)
            body = json.loads(raw)
            response = handler(body)
        except OperatorChannelAuthenticationError:
            logger.warning("Supervisor rejected an unauthenticated operator request")
            self._reply(
                HTTPStatus.UNAUTHORIZED,
                self._failed_closed("authentication_failed"),
            )
            return
        except Exception:
            logger.exception("Supervisor operator request failed closed")
            self._reply(
                HTTPStatus.SERVICE_UNAVAILABLE,
                self._failed_closed("unavailable"),
            )
            return
        self._reply(HTTPStatus.OK, response)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("Supervisor operator HTTP request: " + format, *args)

    @staticmethod
    def _failed_closed(status: str) -> dict[str, Any]:
        return {
            "status": status,
            "runtime_authority_blocked": True,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
        }

    def _reply(self, status: HTTPStatus, payload: Mapping[str, Any]) -> None:
        encoded = json.dumps(dict(payload), sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)


class SupervisorOperatorServer(HTTPServer):
    """Single-threaded foreground Supervisor server with no hidden jobs."""

    def __init__(
        self,
        server_address: tuple[str, int],
        operator_service: OperatorControlPlaneService,
    ) -> None:
        self.operator_service = operator_service
        super().__init__(server_address, _OperatorRequestHandler)


def build_supervisor_operator_server(
    *,
    host: str,
    port: int,
    service: OperatorControlPlaneService,
) -> SupervisorOperatorServer:
    """Build, but do not background or start, the lab Supervisor endpoint."""

    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise OperatorChannelAuthenticationError(
            "the first lab Supervisor endpoint is intentionally loopback-only"
        )
    if port < 0 or port > 65535:
        raise OperatorChannelAuthenticationError(
            "Supervisor endpoint port is invalid"
        )
    return SupervisorOperatorServer((host, port), service)
