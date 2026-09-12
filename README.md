# LIMA Office OS

LIMA Office OS is the SparkPit Labs / LIMA AI Office control-plane project for governed small-business AI office operations.

The repository now contains an attended, localhost-only Supervisor Console and
a Guardian-gated Arc integration for synthetic office-work testing. It remains
lab software, not a production business system. It does not authorize live
connectors, customer-data changes, external submissions, unrestricted worker
dispatch, hidden background actions, or production remediation.

## Current Lab Checkpoint: Profile A

Profile A (`attended_os_session_lab_only`) is selected temporarily while the
complete implemented LIMA Office and Arc workflow is tested on a personal PC.
It deliberately does not establish a named owner identity or MFA.

The current source provides:

- A business-owner Supervisor Console and Arc Lab UI on localhost.
- One attended, read-only Supervisor reasoning turn through the local
  ChatGPT/Codex subscription, with tools disabled and no prompt persistence.
- A deterministic helper for five fixed synthetic registration scenarios.
- Durable task drafts, tokenless approval previews, pending synthetic review
  requests, and non-authorizing deny/cancel/expire records.
- Guardian-gated evidence, exact-record checks, restart persistence, replay
  rejection, SOP gaps, and bounded escalation.
- Tested Supervisor operation with 1, 2, and 8 foreground Arc workers.
- One narrowly governed `document_read` capability when both Supervisor and Arc
  opt in and a fixed document root is supplied at startup.

Positive approval, approval tokens, execution bindings, general Arc dispatch,
external sends, form submission, connectors, and customer-record mutation are
still blocked. See the [Profile A whole-system lab test](docs/audits/PROFILE_A_WHOLE_SYSTEM_LAB_TEST.md)
and [local project logbook](limaoffice-logbook.md).

## Physical-PC Test Harness UI

The first bounded operator UI now runs one Arc worker and one Supervisor on
loopback with explicit **Training** and **Working** modes:

```powershell
python scripts\arc-runtime-harness.py `
  --arc-source C:\path\to\Arc-Bot-shell `
  --session-dir C:\path\to\lima-profile-a-session `
  --ui-port 8767
```

Open `http://127.0.0.1:8767/office/` for LIMA Office or
`http://127.0.0.1:8767/` for the Arc Lab. The safe default above starts in
Training mode with execution disabled.

Training is the startup default and persists reviewed SOP instructions.
Working mode remains unavailable unless both independent execution opt-ins and
the bounded document root were supplied at startup. Its only executable
capability is the existing Guardian-gated `document_read` path. Outcome routing,
SOP gaps, training progress, and sanitized evidence are authoritative on the
LIMA Office side, not in browser storage.

See [the Arc physical runtime test harness](docs/ARC_RUNTIME_HARNESS.md).

The coordinated Windows preview builder and attended operator instructions are
in [release/lab-preview](release/lab-preview/README.md). A built artifact remains
a local lab candidate until its clean-install smoke passes and publication is
explicitly approved.

The latest published package is the
[v0.1.0-lab.5 GitHub prerelease](https://github.com/armpit-symphony/Lima-Office/releases/tag/v0.1.0-lab.5).
The Profile A checkpoint described above is newer source work and is not a new
published package. Lab.5 remains localhost-only and not production-ready.

## Running a governed session

One command brings up an Arc worker and a Supervisor and takes repeated
requests at a prompt:

```bash
python scripts/arc-office-session.py --arc-source /path/to/Arc-Bot-shell   --document-root /path/to/documents   --execution-opt-in --execute-granted-capability --emit-document-content
```

Both opt-ins are off unless passed, and the launcher hands them to the
processes that own them rather than deciding anything itself. See
[docs/ARC_OFFICE_SESSION.md](docs/ARC_OFFICE_SESSION.md), which also covers a
trap worth knowing: `resource_type` is enumerated by contract and `document`
is not a member, so a document is a `file`.

## When a request is denied

A denied request is not one thing, and the difference decides whether a shell
may correct it, retry it, escalate it, or must stop. The escalation ladder is
automated up to the Human rung, so escalating a policy denial to a higher
machine is authority shopping — the same failure as auto-retry with a different
decider.

Reason codes therefore carry a disposition: `forbidden`, `escalatable`,
`correctable`, or `retry_with_fresh_decision`. Unclassified codes are
`forbidden`, so a denial nobody has classified stops rather than looping. See
[docs/DENIAL_ROUTING.md](docs/DENIAL_ROUTING.md), which also sets the boundary
between the ladder a customer configures and the denials only the system may
classify.

## Training Arc toward doing the job alone

Arc bot is fed SOP and trained until it can do its job accurately on its own,
so every shortfall is a fact about what it has not been taught yet. Denials
Arc can be taught past become SOP gaps; an operator can also author SOP
directly, teaching Arc a job before it fails at one.

Denials that exist to stop something never become gaps. Teaching Arc past a
`forbidden` denial would be teaching it to defeat a control, so that record is
refused rather than merely discouraged. `autonomy_rate` — the share of
attempts Arc finished with nobody else involved — is the measure of whether
training is working. See [docs/SOP_TRAINING.md](docs/SOP_TRAINING.md).

## Working a queue of tasks

A task manager queues jobs; Arc works them through the real governed path, and
what comes back decides whether the task finished, retries at the same rung,
climbs to the next, or stops. Retries are bounded, a rung that receives an
escalation starts with a full budget, and at the last rung the task waits for
the person rather than moving. See [docs/TASK_SEAM.md](docs/TASK_SEAM.md), and
`scripts/arc-task-seam-smoke.py` to watch it against real processes.

## What LIMA Office OS Is

LIMA Office OS is intended to coordinate guarded AI office work for one small business at a time. It is designed around:

- A main Supervisor Server.
- 1-8 Arc Bot worker mini PCs.
- Optional 1-4 supervisor-side helper agents.
- Guardian-gated model, tool, file, network, connector, outbound, scheduled, and privileged actions.
- Human approval for high-risk or privileged work.
- Evidence capture for important actions and decisions.
- Future LIMA IT handoff for health checks, diagnostics, helpdesk triage, and approved remediation.

## Small-Business MVP

The first lab MVP is 1 Supervisor Server with 1-3 Arc workers. The design path extends to 1-8 workers for one tenant/customer at a time.

MVP capabilities are documentation-first until explicitly approved:

- Worker registration.
- Worker heartbeat and health status.
- Worker capability manifest.
- Task assignment and status reporting.
- Guardian risk tiering.
- Manual approval tokens plus mock approval binding for privileged-task
  metadata.
- Evidence capture.
- Quarantine and revoke states.
- Basic operator dashboard specification.
- Mock connector readiness states.

## Supervisor Server And Arc Worker Nodes

The Supervisor Server is the control plane. It owns orchestration, worker registry, task routing, policy checks, approval workflow, model routing policy, audit/evidence ledger, tenant memory boundaries, helper-agent boundaries, operator status, and LIMA IT bridge posture.

Arc worker nodes are mini PCs that execute bounded office roles. A worker declares capabilities, receives scoped tasks, reports heartbeat and status, captures evidence, and can be quarantined or revoked. Workers must not receive unrestricted tool, file, browser, network, connector, or memory access.

Optional helper agents run on the supervisor side only. They can assist with memory review, file organization, background review, or LIMA IT triage preparation, but they must remain scoped, visible, logged, and Guardian-gated.

## Guardian Governance

Guardian is the syscall gate. Every model call, tool call, file mutation, network action, outbound message, connector action, scheduled action, and privileged operation must pass through Guardian classification, policy, approval checks, and evidence capture.

Automatic work means no human approval is required. It does not mean Guardian is bypassed.

Privileged and high-risk actions require human approval. MVP-blocked actions remain denied.

## LIMA IT Future Tie-In

LIMA Office OS should later integrate with LIMA IT for PC, server, and network support. Phase 0 only documents handoff boundaries for:

- Health checks.
- Diagnostics.
- Helpdesk triage.
- Security incident context.
- Approved remediation requests.

No remediation runtime, endpoint control, production server change, or network change is implemented in this repo.

## Core Docs

- [Current status](STATUS.md)
- [Canonical baseline](docs/BASELINE.md)
- [Major baseline stabilization review](docs/MAJOR_BASELINE_STABILIZATION_REVIEW.md)
- [Docs index](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [MVP scope](docs/MVP_SCOPE.md)
- [Roadmap](docs/ROADMAP.md)
- [Contracts](docs/CONTRACTS.md)
- [Cross-contract invariants](docs/CROSS_CONTRACT_INVARIANTS.md)
- [Approval token runtime binding](docs/APPROVAL_TOKEN_RUNTIME_BINDING.md)
- [Security model](docs/SECURITY_MODEL.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Worker node spec](docs/WORKER_NODE_SPEC.md)
- [Supervisor spec](docs/SUPERVISOR_SPEC.md)
- [Autonomy boundaries](docs/AUTONOMY_BOUNDARIES.md)
- [Decisions](docs/DECISIONS.md)
- [Open questions](docs/OPEN_QUESTIONS.md)
- [Phase 1A runtime scaffolding](docs/PHASE_1A_RUNTIME_SCAFFOLDING.md)
- [Phase 0 / Phase 1A closeout](docs/PHASE_0_1A_CLOSEOUT.md)
- [Next phase plan](docs/NEXT_PHASE_PLAN.md)
- [Runtime boundaries](docs/RUNTIME_BOUNDARIES.md)
- [Validation evidence](docs/VALIDATION_EVIDENCE.md)
- [Worker deployment blueprint](docs/deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)
- [Governance policy details](docs/governance/README.md)
- [Operator console UX spec](docs/ux/OPERATOR_CONSOLE_SPEC.md)
- [Runbooks](docs/runbooks/)
- [Arc worker control-plane smoke](docs/runbooks/arc-worker-control-plane-smoke.md)
- [Arc operator → Supervisor → Arc smoke](docs/runbooks/arc-operator-supervisor-smoke.md)

## Current Repository Status

The public default branch contains the lab.5 integration baseline. This
checkpoint adds the tested Profile A Supervisor workflow while retaining these
boundaries:

- Contracts and Guardian checks precede every important runtime action.
- The implemented runtime is attended, loopback-only, synthetic-data-only lab
  software with durable local evidence.
- The Supervisor Console exists, but it cannot issue positive approval or
  dispatch general office work to Arc.
- The OpenAI subscription route is one-turn, read-only, ephemeral, and has all
  tools disabled.
- There are no live customer connectors, external sends, browser writes,
  OAuth/provider wiring, customer-system mutations, or remediation execution.
- Profile B or C identity controls, threat review, clean packaging, and another
  release gate are required before any customer or production claim.
