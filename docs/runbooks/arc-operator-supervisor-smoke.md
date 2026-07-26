# Arc Operator → Supervisor → Arc Smoke

This lab smoke proves the first real Arc-centered operator path:

```text
arc-preflight
→ authenticated foreground Supervisor
→ Supervisor-derived classification
→ mandatory Guardian decision
→ Guardian-backed LIMA decision
→ durable SQLite evidence
→ authenticated foreground Arc worker assignment preview
→ Arc acknowledgement
→ signed operator result
→ stop
```

The worker, Supervisor, and operator client run as separate processes. Both
ephemeral HMAC keys are provided only over stdin. The smoke verifies that
neither raw key nor its hexadecimal representation appears in any SQLite
database.

## Prerequisites

- This LIMA Office branch.
- The matching Arc branch containing `arc-preflight` and
  `arc-worker-preview`.
- Python 3.11 or newer.
- Exact lab dependencies from `requirements-lab.txt`.

## Command

```powershell
python scripts/arc-operator-supervisor-smoke.py `
  --arc-source C:\path\to\Arc-Bot-shell
```

## Required result

- Arc worker and Supervisor readiness records report foreground, loopback-only,
  non-executing state.
- The authenticated operator identity and tenant are bound by the operator
  channel.
- The request contains no caller-supplied action category or actor role.
- Guardian returns a request-bound decision.
- LIMA reports `source_policy=guardian_core.policy`.
- Arc acknowledges one assignment preview.
- The Supervisor refreshes and persists the authenticated heartbeat
  synchronously before the assignment preview.
- SQLite contains request, Guardian, LIMA, assignment, and acknowledgement
  evidence.
- An exact replay is denied.
- After Supervisor restart, a fresh request for the same safe-read operation is
  accepted and prior evidence remains.
- All runtime authority, execution, and side-effect flags remain false.

## Boundaries

Both HTTP listeners are loopback-only. Private-LAN deployment remains blocked
until confidentiality and durable device/operator key provisioning are
reviewed.

This smoke authorizes no model, provider, Ollama, tool, connector, outbound
message, customer credential, file mutation, approval execution, hidden
background job, robotics, IoT, drone, or physical-world action.
