# Arc Worker Control-Plane Smoke

This lab smoke proves the Arc-centered non-executing path:

```text
operator command
→ Supervisor request normalization
→ mandatory Guardian decision
→ LIMA governed decision
→ SQLite evidence
→ authenticated Arc assignment preview
→ Arc acknowledgement
→ operator-visible result
→ stop
```

It also performs authenticated Arc registration and heartbeat before routing.
The worker endpoint runs in a separate, explicit foreground process. The smoke
passes a process-local ephemeral channel key to that process once over stdin,
stores only its opaque key identifier, restarts the worker and Supervisor
evidence store, and deletes its temporary SQLite databases on exit.

## Prerequisites

- A clean LIMA Office checkout containing this runbook.
- A clean Arc-Bot-shell checkout containing `arc_bot_shell.control_plane`.
- Python 3.11 or newer.
- The exact dependencies from `requirements-dev.txt` and
  `requirements-lab.txt`.

## Command

From the LIMA Office repository:

```powershell
python scripts/arc-worker-control-plane-smoke.py `
  --arc-source C:\path\to\Arc-Bot-shell
```

## Required result

- Worker registration is authenticated and persisted.
- Heartbeat state is `healthy` and its sequence is persisted.
- Guardian returns a request-bound decision.
- LIMA reports `source_policy=guardian_core.policy`.
- Arc acknowledges one `document_read` assignment preview.
- Evidence contains request, Guardian, LIMA, assignment, and acknowledgement
  events.
- The Arc worker process restarts with a new boot ID and returns to `healthy`.
- The reopened Supervisor SQLite store retains the complete evidence chain and
  worker record.
- `runtime_authority_blocked=true`.
- `executable=false`.
- `execution_allowed=false`.
- `side_effects_allowed=false`.

## Boundaries

This smoke authorizes no model, provider, Ollama, tool, connector, outbound
message, customer credential, file mutation, approval execution, background
job, robotics, IoT, drone, or physical-world action.

The first endpoint is loopback-only. Private-LAN worker transport requires a
separate reviewed confidentiality and device-key provisioning design; do not
expose this HTTP endpoint to a public address.
