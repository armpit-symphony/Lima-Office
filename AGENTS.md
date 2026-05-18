# LIMA Office OS - Agent Instructions

## Project Mission

LIMA Office OS is a SparkPit Labs / LIMA AI Office project for small-business AI office operations.

The first viable deployment target is:

- 1 Supervisor Server
- 1-8 Arc Bot worker mini PCs
- Optional 1-4 helper agents on the supervisor side
- 1 customer/tenant at a time
- Guardian-gated actions
- Human approval for privileged or high-risk work
- LIMA IT tie-in for health checks, helpdesk triage, diagnostics, and approved remediation

This repository is not production-ready. Treat it as Phase 0 architecture, security, contracts, and planning until runtime foundations are explicitly approved.

## Core Architecture Rules

- Build LIMA Office as a governed office control plane, not a loose bundle of bots.
- Supervisor Server coordinates, routes, audits, corrects, and approves work.
- Arc worker nodes execute bounded office roles on mini PCs.
- Helper agents, when used, remain supervisor-side assistants with explicit scope and evidence requirements.
- Guardian must act as the syscall gate for model calls, tool calls, file mutations, network actions, outbound messages, connector access, and privileged operations.
- Every important action must produce evidence.
- No hidden background actions.
- No production claims.
- No live customer connectors until contracts and threat model exist.
- No marketing, pricing, financial projections, TAM, or sales copy unless explicitly requested.

## Guardian Syscall Gate Rules

Guardian is the required control point before any action leaves planning, drafting, or read-only analysis.

Guardian-gated surfaces include:

- Model calls and model routing
- Tool calls and tool-pack selection
- File reads, writes, deletes, and exports
- Network and browser access
- Connector access
- Outbound messages
- Privileged operations
- Scheduled or background work
- Secrets and token use
- LIMA IT diagnostics or remediation

Guardian decisions must classify the action, assign risk, enforce approval requirements, record evidence, and deny or quarantine unsafe work.

## Small-Business MVP Scope

Design for one small business at a time:

- One Supervisor Server on trusted business-owned infrastructure.
- 1-8 Arc Bot worker mini PCs with heartbeat, health, and quarantine state.
- Optional 1-4 helper agents attached to the supervisor, not free-running workers.
- Local-first operation where practical.
- Clear operator approvals for risky work.
- Read-only or draft-only behavior until contracts approve writes.
- LIMA IT integration as a future approved pathway for health checks, diagnostics, helpdesk triage, and remediation.

Avoid enterprise-scale assumptions, cross-tenant features, broad SaaS posture, unrestricted agent autonomy, or runtime implementation before contracts exist.

## Autonomy Boundaries

Allowed automatically:

- Summarize documents
- Classify tickets
- Draft emails or messages
- Prepare forms
- Gather diagnostics
- Update internal notes
- Suggest runbook steps
- Organize files
- Produce customer-service draft replies

Approval required:

- Send external email, text, or chat
- Submit forms
- Delete or overwrite files
- Modify customer records
- Install or update software
- Run remediation
- Access sensitive HR, finance, legal, or medical data
- Touch production servers
- Use payment, legal, or regulated systems

Blocked for MVP:

- Autonomous financial decisions
- Autonomous employee discipline or monitoring decisions
- Autonomous production server changes
- Cross-tenant memory sharing
- Hidden background actions
- Unrestricted browser, file, or network access

## Required Engineering Lenses

Use these lenses on every meaningful change:

1. Distributed systems software architect.
2. Security architect: Zero Trust, secrets, audit, least privilege.
3. SRE / Field IT engineer: deployment, observability, updates, rollback.
4. AI runtime engineer: model routing, local/cloud boundaries, tool-use safety.
5. Compliance/privacy reviewer: NIST CSF 2.0, NIST AI RMF, Zero Trust, Secure by Design.
6. Product scope guardian: small-business MVP, no overbuilding.

## Phase 0 Expected Outputs

Prefer docs and contracts before code.

Important files:

- `docs/ARCHITECTURE.md`
- `docs/MVP_SCOPE.md`
- `docs/ROADMAP.md`
- `docs/CONTRACTS.md`
- `docs/SECURITY_MODEL.md`
- `docs/THREAT_MODEL.md`
- `docs/WORKER_NODE_SPEC.md`
- `docs/SUPERVISOR_SPEC.md`
- `docs/AUTONOMY_BOUNDARIES.md`
- `docs/DECISIONS.md`
- `docs/OPEN_QUESTIONS.md`
- `docs/runbooks/`

## Done Criteria

Before finishing any task:

- Keep scope aligned to 1 Supervisor Server and 1-8 Arc workers.
- Confirm optional helper agents are bounded to supervisor-side support.
- Check for security implications.
- Check for autonomy-boundary violations.
- Update docs if architecture, contracts, or scope changed.
- Run available formatting/check commands.
- Run `git diff --check` if available.
- Report files changed, validation performed, blockers, and the next recommended step.
