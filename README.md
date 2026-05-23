# LIMA Office OS

LIMA Office OS is the SparkPit Labs / LIMA AI Office control-plane project for governed small-business AI office operations.

The repo is currently Phase 1A mock runtime scaffolding on top of Phase 0 architecture, security, contracts, and planning. It is not production-ready. It does not contain live connectors, runtime dispatch, hidden background jobs, approval enforcement for live actions, production server control, or customer-system mutation.

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
- Manual approval tokens for privileged tasks.
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
- [Docs index](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [MVP scope](docs/MVP_SCOPE.md)
- [Roadmap](docs/ROADMAP.md)
- [Contracts](docs/CONTRACTS.md)
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
- [Worker deployment blueprint](docs/deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)
- [Governance policy details](docs/governance/README.md)
- [Operator console UX spec](docs/ux/OPERATOR_CONSOLE_SPEC.md)
- [Runbooks](docs/runbooks/)

## Current Repo Status

This repo is Phase 1A mock runtime scaffolding only:

- Docs and scaffolding are allowed.
- Contracts are required before implementation.
- Mock in-memory worker, heartbeat, task, Guardian, and evidence flows are allowed.
- Governance policy details are docs/contracts scaffolding only.
- Operator console UX specs are docs/contracts scaffolding only; no frontend code exists.
- No production-readiness claims.
- No live customer connectors.
- No live runtime behavior beyond the tiny in-memory scaffold.
- No external sends, external model APIs, browser automation, OAuth/provider wiring, or remediation execution.
- No marketing, pricing, financial projections, TAM, investor content, or sales copy.
