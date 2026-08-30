#!/usr/bin/env python3
"""Run the localhost Arc physical-PC test harness and operator UI."""

from __future__ import annotations

import importlib.util
import json
import os
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



MAX_REQUEST_BYTES = 64 * 1024


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
    ) -> None:
        self.harness = harness
        self.ui = ui
        super().__init__(address, HarnessRequestHandler)


class HarnessRequestHandler(BaseHTTPRequestHandler):
    server: HarnessHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("arc-harness: " + (format % args) + "\n")

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
        )
        self.end_headers()

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(body))
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

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._headers(200, "text/html; charset=utf-8", len(self.server.ui))
            self.wfile.write(self.server.ui)
            return
        if self.path == "/api/state":
            self._json(200, self.server.harness.state())
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
        if not self._origin_allowed():
            self._json(403, {"error": "origin_not_allowed"})
            return
        try:
            payload = self._read_json()
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
        except HarnessBoundaryError as exc:
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
        server = HarnessHTTPServer(("127.0.0.1", args.ui_port), harness, ui)
        host, port = server.server_address
        print(
            json.dumps(
                {
                    "status": "ready",
                    "url": f"http://{host}:{port}/",
                    "mode": harness.mode,
                    "working_ready": harness.working_ready,
                    "session_dir": str(args.session_dir),
                    "local_model_ready": harness.state()["local_model"]["ready"],
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
