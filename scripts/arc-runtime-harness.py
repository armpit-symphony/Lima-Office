#!/usr/bin/env python3
"""Run the localhost Arc physical-PC test harness and operator UI."""

from __future__ import annotations

import importlib.util
import json
import os
import hmac
import re
import subprocess
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import shutil
import sys
from typing import Any


OFFICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(OFFICE_ROOT))

_SESSION_PATH = OFFICE_ROOT / "scripts" / "arc-office-session.py"
_spec = importlib.util.spec_from_file_location("_arc_office_session", _SESSION_PATH)
assert _spec is not None and _spec.loader is not None
_session = importlib.util.module_from_spec(_spec)
sys.modules["_arc_office_session"] = _session
_spec.loader.exec_module(_session)

from lima_office.runtime.operator_harness import HarnessBoundaryError  # noqa: E402
from lima_office.runtime.operator_ide import (  # noqa: E402
    OperatorIDEStateStore,
)
from lima_office.runtime.training_model import (  # noqa: E402
    GovernedTrainingAssistant,
    LocalModelOperatorIDEHarness,
)
from lima_office.runtime.supervisor_console import (  # noqa: E402
    build_supervisor_console_state,
)
from lima_office.runtime.supervisor_conversation import (  # noqa: E402
    SupervisorConversationError,
    SupervisorConversationService,
)
from lima_office.runtime.office_helper import (  # noqa: E402
    OfficeHelperError,
    OfficeOperationsHelperService,
)
from lima_office.runtime.task_proposal import (  # noqa: E402
    OfficeTaskProposalService,
    TaskProposalError,
)
from lima_office.runtime.approval_preview import (  # noqa: E402
    ApprovalPreviewError,
    OfficeApprovalPreviewService,
)
from lima_office.runtime.operator_session import (  # noqa: E402
    AttendedOperatorSessionService,
    OperatorSessionError,
)
from lima_office.runtime.local_loopback_api import (  # noqa: E402
    LocalApiError,
    LocalLoopbackApi,
    assert_loopback_bind,
    client_is_loopback,
    deprecation_headers,
    host_header_is_loopback,
)
from lima_office.runtime.profile_b_session import (  # noqa: E402
    PlatformHelperCeremonyVerifier,
    ProfileBError,
    ProfileBSessionService,
)
from lima_office.runtime.webauthn_verifier import LocalhostWebAuthnVerifier  # noqa: E402
from lima_office.runtime.pending_approval_request import (  # noqa: E402
    PendingApprovalRequestError,
    PendingApprovalRequestService,
)
from lima_office.runtime.approval_decision import (  # noqa: E402
    ApprovalDecisionError,
    NonAuthorizingApprovalDecisionService,
)



MAX_REQUEST_BYTES = 64 * 1024


def _build_info(args: Any) -> dict:
    result = {"version": "development", "arc_commit": "unknown", "source_modified": True}
    if args.installation_info:
        info = json.loads(args.installation_info.read_text(encoding="utf-8-sig"))
        version = info.get("version", "")
        if re.fullmatch(r"[0-9A-Za-z.-]{1,64}", version):
            result["version"] = version
    try:
        commit = subprocess.check_output(["git", "-C", str(args.arc_source), "rev-parse", "HEAD"], text=True).strip()
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            result["arc_commit"] = commit
        dirty = subprocess.check_output(["git", "-C", str(args.arc_source), "status", "--porcelain", "--untracked-files=no"], text=True)
        result["source_modified"] = bool(dirty.strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return result


def _parser():
    parser = _session._parser()
    parser.description = (
        "Start the real governed Arc worker and Supervisor behind a "
        "localhost-only Training/Working test UI."
    )
    parser.add_argument(
        "--ui-file",
        type=Path,
        default=None,
        help="Arc-owned IDE HTML. Defaults to <arc-source>/ui/arc_operator_ide.html.",
    )
    parser.add_argument(
        "--office-ui-file",
        type=Path,
        default=None,
        help=(
            "LIMA Office Supervisor Console HTML. Defaults to "
            "<office-source>/ui/lima_office_supervisor_console.html."
        ),
    )
    parser.add_argument(
        "--ui-port",
        type=int,
        default=8765,
        help="Loopback UI port (default: 8765).",
    )
    parser.add_argument(
        "--task-queue-path",
        type=Path,
        default=None,
        help="Optional Arc JSONL task queue; defaults to Arc's local queue.",
    )
    parser.add_argument(
        "--approval-path",
        type=Path,
        default=None,
        help="Optional Arc JSONL approval queue; defaults to Arc's local queue.",
    )
    parser.add_argument(
        "--local-model-enabled",
        action="store_true",
        help="Configure the attended loopback Ollama SOP drafting surface.",
    )
    parser.add_argument(
        "--local-model-endpoint",
        default="http://127.0.0.1:11434",
        help="Loopback-only Ollama base URL.",
    )
    parser.add_argument(
        "--local-model-name",
        default="qwen2.5:7b",
        help="Explicit local Ollama model name.",
    )
    parser.add_argument(
        "--local-model-supervisor-opt-in",
        action="store_true",
        help="Supervisor-side opt-in for local-model grants.",
    )
    parser.add_argument(
        "--local-model-arc-opt-in",
        action="store_true",
        help="Arc-side opt-in for loopback local-model execution.",
    )
    parser.add_argument("--installation-info", type=Path)
    parser.add_argument("--lifecycle-token-file", type=Path)
    parser.add_argument(
        "--profile-b-helper",
        type=Path,
        default=None,
        help="Absolute platform helper. When unset, localhost WebAuthn verification is used.",
    )
    parser.add_argument(
        "--disable-profile-a-lab",
        action="store_true",
        help="Turn off the lab-only Profile A attended bind. Profile A stays on unless this is set.",
    )
    return parser


def _default_session_dir() -> Path:
    explicit = os.environ.get("ARC_BOT_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser() / "runtime-harness"
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "ArcBot" / "runtime-harness"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "arc-bot-shell" / "runtime-harness"
    return Path.home() / ".local" / "share" / "arc-bot-shell" / "runtime-harness"


class HarnessHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        harness: OperatorIDEHarness,
        ui: bytes,
        office_ui: bytes,
        supervisor_conversation: SupervisorConversationService | None = None,
        office_helper: OfficeOperationsHelperService | None = None,
        task_proposals: OfficeTaskProposalService | None = None,
        approval_previews: OfficeApprovalPreviewService | None = None,
        operator_sessions: AttendedOperatorSessionService | None = None,
        pending_approval_requests: PendingApprovalRequestService | None = None,
        approval_decisions: NonAuthorizingApprovalDecisionService | None = None,
        profile_b: ProfileBSessionService | None = None,
        profile_a_lab_enabled: bool = True,
    ) -> None:
        assert_loopback_bind(address[0])
        self.harness = harness
        self.ui = ui
        self.office_ui = office_ui
        self.supervisor_conversation = supervisor_conversation
        self.office_helper = office_helper
        self.task_proposals = task_proposals
        self.approval_previews = approval_previews
        self.operator_sessions = operator_sessions
        self.pending_approval_requests = pending_approval_requests
        self.approval_decisions = approval_decisions
        self.profile_b = profile_b
        self.profile_a_lab_enabled = profile_a_lab_enabled
        self.local_api = None
        self.build_info = {"version": "development", "arc_commit": "unknown", "source_modified": True}
        self.lifecycle_token = None
        super().__init__(address, HarnessRequestHandler)


class _OfficeRouteNotFound(Exception):
    pass


class HarnessRequestHandler(BaseHTTPRequestHandler):
    server: HarnessHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("arc-harness: " + (format % args) + "\n")

    def _headers(self, status: int, content_type: str, length: int, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
        )
        self.end_headers()

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        extra = deprecation_headers() if self.path.startswith("/api/office") else None
        self._headers(status, "application/json; charset=utf-8", len(body), extra)
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").partition(";")[0]
        if content_type != "application/json":
            raise HarnessBoundaryError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise HarnessBoundaryError("invalid Content-Length") from exc
        if length < 2 or length > MAX_REQUEST_BYTES:
            raise HarnessBoundaryError("request body size is outside the allowed range")
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise HarnessBoundaryError("request body is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise HarnessBoundaryError("request body must be a JSON object")
        return payload

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        host, port = self.server.server_address
        allowed = {
            f"http://{host}:{port}",
            f"http://localhost:{port}",
        }
        return origin in allowed

    def _reject_non_loopback(self) -> bool:
        client_host = self.client_address[0] if self.client_address else ""
        if not client_is_loopback(client_host):
            self._json(403, self._safe_error("non_loopback", "This API accepts 127.0.0.1 clients only."))
            return True
        port = self.server.server_address[1]
        if not host_header_is_loopback(self.headers.get("Host"), port):
            self._json(403, self._safe_error("non_loopback", "The Host header is not loopback."))
            return True
        return False

    def _safe_error(self, code: str, detail: str) -> dict[str, Any]:
        try:
            return self._local_api().error(code, detail)
        except Exception:
            return {
                "error": code,
                "detail": detail,
                "loopback_only": True,
                "approval_authority": False,
            }

    def _local_api(self) -> LocalLoopbackApi:
        api = self.server.local_api
        if api is not None:
            return api
        api = LocalLoopbackApi(
            operator_sessions=self.server.operator_sessions,
            profile_b=self.server.profile_b,
            build_info=self.server.build_info,
            profile_a_lab_enabled=self.server.profile_a_lab_enabled,
        )
        self.server.local_api = api
        if self.server.profile_b is None:
            self.server.profile_b = api.profile_b
        return api

    def _supervisor_state(self) -> dict[str, Any]:
        profile_b = self.server.profile_b
        return build_supervisor_console_state(
            self.server.harness.state(),
            self.server.build_info,
            conversation_state=(
                self.server.supervisor_conversation.state_summary()
                if self.server.supervisor_conversation is not None
                else None
            ),
            helper_state=(
                self.server.office_helper.state_summary()
                if self.server.office_helper is not None
                else None
            ),
            proposal_state=(
                self.server.task_proposals.state_summary()
                if self.server.task_proposals is not None
                else None
            ),
            approval_preview_state=(
                self.server.approval_previews.state_summary()
                if self.server.approval_previews is not None
                else None
            ),
            operator_session_state=(
                self.server.operator_sessions.state_summary()
                if self.server.operator_sessions is not None else None
            ),
            pending_approval_request_state=(
                self.server.pending_approval_requests.state_summary()
                if self.server.pending_approval_requests is not None else None
            ),
            profile_b_state=(
                profile_b.public_summary() if profile_b is not None else None
            ),
        )

    def _cached_worker_count(self) -> dict[str, Any]:
        state = self.server.harness.state()
        office = state.get("office_integration") if isinstance(state, dict) else None
        office = office if isinstance(office, dict) else {}
        inventory = office.get("inventory") if isinstance(office.get("inventory"), dict) else {}
        workers = inventory.get("workers") if isinstance(inventory, dict) else []
        return {
            "resource": "workers",
            "cached": True,
            "count": len(workers) if isinstance(workers, list) else 0,
            "runtime_authority_blocked": True,
            "automatic_refresh": False,
            "approval_authority": False,
        }

    def _handle_v1(self, method: str) -> None:
        if method == "POST" and not self._origin_allowed():
            self._json(403, self._safe_error("origin_not_allowed", "The request origin is not this loopback UI."))
            return
        payload = None
        if method == "POST":
            try:
                payload = self._read_json()
            except HarnessBoundaryError as exc:
                self._json(409, self._safe_error("request_invalid", str(exc)))
                return
        try:
            outcome = self._local_api().dispatch(
                method,
                self.path,
                payload,
                self.headers.get("X-Lima-Operator-Session"),
            )
        except LocalApiError as exc:
            self._json(exc.status, self._safe_error(exc.code, str(exc)))
            return
        if outcome.read_kind == "state":
            self._json(200, self._supervisor_state())
            return
        if outcome.read_kind == "workers":
            self._json(200, self._cached_worker_count())
            return
        if outcome.office_path:
            try:
                result = self._legacy_office_post(outcome.office_path, payload or {})
            except _OfficeRouteNotFound:
                self._json(404, self._safe_error("not_found", "No such local API route."))
                return
            except (
                HarnessBoundaryError, OfficeHelperError, SupervisorConversationError,
                TaskProposalError, ApprovalPreviewError, OperatorSessionError,
                PendingApprovalRequestError, ApprovalDecisionError, ProfileBError,
            ) as exc:
                self._json(409, {"error": "boundary_denied", "detail": str(exc)})
                return
            except Exception as exc:
                self.log_error("request failed: %s", type(exc).__name__)
                self._json(500, {"error": "harness_request_failed"})
                return
            self._json(200, result)
            return
        self._json(outcome.status, outcome.body)

    def _legacy_office_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if path == "/api/office/workers":
            return self.server.harness.refresh_office_workers()
        if path == "/api/office/evidence":
            return self.server.harness.read_office_evidence(
                target_request_id=payload.get("target_request_id")
            )
        if path == "/api/office/conversation":
            if self.server.supervisor_conversation is None:
                raise SupervisorConversationError("Supervisor conversation contracts are unavailable.")
            return self.server.supervisor_conversation.turn(
                message=payload.get("message"),
                confirmation=payload.get("confirmation"),
                data_classification=payload.get("data_classification"),
            )
        if path == "/api/office/helper/review":
            if self.server.office_helper is None:
                raise OfficeHelperError("Office Operations Helper is unavailable.")
            return self.server.office_helper.review_registration(
                scenario_id=payload.get("scenario_id"),
                confirmation=payload.get("confirmation"),
            )
        if path == "/api/office/proposals/create":
            if self.server.office_helper is None or self.server.task_proposals is None:
                raise TaskProposalError("Supervisor task proposals are unavailable.")
            helper_result = self.server.office_helper.proposal_source(payload.get("helper_result_id"))
            return self.server.task_proposals.create_from_helper(
                helper_result=helper_result,
                confirmation=payload.get("confirmation"),
            )
        if path == "/api/office/proposals/edit":
            if self.server.task_proposals is None:
                raise TaskProposalError("Supervisor task proposals are unavailable.")
            return self.server.task_proposals.edit(
                proposal_id=payload.get("proposal_id"),
                expected_revision=payload.get("expected_revision"),
                priority=payload.get("priority"),
                selected_step_ids=payload.get("selected_step_ids"),
                confirmation=payload.get("confirmation"),
            )
        if path == "/api/office/proposals/transition":
            if self.server.task_proposals is None:
                raise TaskProposalError("Supervisor task proposals are unavailable.")
            return self.server.task_proposals.transition(
                proposal_id=payload.get("proposal_id"),
                expected_revision=payload.get("expected_revision"),
                action=payload.get("action"),
                confirmation=payload.get("confirmation"),
            )
        if path == "/api/office/approval-previews/create":
            if self.server.approval_previews is None:
                raise ApprovalPreviewError("Approval previews are unavailable.")
            return self.server.approval_previews.create_from_proposal(
                proposal_id=payload.get("proposal_id"),
                expected_proposal_revision=payload.get("expected_proposal_revision"),
                confirmation=payload.get("confirmation"),
            )
        if path == "/api/office/approval-previews/transition":
            if self.server.approval_previews is None:
                raise ApprovalPreviewError("Approval previews are unavailable.")
            return self.server.approval_previews.transition(
                approval_preview_id=payload.get("approval_preview_id"),
                expected_revision=payload.get("expected_revision"),
                action=payload.get("action"),
                confirmation=payload.get("confirmation"),
            )
        if path == "/api/office/operator-session/bind":
            if self.server.operator_sessions is None:
                raise OperatorSessionError("Operator-session binding is unavailable.")
            return self.server.operator_sessions.bind(confirmation=payload.get("confirmation"))
        if path == "/api/office/approval-requests/create":
            if self.server.pending_approval_requests is None:
                raise PendingApprovalRequestError("Pending approval requests are unavailable.")
            return self.server.pending_approval_requests.create(
                approval_preview_id=payload.get("approval_preview_id"),
                expected_preview_revision=payload.get("expected_preview_revision"),
                operator_session_binding_id=payload.get("operator_session_binding_id"),
                confirmation=payload.get("confirmation"),
            )
        if path == "/api/office/approval-requests/transition":
            if self.server.approval_decisions is None:
                raise ApprovalDecisionError("Approval decisions are unavailable.")
            return self.server.approval_decisions.transition(
                approval_request_id=payload.get("approval_request_id"),
                expected_request_hash=payload.get("expected_request_hash"),
                action=payload.get("action"),
                operator_session_binding_id=payload.get("operator_session_binding_id"),
                confirmation=payload.get("confirmation"),
            )
        raise _OfficeRouteNotFound()

    def do_GET(self) -> None:  # noqa: N802
        if self._reject_non_loopback():
            return
        if self.path.startswith("/api/v1"):
            self._handle_v1("GET")
            return
        if self.path in {"/", "/index.html"}:
            self._headers(200, "text/html; charset=utf-8", len(self.server.ui))
            self.wfile.write(self.server.ui)
            return
        if self.path in {"/office", "/office/", "/office/index.html"}:
            self._headers(
                200,
                "text/html; charset=utf-8",
                len(self.server.office_ui),
            )
            self.wfile.write(self.server.office_ui)
            return
        if self.path == "/api/state":
            self._json(200, {**self.server.harness.state(), "build": self.server.build_info})
            return
        if self.path == "/api/office/state":
            self._json(200, self._supervisor_state())
            return
        if self.path == "/api/training/registration/catalog":
            self._json(200, self.server.harness.registration_catalog())
            return
        if self.path == "/api/health":
            self._json(
                200,
                {
                    "status": "ready",
                    "loopback_only": True,
                    "mode": self.server.harness.mode,
                },
            )
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self._reject_non_loopback():
            return
        if self.path.startswith("/api/v1"):
            self._handle_v1("POST")
            return
        if not self._origin_allowed():
            self._json(403, {"error": "origin_not_allowed"})
            return
        try:
            payload = self._read_json()
            if self.path == "/api/support/export":
                from lima_office.runtime.lab_support import diagnostic_bundle
                body = diagnostic_bundle(self.server.harness, self.server.build_info)
                self._headers(200, "application/zip", len(body))
                self.wfile.write(body)
                return
            if self.path == "/api/support/reset":
                from lima_office.runtime.lab_support import support_action
                result = support_action(self.server.harness, "synthetic_history_reset",
                    confirmed=payload.get("confirmation") == "RESET SYNTHETIC HISTORY")
                self._json(200, result)
                return
            if self.path == "/api/lifecycle/stop":
                token = payload.get("token")
                expected = self.server.lifecycle_token
                if not expected or not isinstance(token, str) or not hmac.compare_digest(token, expected):
                    self._json(403, {"error": "lifecycle_token_required"})
                    return
                from lima_office.runtime.lab_support import support_action
                support_action(self.server.harness, "service_stop")
                self._json(200, {"status": "stopping"})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if self.path == "/api/mode":
                result = self.server.harness.set_mode(payload.get("mode"))
            elif self.path == "/api/training/instruction":
                result = self.server.harness.teach(
                    task_ref=payload.get("task_ref"),
                    instruction=payload.get("instruction"),
                    authored_by_role=payload.get("authored_by_role"),
                )
            elif self.path == "/api/training/draft":
                result = self.server.harness.draft_training(
                    task_ref=payload.get("task_ref"),
                    goal=payload.get("goal"),
                )
            elif self.path == "/api/training/registration/run":
                result = self.server.harness.run_registration_practice(
                    scenario_id=payload.get("scenario_id"),
                )
            elif self.path == "/api/training/registration/run-suite":
                result = self.server.harness.run_registration_practice_suite()
            elif self.path == "/api/training/registration/review":
                result = self.server.harness.review_registration_practice(
                    attempt_id=payload.get("attempt_id"),
                    decision=payload.get("decision"),
                )
            elif self.path == "/api/training/resolve-gap":
                result = self.server.harness.resolve_gap(
                    gap_id=payload.get("gap_id"),
                    instruction=payload.get("instruction"),
                    resolved_by_role=payload.get("resolved_by_role"),
                )
            elif self.path == "/api/training/escalation-ladder":
                result = self.server.harness.configure_ladder(payload)

            elif self.path == "/api/work/list":
                result = self.server.harness.governed_list(
                    task_ref=payload.get("task_ref"),
                    resource_id=payload.get("resource_id"),
                )
            elif self.path == "/api/work/read":
                result = self.server.harness.governed_read(
                    task_ref=payload.get("task_ref"),
                    resource_id=payload.get("resource_id"),
                )
            elif self.path == "/api/worker/status":
                result = self.server.harness.worker_status()
            elif self.path.startswith("/api/office/"):
                try:
                    result = self._legacy_office_post(self.path, payload)
                except _OfficeRouteNotFound:
                    self._json(404, {"error": "not_found"})
                    return
            elif self.path == "/api/work/content-page":
                result = self.server.harness.document_page(
                    content_id=payload.get("content_id"),
                    offset=payload.get("offset"),
                )
            elif self.path == "/api/work/approval":
                result = self.server.harness.decide_approval(
                    approval_id=payload.get("approval_id"),
                    decision=payload.get("decision"),
                    operator_id=payload.get("operator_id"),
                    reason=payload.get("reason"),
                )

            else:
                self._json(404, {"error": "not_found"})
                return
        except (
            HarnessBoundaryError, OfficeHelperError, SupervisorConversationError,
            TaskProposalError, ApprovalPreviewError, OperatorSessionError,
            PendingApprovalRequestError,
            ApprovalDecisionError,
        ) as exc:
            self._json(409, {"error": "boundary_denied", "detail": str(exc)})
            return
        except Exception as exc:  # the UI must fail closed, not leak internals
            self.log_error("request failed: %s", type(exc).__name__)
            self._json(500, {"error": "harness_request_failed"})
            return
        self._json(200, result)


def _resolve_args(args: Any) -> Any:
    args.arc_source = args.arc_source.expanduser().resolve()
    if not (args.arc_source / "arc_bot_shell" / "control_plane").is_dir():
        raise SystemExit("Arc source lacks the control-plane package")
    if args.document_root is not None:
        args.document_root = args.document_root.expanduser().resolve()
        if not args.document_root.is_dir():
            raise SystemExit("document root is not a directory")
    if not 0 <= args.ui_port <= 65535:
        raise SystemExit("ui port must be between 0 and 65535")
    args.session_dir = (
        args.session_dir.expanduser().resolve()
        if args.session_dir is not None
        else _default_session_dir().resolve()
    )
    for name in ("task_queue_path", "approval_path"):
        value = getattr(args, name)
        if value is not None:
            setattr(args, name, value.expanduser().resolve())

    args.session_dir.mkdir(parents=True, exist_ok=True)
    args.ui_file = (
        args.ui_file.expanduser().resolve()
        if args.ui_file is not None
        else args.arc_source / "ui" / "arc_operator_ide.html"
    )
    if not args.ui_file.is_file():
        raise SystemExit(f"Arc harness UI not found: {args.ui_file}")
    args.office_ui_file = (
        args.office_ui_file.expanduser().resolve()
        if args.office_ui_file is not None
        else OFFICE_ROOT / "ui" / "lima_office_supervisor_console.html"
    )
    if not args.office_ui_file.is_file():
        raise SystemExit(f"LIMA Office Supervisor UI not found: {args.office_ui_file}")
    return args


def _arc_operator_ide(args: Any) -> Any:
    sys.path.insert(0, str(args.arc_source))
    from arc_bot_shell.tasks import ArcOperatorIDE

    return ArcOperatorIDE(
        args.arc_source,
        queue_path=args.task_queue_path,
        approval_path=args.approval_path,
    )

def _training_assistant(args: Any) -> GovernedTrainingAssistant | None:
    if not args.local_model_enabled:
        return None
    sys.path.insert(0, str(args.arc_source))
    from arc_bot_shell.model import OllamaTrainingDraftExecutor

    executor = OllamaTrainingDraftExecutor(
        endpoint=args.local_model_endpoint,
        model=args.local_model_name,
        operator_opt_in=args.local_model_arc_opt_in,
    )
    return GovernedTrainingAssistant(
        executor,
        supervisor_opt_in=args.local_model_supervisor_opt_in,
        tenant_id=str(args.tenant_id),
        worker_id=str(args.worker_id),
    )


def main(argv: list[str] | None = None) -> int:
    args = _resolve_args(_parser().parse_args(argv))

    ui = args.ui_file.read_bytes()
    office_ui = args.office_ui_file.read_bytes()
    session = _session.ArcOfficeSession(args, args.session_dir)
    store: OperatorIDEStateStore | None = None
    server: HarnessHTTPServer | None = None


    try:
        session.start()
        store = OperatorIDEStateStore(args.session_dir / "harness-state.db")
        harness = LocalModelOperatorIDEHarness(
            session, store, arc_ide=_arc_operator_ide(args),
            training_assistant=_training_assistant(args),
        )
        try:
            supervisor_conversation = SupervisorConversationService(
                store,
                tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
        except Exception:
            supervisor_conversation = None
        try:
            office_helper = OfficeOperationsHelperService(
                store,
                tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
        except Exception:
            office_helper = None
        try:
            task_proposals = OfficeTaskProposalService(
                store,
                tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
        except Exception:
            task_proposals = None
        try:
            approval_previews = OfficeApprovalPreviewService(
                store,
                tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
        except Exception:
            approval_previews = None
        try:
            operator_sessions = AttendedOperatorSessionService(
                store, tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
            pending_approval_requests = PendingApprovalRequestService(
                store, operator_sessions, tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
            approval_decisions = NonAuthorizingApprovalDecisionService(
                store, operator_sessions, tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
        except Exception:
            operator_sessions = None
            pending_approval_requests = None
            approval_decisions = None
        profile_b = None
        try:
            helper_path = args.profile_b_helper
            if helper_path is None:
                env_helper = os.environ.get("LIMA_OFFICE_PROFILE_B_HELPER")
                helper_path = Path(env_helper) if env_helper else None
            verifier = (
                PlatformHelperCeremonyVerifier(helper_path)
                if helper_path is not None
                else LocalhostWebAuthnVerifier()
            )
            profile_b = ProfileBSessionService(
                store,
                verifier=verifier,
                tenant_id=str(args.tenant_id),
                customer_context_id="customer-context-main",
            )
        except Exception:
            profile_b = None
        server = HarnessHTTPServer(
            ("127.0.0.1", args.ui_port),
            harness,
            ui,
            office_ui,
            supervisor_conversation,
            office_helper,
            task_proposals,
            approval_previews,
            operator_sessions,
            pending_approval_requests,
            approval_decisions,
            profile_b,
            profile_a_lab_enabled=not args.disable_profile_a_lab,
        )
        server.build_info = _build_info(args)
        if args.lifecycle_token_file:
            token = args.lifecycle_token_file.read_text(encoding="utf-8-sig").strip()
            if not re.fullmatch(r"[0-9a-f]{64}", token):
                raise ValueError("invalid lifecycle token")
            server.lifecycle_token = token
        host, port = server.server_address
        print(
            json.dumps(
                {
                    "status": "ready",
                    "url": f"http://{host}:{port}/",
                    "office_url": f"http://{host}:{port}/office",
                    "mode": harness.mode,
                    "working_ready": harness.working_ready,
                    "session_dir": str(args.session_dir),
                    "local_model_ready": harness.state()["local_model"]["ready"],
                    "api_version": "v1",
                    "loopback_only": True,
                    "profile_b_helper_configured": args.profile_b_helper is not None or bool(os.environ.get("LIMA_OFFICE_PROFILE_B_HELPER")),
                    "profile_a_lab_enabled": not args.disable_profile_a_lab,
                    "operator_authentication_manifest": False,
                    "production_ready": False,
                    "customer_pilot_allowed": False,
                }
            ),
            flush=True,
        )
        server.serve_forever(poll_interval=0.25)
        return 0
    except KeyboardInterrupt:
        return 0
    except _session.SessionError as exc:
        raise SystemExit(f"harness failed to start: {exc}") from exc
    finally:
        if server is not None:
            server.server_close()
        if store is not None:
            store.close()
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
