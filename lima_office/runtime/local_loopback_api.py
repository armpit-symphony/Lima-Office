"""Versioned loopback API for the localhost Supervisor UI.

The listener must be 127.0.0.1. Mutating /api/v1 routes require an active
Profile A or Profile B session. Session establishment is the only
unauthenticated POST set. Legacy /api/office routes stay as lab.7 aliases.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.runtime.errors import ContractValidationError
from lima_office.runtime.operator_session import OperatorSessionError
from lima_office.runtime.profile_b_session import (
    MemoryEvidenceStore,
    ProfileBError,
    ProfileBSessionService,
)
from lima_office.runtime.webauthn_verifier import LocalhostWebAuthnVerifier


API_POLICY = "policy-local-loopback-api-v1"
LOOPBACK_BIND_HOST = "127.0.0.1"
_COMMIT_RE = re.compile(r"^(unknown|[0-9a-f]{40})$")


class LoopbackBindError(RuntimeError):
    """Raised before a socket opens on a non-loopback address."""


class LocalApiError(RuntimeError):
    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    auth: str
    mutating: bool
    office_path: str | None = None
    read_kind: str | None = None


@dataclass(frozen=True)
class DispatchResult:
    status: int
    body: dict[str, Any]
    office_path: str | None = None
    read_kind: str | None = None


ROUTES: tuple[Route, ...] = (
    Route("GET", "/api/v1", "public_read", False),
    Route("GET", "/api/v1/health", "public_read", False),
    Route("GET", "/api/v1/build", "public_read", False),
    Route("GET", "/api/v1/state", "public_read", False, read_kind="state"),
    Route("GET", "/api/v1/operator-session", "public_read", False),
    Route("POST", "/api/v1/operator-session/bind", "session_establishment", True),
    Route("POST", "/api/v1/operator-session/profile-b/begin", "session_establishment", True),
    Route("POST", "/api/v1/operator-session/profile-b/complete", "session_establishment", True),
    Route("GET", "/api/v1/workers", "session_required", False, read_kind="workers"),
    Route("POST", "/api/v1/workers", "session_required", True, office_path="/api/office/workers"),
    Route("POST", "/api/v1/evidence", "session_required", True, office_path="/api/office/evidence"),
    Route("GET", "/api/v1/sop", "session_required", False),
    Route("POST", "/api/v1/conversation", "session_required", True, office_path="/api/office/conversation"),
    Route("POST", "/api/v1/helper/review", "session_required", True, office_path="/api/office/helper/review"),
    Route("POST", "/api/v1/proposals/create", "session_required", True, office_path="/api/office/proposals/create"),
    Route("POST", "/api/v1/proposals/edit", "session_required", True, office_path="/api/office/proposals/edit"),
    Route("POST", "/api/v1/proposals/transition", "session_required", True, office_path="/api/office/proposals/transition"),
    Route("POST", "/api/v1/approval-previews/create", "session_required", True, office_path="/api/office/approval-previews/create"),
    Route("POST", "/api/v1/approval-previews/transition", "session_required", True, office_path="/api/office/approval-previews/transition"),
    Route("POST", "/api/v1/approval-requests/create", "session_required", True, office_path="/api/office/approval-requests/create"),
    Route("POST", "/api/v1/approval-requests/transition", "session_required", True, office_path="/api/office/approval-requests/transition"),
)

_ROUTE_INDEX = {(route.method, route.path): route for route in ROUTES}

NON_GOALS = [
    "foreign_operator_shell_shapes",
    "lan_bind",
    "positive_approval_token_issue",
    "arc_dispatch",
    "profile_c_oidc",
    "customer_data",
]


def assert_loopback_bind(host: str) -> None:
    if host != LOOPBACK_BIND_HOST:
        raise LoopbackBindError("The local API refuses a non-loopback bind.")


def client_is_loopback(host: str) -> bool:
    return host == LOOPBACK_BIND_HOST


def host_header_is_loopback(value: str | None, port: int) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    host = value.strip().lower()
    return host in {
        LOOPBACK_BIND_HOST,
        "localhost",
        f"{LOOPBACK_BIND_HOST}:{port}",
        f"localhost:{port}",
    }


def deprecation_headers() -> dict[str, str]:
    return {
        "Deprecation": "true",
        "X-Lima-Api-Deprecated": "lab.7-alias",
        "Link": '</api/v1>; rel="successor-version"',
    }


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class LocalLoopbackApi:
    """Authz and direct /api/v1 responses. Office mutations delegate out."""

    def __init__(
        self,
        *,
        operator_sessions: Any = None,
        profile_b: ProfileBSessionService | None = None,
        build_info: dict[str, Any] | None = None,
        profile_a_lab_enabled: bool = True,
        tenant_id: str = "tenant-lab-001",
        customer_context_id: str = "customer-context-main",
        validator: ContractValidator | None = None,
        clock: Any = None,
    ) -> None:
        self.operator_sessions = operator_sessions
        self.profile_b = profile_b or ProfileBSessionService(
            MemoryEvidenceStore(),
            verifier=LocalhostWebAuthnVerifier(),
            tenant_id=tenant_id,
            customer_context_id=customer_context_id,
            validator=validator,
            clock=clock,
        )
        self.build_info = build_info or {}
        self.profile_a_lab_enabled = profile_a_lab_enabled
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.validator = validator or self.profile_b.validator
        self.clock = clock or self.profile_b.clock

    def dispatch(self, method: str, path: str, payload: dict[str, Any] | None, session_header: str | None) -> DispatchResult:
        route = _ROUTE_INDEX.get((method, path))
        if route is None:
            if method == "POST":
                self._require_session(session_header)
            raise LocalApiError(404, "not_found", "No such local API route.")
        if route.auth == "session_required":
            self._require_session(session_header)
        if route.office_path:
            return DispatchResult(200, {}, office_path=route.office_path)
        if route.read_kind:
            return DispatchResult(200, {}, read_kind=route.read_kind)
        body = self._direct(route, payload or {})
        return DispatchResult(200, body)

    def error(self, code: str, detail: str) -> dict[str, Any]:
        now = self.clock()
        token = uuid4().hex
        safe_detail = " ".join(str(detail).split())[:240] or "The local API denied the request."
        record = {
            **self._envelope(now, token, "local_loopback_api", "local.api.v1.error"),
            "error": code,
            "detail": safe_detail,
            "loopback_only": True,
            "runtime_authority_blocked": True,
            "approval_authority": False,
            "production_ready": False,
            "customer_pilot_allowed": False,
        }
        return self._validated(record, "local.api.v1.error")

    def descriptor(self) -> dict[str, Any]:
        now = self.clock()
        token = "descriptor"
        record = {
            **self._envelope(now, token, "local_loopback_api", "local.api.v1.descriptor"),
            "api_version": "v1",
            "bind_host": LOOPBACK_BIND_HOST,
            "version_prefix": "/api/v1",
            "legacy_prefix": "/api/office",
            "legacy_aliases_deprecated": True,
            "anonymous_mutating_routes": False,
            "production_ready": False,
            "customer_pilot_allowed": False,
            "operator_authentication_manifest": False,
            "runtime_authority_blocked": True,
            "foreign_operator_shell_dependency": False,
            "non_goals": list(NON_GOALS),
            "routes": [
                {
                    "method": route.method,
                    "path": route.path,
                    "auth": route.auth,
                    "mutating": route.mutating,
                    "runtime_authority_blocked": True,
                }
                for route in ROUTES
            ],
        }
        return self._validated(record, "local.api.v1.descriptor")

    def health(self) -> dict[str, Any]:
        now = self.clock()
        version = self.build_info.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"[0-9A-Za-z.-]{1,64}", version):
            version = "development"
        commit = self.build_info.get("arc_commit")
        if not isinstance(commit, str) or not _COMMIT_RE.fullmatch(commit):
            commit = "unknown"
        record = {
            **self._envelope(now, "health", "local_loopback_api", "local.api.v1.health"),
            "status": "ready",
            "loopback_only": True,
            "bind_host": LOOPBACK_BIND_HOST,
            "api_version": "v1",
            "build_version": version,
            "arc_commit": commit,
            "source_modified": self.build_info.get("source_modified") is True,
            "production_ready": False,
            "customer_pilot_allowed": False,
            "operator_authentication": False,
            "runtime_authority_blocked": True,
        }
        return self._validated(record, "local.api.v1.health")

    def sop_list(self) -> dict[str, Any]:
        now = self.clock()
        record = {
            **self._envelope(now, "sop", "local_loopback_api", "local.api.v1.sop_list"),
            "items": [
                {
                    "sop_id": "sop-lab-registration-practice",
                    "title": "Synthetic registration practice",
                }
            ],
            "count": 1,
            "instruction_bodies_included": False,
            "runtime_authority_blocked": True,
            "dispatch_enabled": False,
        }
        return self._validated(record, "local.api.v1.sop_list")

    def _direct(self, route: Route, payload: dict[str, Any]) -> dict[str, Any]:
        if route.path == "/api/v1":
            return self.descriptor()
        if route.path in {"/api/v1/health", "/api/v1/build"}:
            return self.health()
        if route.path == "/api/v1/operator-session" and route.method == "GET":
            summary = self.profile_b.public_summary()
            if "binding_id" in summary:
                raise LocalApiError(500, "boundary_denied", "The local API response was rejected.")
            return summary
        if route.path == "/api/v1/sop":
            return self.sop_list()
        if route.path == "/api/v1/operator-session/bind":
            return self._bind_profile_a(payload)
        if route.path == "/api/v1/operator-session/profile-b/begin":
            return self._profile_b_begin(payload)
        if route.path == "/api/v1/operator-session/profile-b/complete":
            return self._profile_b_complete(payload)
        raise LocalApiError(404, "not_found", "No such local API route.")

    def _bind_profile_a(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.profile_a_lab_enabled:
            raise LocalApiError(403, "profile_a_disabled", "Profile A lab bind is turned off.")
        if self.operator_sessions is None:
            raise LocalApiError(403, "ceremony_unavailable", "Profile A session binding is unavailable.")
        try:
            return self.operator_sessions.bind(confirmation=payload.get("confirmation"))
        except OperatorSessionError as exc:
            raise LocalApiError(409, "boundary_denied", str(exc)) from exc

    def _profile_b_begin(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.profile_b.begin(
                owner_display_name=payload.get("owner_display_name"),
                confirmation=payload.get("confirmation"),
            )
        except ProfileBError as exc:
            status = 400 if exc.code == "request_invalid" else 403
            raise LocalApiError(status, exc.code, str(exc)) from exc

    def _profile_b_complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.profile_b.complete(
                challenge_id=payload.get("challenge_id"),
                assertion=payload.get("assertion"),
            )
        except ProfileBError as exc:
            status = 400 if exc.code == "request_invalid" else 403
            raise LocalApiError(status, exc.code, str(exc)) from exc

    def _require_session(self, session_header: str | None) -> dict[str, Any]:
        if not isinstance(session_header, str) or not session_header:
            raise LocalApiError(401, "unauthenticated", "An active operator session is required.")
        try:
            if session_header.startswith("operator-profile-b-session:"):
                return self.profile_b.require_active(session_header)
            if session_header.startswith("operator-session-binding:") and self.operator_sessions is not None:
                return self.operator_sessions.require_active(session_header)
        except (ProfileBError, OperatorSessionError) as exc:
            raise LocalApiError(401, "unauthenticated", "The operator session is not active.") from exc
        raise LocalApiError(401, "unauthenticated", "An active operator session is required.")

    def _envelope(self, now: datetime, token: str, component: str, contract_name: str) -> dict[str, Any]:
        return {
            "contract_name": contract_name,
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr-{contract_name}-{token}",
            "causation_id": None,
            "idempotency_key": f"idem-{contract_name}-{token}",
            "producer": {"component": component, "produced_at": _timestamp(now)},
            "policy_version": API_POLICY,
        }

    def _validated(self, payload: dict[str, Any], schema: str) -> dict[str, Any]:
        try:
            return self.validator.validate(payload, schema)
        except ContractValidationError as exc:
            raise LocalApiError(500, "boundary_denied", "The local API response was rejected.") from exc
