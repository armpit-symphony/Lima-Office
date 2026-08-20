# Arc physical runtime test harness

Status: bounded physical-PC test lane. Not production-ready.

The runtime harness starts one real Arc worker, one real LIMA Office
Supervisor, and a localhost-only operator UI. It is the first usable bridge
between the proven governed document path and the SOP/outcome-routing
stack.

## Start it on Windows

Use the repository-specific LIMA Office virtual environment. Choose a document
root that contains test documents only and no credentials, recovery codes, or
customer secrets.

```powershell
cd C:\LIMA\Lima-Office
.\.venv\Scripts\python.exe scripts\arc-runtime-harness.py `
  --arc-source C:\LIMA\Arc-Bot-shell `
  --document-root C:\path\to\safe-test-documents `
  --execution-opt-in `
  --execute-granted-capability `
  --emit-document-content
```

The launcher prints one JSON readiness record containing the loopback URL,
normally `http://127.0.0.1:8765/`. It does not open a browser or expose the
server to the LAN.

## Two modes

### Training mode

Training is the startup default and has no work-execution endpoint available
through the controller. An operator can enter a reviewed SOP instruction for a
named task. LIMA Office validates and persists it as an `operator_authored`
`SopGap` record.

An SOP instruction cannot override Guardian, change a denial disposition, or
turn a `forbidden` reason into permission. Training records are instructions
for correctable work, not authority.

### Working mode

Working mode is refused unless all of these were fixed at process startup:

1. Supervisor `--execution-opt-in`.
2. Arc `--execute-granted-capability`.
3. A bounded `--document-root`.

The only working capabilities exposed by this harness are bounded
`document_list` and `document_read`. Each request travels through the
existing real operator CLI, Supervisor classification, Guardian decision,
single-use LIMA grant, and Arc grant-consumption path. A list is non-recursive
and returns at most 200 visible, non-symlink names with type and file size. It
returns no content or absolute paths. The harness controller neither lists the
directory nor reads the file itself.

Every returned result is handed to `route_task_outcome`. Correctable denials
open a durable SOP gap and escalate without blind retry. Successful work raises
the measured autonomy rate. Browser state is never the product source of truth.

## Durable state and evidence

The harness stores:

- SOP gap records and reviewed instructions;
- completed-alone and stopped-short counters;
- sanitized mode transitions, status checks, and routed outcome events.

It does not store returned document content in its event ledger. The underlying
Supervisor retains its existing evidence database.

Default harness state is outside the repository:

- Windows: `%LOCALAPPDATA%\ArcBot\runtime-harness`
- Linux: `$XDG_DATA_HOME/arc-bot-shell/runtime-harness`, or
  `~/.local/share/arc-bot-shell/runtime-harness`
- Override: `ARC_BOT_DATA_DIR`

Pass `--session-dir` to select an explicit test-state directory.

## Security boundary

- Listener is hard-coded to `127.0.0.1`.
- POST requests accept JSON only, cap bodies at 64 KiB, and reject foreign
  browser origins.
- Absolute paths, Windows drive paths, and `..` traversal are rejected before
  the Arc request is sent. Arc independently enforces document-root
  containment, its 1 MiB read cap, and its 200-entry listing cap. Hidden
  directories are not listable; hidden entries, symlinks, special files, and
  control-character names are excluded.
- Ephemeral channel keys remain process memory only and reach child processes
  on stdin. They are not returned to the UI or stored in the harness database.
- Connector writes, external sends, file mutation, unrestricted network
  egress, remediation, and device/robotics control are not routed.
- Mode changes and work outcomes create evidence events. There are no hidden
  background actions.

The loopback UI has no operator authentication layer yet. That is acceptable
only for a locally attended lab PC. Do not bind it to a LAN interface, reverse
proxy it, or treat it as a customer deployment.

## Stop and recovery

Press `Ctrl+C` in the launcher terminal. The HTTP server, Supervisor, and Arc
worker are closed. On restart, mode resets to Training; durable SOP/evidence
state remains.

If a child process fails, the controller refuses new requests. Restart the
harness and inspect the terminal plus the selected session directory. Do not
delete evidence to make a failed test look clean.

## Operator IDE wiring

The default UI is now the Arc-owned operator IDE. It reads Arc's existing
JSONL task and approval stores through an Arc adapter rather than copying queue
state into LIMA Office. Arc's existing selector explains whether the next task
is new work or a blocked task whose answer arrived.

An approved Arc v0.6 record remains evidence-only
(`execution_allowed=false`). The IDE can record the human decision and use it
as a queue-resolution signal, but it cannot issue a Supervisor execution grant
or bypass Guardian. An instructed Office SOP gap supplies the same explicit
resolution signal by task reference.

Training mode also accepts a customer escalation ladder. LIMA Office validates
the existing structural invariants before replacing the durable configuration:
system-manager and executive failsafes must exist, and a terminal human must
decide everything reaching the last rung.

Returned document content is divided into 8,000-character pages. At most four
document buffers remain in process memory, never in the harness SQLite event
ledger, and all buffers are cleared when the operator returns to Training mode.

Use `--task-queue-path` and `--approval-path` to point the IDE at explicit
Arc JSONL stores. Without them it uses Arc's standard local artifact paths.

## What this does not make ready

This IDE is not a task-packet editor, local-model execution surface, connector
console, outbound-action console, operator-authenticated network service, or
multi-worker fleet controller. Those remain later bounded slices.
