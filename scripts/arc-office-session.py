#!/usr/bin/env python3
"""One command that brings up a governed Arc office session.

Running the lab by hand means three terminals, two ephemeral keys pasted on
stdin in the right order, and ports copied out of readiness JSON — per request.
That is fine for proving the path and useless for actually working in it.

This starts the Arc worker and the Supervisor, holds the ephemeral keys for the
life of the session, and takes repeated requests at a prompt.

What it deliberately does not do:

* It does not weaken either gate. Both opt-ins are still off unless passed, and
  they are passed through to the processes that own them rather than being
  decided here.
* It does not print, log, or persist a channel key.
* It does not perform any read itself. Every request runs through the real Arc
  operator CLI against the real Supervisor, so a session behaves exactly like
  the hand-run path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import uuid


OFFICE_ROOT = Path(__file__).resolve().parents[1]

# resource_type is enumerated by the guardian.decision contract. A document is
# a "file"; "document" is not a member and a request using it is denied before
# Guardian ever produces a decision, with the unhelpful reason code
# recon_missing_guardian_decision.
DOCUMENT_RESOURCE_TYPE = "file"
WORKER_RESOURCE_TYPE = "worker_status"

PROMPT = "arc> "
HELP = """\
Commands:
  read <path>       Governed document read. Prints the text when this session
                    was started with both opt-ins and a document root.
  status            Read-only worker status request.
  info              Show session identities, ports, and gate settings.
  help              This text.
  quit / exit       Stop the worker and the Supervisor and leave.

<path> is relative to the session document root."""


class SessionError(RuntimeError):
    """Something went wrong bringing the session up."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Start one governed Arc office session: a foreground Arc worker, a "
            "foreground Supervisor, and a prompt that takes repeated requests."
        )
    )
    parser.add_argument("--arc-source", type=Path, required=True)
    parser.add_argument("--tenant-id", default="tenant-lab-001")
    parser.add_argument("--customer-context-id", default="customer-context-main")
    parser.add_argument("--operator-id", default="operator-lab-001")
    parser.add_argument("--operator-key-id", default="operator-key-001")
    parser.add_argument("--worker-id", default="arc-worker-001")
    parser.add_argument("--worker-key-id", default="worker-key-001")
    parser.add_argument("--policy-version", default="guardian-policy-lab-v1")
    parser.add_argument(
        "--session-dir",
        type=Path,
        default=None,
        help=(
            "Where replay and evidence databases live. A temporary directory "
            "is used and removed on exit when this is not given."
        ),
    )
    parser.add_argument(
        "--document-root",
        type=Path,
        default=None,
        help="Directory a granted document_read may read from.",
    )
    parser.add_argument(
        "--execution-opt-in",
        action="store_true",
        help=(
            "Supervisor opt-in: allow it to issue execution grants at all. Off "
            "unless passed."
        ),
    )
    parser.add_argument(
        "--execute-granted-capability",
        action="store_true",
        help=(
            "Arc opt-in: allow Arc to honour a grant it receives. Off unless "
            "passed. Both opt-ins are required before anything runs."
        ),
    )
    parser.add_argument(
        "--emit-document-content",
        action="store_true",
        help="Show document text for granted reads. Off unless passed.",
    )
    return parser


def _stop(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _readiness(process: subprocess.Popen[str], label: str) -> dict[str, Any]:
    if process.stdout is None:
        raise SessionError(f"{label} stdout is unavailable")
    line = process.stdout.readline()
    if not line:
        stderr = process.stderr.read() if process.stderr else ""
        raise SessionError(f"{label} did not report readiness\n{stderr.strip()}")
    try:
        ready = json.loads(line)
    except json.JSONDecodeError as exc:
        raise SessionError(f"{label} readiness record is not valid JSON") from exc
    if ready.get("status") != "ready":
        raise SessionError(f"{label} did not come up ready")
    if ready.get("executable") is not False:
        # A component claiming it can execute has failed its own boundary, so
        # the session refuses to continue rather than trusting it.
        raise SessionError(f"{label} reported an executable boundary")
    if not isinstance(ready.get("port"), int) or ready["port"] < 1:
        raise SessionError(f"{label} reported an invalid port")
    return ready


class ArcOfficeSession:
    """Owns the worker, the Supervisor, and the ephemeral keys."""

    def __init__(self, args: argparse.Namespace, session_dir: Path) -> None:
        self.args = args
        self.session_dir = session_dir
        # Generated here and never written down. They exist for the life of
        # this process and reach the children only on stdin.
        self._operator_key = secrets.token_bytes(32)
        self._worker_key = secrets.token_bytes(32)
        self.worker: subprocess.Popen[str] | None = None
        self.supervisor: subprocess.Popen[str] | None = None
        self.worker_port: int | None = None
        self.supervisor_port: int | None = None
        self._request_count = 0

    # -- lifecycle ----------------------------------------------------

    def start(self) -> None:
        self.worker = self._start_worker()
        ready = _readiness(self.worker, "Arc worker")
        self.worker_port = ready["port"]

        self.supervisor = self._start_supervisor()
        ready = _readiness(self.supervisor, "Supervisor")
        self.supervisor_port = ready["port"]

    def close(self) -> None:
        for process in (self.supervisor, self.worker):
            _stop(process)

    def _start_worker(self) -> subprocess.Popen[str]:
        process = subprocess.Popen(
            [
                sys.executable, "-m", "arc_bot_shell.control_plane.cli",
                "--host", "127.0.0.1", "--port", "0",
                "--tenant-id", self.args.tenant_id,
                "--customer-context-id", self.args.customer_context_id,
                "--worker-id", self.args.worker_id,
                "--worker-role", "general_office_arc_worker",
                "--worker-version", "arc-bot-shell-0.1.0",
                "--boot-id", f"boot-session-{uuid.uuid4().hex[:8]}",
                "--key-id", self.args.worker_key_id,
                "--policy-version", self.args.policy_version,
                "--capability", "document_read",
                "--capability", "it_diagnostics_read_only",
                "--replay-db", str(self.session_dir / "worker-replay.db"),
                "--channel-key-stdin",
            ],
            cwd=self.args.arc_source,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._feed(process, [self._worker_key])
        return process

    def _start_supervisor(self) -> subprocess.Popen[str]:
        command = [
            sys.executable, "-m", "lima_office.supervisor.cli",
            "--host", "127.0.0.1", "--port", "0",
            "--tenant-id", self.args.tenant_id,
            "--customer-context-id", self.args.customer_context_id,
            "--operator-id", self.args.operator_id,
            "--operator-key-id", self.args.operator_key_id,
            "--worker-id", self.args.worker_id,
            "--worker-key-id", self.args.worker_key_id,
            "--worker-url", f"http://127.0.0.1:{self.worker_port}",
            "--evidence-db", str(self.session_dir / "supervisor.db"),
            "--policy-version", self.args.policy_version,
            "--operator-key-stdin", "--worker-key-stdin",
        ]
        if self.args.execution_opt_in:
            command.append("--execution-opt-in")
        process = subprocess.Popen(
            command,
            cwd=OFFICE_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._feed(process, [self._operator_key, self._worker_key])
        return process

    @staticmethod
    def _feed(process: subprocess.Popen[str], keys: list[bytes]) -> None:
        if process.stdin is None:
            _stop(process)
            raise SessionError("foreground process stdin is unavailable")
        for key in keys:
            process.stdin.write(key.hex() + "\n")
        process.stdin.flush()
        process.stdin.close()

    # -- requests -----------------------------------------------------

    def _alive(self) -> None:
        for label, process in (
            ("Arc worker", self.worker),
            ("Supervisor", self.supervisor),
        ):
            if process is None or process.poll() is not None:
                raise SessionError(f"{label} is no longer running")

    def request(self, *, action: str, resource_type: str, resource_id: str) -> str:
        """Run one real operator request and return the CLI's raw output."""

        self._alive()
        self._request_count += 1
        tag = f"{uuid.uuid4().hex[:8]}-{self._request_count}"
        command = [
            sys.executable, "-m", "arc_bot_shell.control_plane.operator_cli",
            "--supervisor-url", f"http://127.0.0.1:{self.supervisor_port}",
            "--tenant-id", self.args.tenant_id,
            "--customer-context-id", self.args.customer_context_id,
            "--operator-id", self.args.operator_id,
            "--operator-key-id", self.args.operator_key_id,
            "--worker-id", self.args.worker_id,
            "--action", action,
            "--resource-type", resource_type,
            "--resource-id", resource_id,
            "--request-id", f"request-{tag}",
            "--idempotency-key", f"idem-{tag}",
            "--policy-version", self.args.policy_version,
            "--replay-db", str(self.session_dir / "operator-replay.db"),
            "--operator-key-stdin",
        ]
        if self.args.execute_granted_capability:
            command.append("--execute-granted-capability")
        if self.args.document_root is not None:
            command += ["--document-root", str(self.args.document_root)]
        if self.args.emit_document_content:
            command.append("--emit-document-content")

        completed = subprocess.run(
            command,
            cwd=self.args.arc_source,
            input=self._operator_key.hex() + "\n",
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return f"request failed\n{completed.stderr.strip()}"
        return completed.stdout


def _summarize(output: str) -> str:
    """Turn one operator result into something readable at a prompt."""

    payload, marker, content = output.partition("--- BEGIN DOCUMENT CONTENT")
    try:
        result = json.loads(payload)
    except json.JSONDecodeError:
        return output.strip()

    execution = result.get("execution") or {}
    grant = result.get("execution_grant")

    # The Supervisor's own outcome comes first. Reporting only Arc's reason
    # code hides the real cause: a request denied upstream shows up here as
    # "execution_grant_absent", which points at the wrong gate entirely.
    lines = [f"  status     : {result.get('status')}"]
    reason_codes = result.get("reason_codes") or []
    if reason_codes:
        lines.append(f"  denied for : {', '.join(reason_codes)}")
    lines.append(f"  grant      : {'issued' if isinstance(grant, dict) else 'none'}")
    lines.append(f"  performed  : {execution.get('performed')}")
    if execution.get("performed"):
        lines.append(f"  bytes      : {execution.get('byte_count')}")
        lines.append(f"  capability : {execution.get('capability')}")
    reason = execution.get("reason_code") or execution.get("content_reason_code")
    if reason:
        lines.append(f"  reason     : {reason}")
    # Always restate the invariant: a decision never authorizes execution.
    lines.append(f"  side effects: {execution.get('side_effects_performed', False)}")

    if marker:
        body = content.split("---", 1)[-1].lstrip("- \n")
        body = body.rsplit("--- END DOCUMENT CONTENT ---", 1)[0]
        lines.append("")
        lines.append(body.rstrip("\n"))
    return "\n".join(lines)


def _info(session: ArcOfficeSession) -> str:
    args = session.args
    return "\n".join(
        [
            f"  tenant        : {args.tenant_id}",
            f"  worker        : {args.worker_id} on 127.0.0.1:{session.worker_port}",
            f"  supervisor    : 127.0.0.1:{session.supervisor_port}",
            f"  session dir   : {session.session_dir}",
            f"  document root : {args.document_root or 'not configured'}",
            f"  supervisor opt-in : {args.execution_opt_in}",
            f"  arc opt-in        : {args.execute_granted_capability}",
            f"  show content      : {args.emit_document_content}",
        ]
    )


def _repl(session: ArcOfficeSession) -> int:
    print("Governed Arc office session ready. 'help' for commands.")
    print(_info(session))
    while True:
        try:
            raw = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        command, _, argument = raw.partition(" ")
        command = command.lower()
        argument = argument.strip()

        if command in {"quit", "exit"}:
            return 0
        if command == "help":
            print(HELP)
            continue
        if command == "info":
            print(_info(session))
            continue

        try:
            if command == "read":
                if not argument:
                    print("usage: read <path>")
                    continue
                output = session.request(
                    action="safe_read",
                    resource_type=DOCUMENT_RESOURCE_TYPE,
                    resource_id=argument,
                )
            elif command == "status":
                output = session.request(
                    action="status",
                    resource_type=WORKER_RESOURCE_TYPE,
                    resource_id=session.args.worker_id,
                )
            else:
                print(f"unknown command {command!r}. 'help' for commands.")
                continue
        except SessionError as exc:
            print(f"session ended: {exc}")
            return 1
        print(_summarize(output))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    arc_source = args.arc_source.resolve()
    if not (arc_source / "arc_bot_shell" / "control_plane").is_dir():
        raise SystemExit("Arc source lacks the control-plane package")
    args.arc_source = arc_source
    if args.document_root is not None:
        args.document_root = args.document_root.resolve()
        if not args.document_root.is_dir():
            raise SystemExit("document root is not a directory")

    temporary = args.session_dir is None
    session_dir = (
        Path(tempfile.mkdtemp(prefix="arc-office-session-"))
        if temporary
        else args.session_dir.resolve()
    )
    session_dir.mkdir(parents=True, exist_ok=True)

    session = ArcOfficeSession(args, session_dir)
    try:
        session.start()
        return _repl(session)
    except SessionError as exc:
        raise SystemExit(f"session failed to start: {exc}") from exc
    finally:
        session.close()
        if temporary:
            shutil.rmtree(session_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
