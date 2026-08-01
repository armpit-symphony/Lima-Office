# Arc Multi-Worker Supervisor Smoke

This lab smoke proves that the same foreground, non-executing control-plane path
works with two and eight separate Arc worker processes:

```text
Arc operator preflight
→ one foreground Supervisor
→ mandatory Guardian
→ Guardian-backed LIMA decision
→ synchronous authenticated worker heartbeat
→ durable SQLite evidence
→ one selected Arc assignment preview
→ Arc acknowledgement
→ stop
```

No worker executes the requested action.

## Prerequisites

- This LIMA Office branch.
- The matching Arc branch containing `arc-preflight` and
  `arc-worker-preview`.
- Python 3.11 or newer.
- Exact lab dependencies from `requirements-lab.txt`.

## Commands

```powershell
python scripts/arc-multi-worker-supervisor-smoke.py `
  --arc-source C:\path\to\Arc-Bot-shell `
  --worker-count 2

python scripts/arc-multi-worker-supervisor-smoke.py `
  --arc-source C:\path\to\Arc-Bot-shell `
  --worker-count 8
```

## Required evidence

For each run:

- The Supervisor readiness record contains exactly the requested worker count.
- Every worker is a separate foreground Arc process.
- Every worker receives one real authenticated, non-executing assignment
  preview and acknowledges it.
- A Supervisor restart restores the complete durable worker inventory.
- The final worker process is disconnected after restart.
- A request for that worker fails closed as `blocked` with `worker_stale`.
- The disconnected worker's durable state becomes `offline`.
- A subsequent request to another worker is still acknowledged.
- The offline path contains `worker_heartbeat` followed by `denial` evidence.
- No raw or hex-encoded channel key appears in Supervisor, operator, or Arc
  SQLite databases.
- Every runtime-authority, execution, and side-effect flag remains false.

## Boundaries

All listeners are loopback-only. The smoke starts no scheduler or hidden
background process. Private-LAN transport remains blocked until confidentiality,
mutual device identity, revocation, and durable key provisioning are reviewed.

This smoke authorizes no model, provider, Ollama, tool, connector, outbound
message, customer credential, file mutation, approval execution, robotics, IoT,
drone, or physical-world action.
