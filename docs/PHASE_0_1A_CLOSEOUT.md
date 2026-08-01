# Phase 0 / Phase 1A Closeout Archive

This archive captures the LIMA Office OS baseline at the close of Phase 0 and
the reachable Phase 1A mock runtime scaffolding checkpoint. It is a checkpoint
only. It does not approve live connectors, external sends, real remediation,
external model provider calls, browser automation, durable services, production
systems, or customer data operations.

Date: 2026-05-22

Closeout branch: `phase-0-1a-closeout-archive`

Available local baseline: `phase-1a-runtime-scaffolding` at `d259409`

Task-provided later baseline: `phase-1a-cross-contract-invariants` at
`e71431007ddbe96c3e141b77591efc2508c53e5d`

Repository evidence note: the task-provided cross-contract invariant commit was
not reachable from local refs, advertised `origin` refs, PR refs, or a direct
fetch by SHA during the original closeout. A 2026-05-22 reconciliation check
after `git fetch --all --prune` again found that the local object is absent and
`origin` does not advertise `phase-1a-cross-contract-invariants`. Any statement
about that branch is therefore recorded as an expected checkpoint input, not as
validated repository evidence. Runtime expansion remains blocked until that
source is pushed, restored, recreated, or formally superseded.

## Timeline

| Branch / commit | What it added | Closeout state |
| --- | --- | --- |
| `roadmap-lima-office-control-plane` / `22b4d04` | Initial control-plane roadmap for LIMA Office. | Historical planning baseline. |
| `phase-0-architecture-contracts-roadmap` / `ba665f8` | Phase 0 architecture, governance, MVP scope, roadmap, security, threat model, supervisor/worker specs, decisions, open questions, and initial runbooks. | Accepted Phase 0 architecture baseline. |
| `phase-0-contract-schemas` / `761c393` | Versioned v1 contract schemas and sanitized examples for worker lifecycle, heartbeat, task execution, Guardian decisions, approvals, connector trust, evidence, incidents, SLOs, and LIMA IT handoff. | Accepted contracts-first baseline. |
| `phase-0-policy-runbook-hardening` / `64de3f0` | Policy and runbook hardening for approval tokens, evidence writer failure, prompt injection, worker quarantine/re-enrollment, retention/redaction, and LIMA IT handoff. | Accepted policy/runbook baseline. |
| `phase-0-schema-conditionals-followups` / `fd5421d` | JSON Schema conditional hardening and follow-up contracts for approval results, token verification, helper scope, taint refs, model routing, tool invocation, memory access, evidence failure, and LIMA IT denial examples. | Accepted schema hardening baseline. |
| `phase-0-ci-schema-validation` / `0be4ced` | Strict schema validation, doc link checks, CI workflow, unsafe-content scan, and validation docs. | Accepted validation/CI baseline. |
| `phase-1a-runtime-scaffolding` / `d259409` | Mock in-memory Python runtime scaffolding, runtime contract loading/validation, default-deny Guardian policy stub, worker registry, heartbeat validation, task queue, evidence writer, and unit tests. | Available local Phase 1A runtime baseline. |
| `phase-1a-cross-contract-invariants` / `e71431007ddbe96c3e141b77591efc2508c53e5d` | Expected cross-contract invariant hardening checkpoint based on the task input. | Reconciliation on 2026-05-22 found no local commit object and no `origin` branch; remains a closeout evidence blocker until pushed, restored, recreated, or formally superseded. |

## Architecture Baseline

LIMA Office OS is a governed office control plane for one small business tenant
at a time. The target remains one Supervisor Server and 1-8 Arc worker mini PCs,
with optional 1-4 supervisor-side helper agents.

The baseline planes are:

- Control Plane: supervisor orchestration, task routing, approval posture,
  worker registry, health status, evidence references, and operator reporting.
- Worker Plane: Arc mini PCs with bounded roles, scoped task assignments,
  heartbeat, status, evidence, quarantine, and revoke behavior.
- Guardian Plane: mandatory syscall gate for model calls, tools, file mutation,
  network, connectors, outbound messages, scheduled work, secrets, and
  privileged operations.
- Data Plane: task metadata, tenant-scoped memory refs, worker status, approval
  records, evidence artifacts, redaction, retention, export, delete, and
  customer exit posture.
- Connector Plane: mock/readiness-only in the current baseline.
- Operator Plane: visible status, approvals, warnings, quarantine controls,
  evidence views, and runbook guidance.

Architecture remains bounded by [Architecture](ARCHITECTURE.md),
[MVP Scope](MVP_SCOPE.md), [Supervisor Spec](SUPERVISOR_SPEC.md),
[Worker Node Spec](WORKER_NODE_SPEC.md), and [Autonomy Boundaries](AUTONOMY_BOUNDARIES.md).

## Contract And Schema Baseline

The contract source of truth is [contracts/README.md](../contracts/README.md)
and [contracts/v1](../contracts/v1).

Current v1 contracts define records for:

- Worker lifecycle and heartbeat.
- Task execution and Guardian decisions.
- Approval requests, approval results, approval tokens, and token verification.
- Model routing, tool invocation, memory access, helper scope, and taint refs.
- Connector trust.
- Evidence artifacts and evidence failures.
- Incident operations, lab SLOs, and LIMA IT handoff.

The contract baseline is schema-first and evidence-first. Runtime behavior
remains blocked when the relevant contract, Guardian policy, approval state,
evidence behavior, failure handling, and MVP acceptance gate are missing or
ambiguous.

## Policy And Runbook Baseline

Policy docs are indexed in [Policy Index](policies/README.md). Runbooks are
indexed in [Docs README](README.md).

Current policy/runbook coverage includes:

- Approval flow and approval token lifecycle.
- Evidence writer failure.
- Retention and redaction placeholders.
- Prompt-injection handling.
- Worker onboarding, quarantine, and re-enrollment.
- Security incident response.
- Health checks.
- LIMA IT diagnostic and remediation handoff.

These are planning and operator-control docs. They do not authorize live
customer actions, live connector use, or remediation execution.

## Validation And CI Baseline

Validation is documented in [Phase 0 Validation](VALIDATION.md) and captured for
this closeout in [Validation Evidence](VALIDATION_EVIDENCE.md).

The validation baseline includes:

- Strict JSON Schema draft 2020-12 validation with format checks.
- Example-to-schema mapping and coverage checks.
- Unsafe-content scanning across examples and Markdown docs.
- Local Markdown link validation.
- Unit tests for Phase 1A mock runtime behavior.
- Python compile checks.
- Git whitespace checks.

CI expectation is the workflow in `.github/workflows/phase0-validation.yml`.
CI runs without repository secrets and validates contracts, docs links, unit
tests, Python compilation, and whitespace.

Validation is not production certification. It does not prove live connector
readiness, live customer data safety, identity assurance, worker attestation,
durable evidence integrity, audit export, customer exit/delete, or LIMA IT
separation of duties.

## Runtime Baseline

Phase 1A runtime is mock/in-memory only. It is documented in
[Phase 1A Runtime Scaffolding](PHASE_1A_RUNTIME_SCAFFOLDING.md) and bounded by
[Runtime Boundaries](RUNTIME_BOUNDARIES.md).

Available runtime modules provide:

- Contract loading from `contracts/v1` with fail-closed behavior for missing,
  unreadable, invalid, or ambiguous schemas.
- Runtime contract validation requiring `jsonschema` and format support.
- Default-deny Guardian policy stubs for Phase 1A action classes.
- One-tenant, up-to-eight-worker in-memory registry.
- Heartbeat validation for worker state, tenant, staleness, Guardian
  reachability, and evidence-writer posture.
- In-memory task queue that requires validated Guardian decisions before
  assignment and blocks quarantined, revoked, offline, or wrong-tenant workers.
- Metadata-only in-memory evidence writer with simulated failure behavior.

It does not implement real dispatch, model calls, tools, connector access,
background loops, durable storage, UI, or production operations.

## Cross-Contract Invariant Baseline

The task requested use of `docs/CROSS_CONTRACT_INVARIANTS.md`; that file is not
present in this checkout. The task also identifies
`phase-1a-cross-contract-invariants` / `e71431007ddbe96c3e141b77591efc2508c53e5d`.
The original checkpoint and the 2026-05-22 reconciliation check both found that
the commit is not reachable from the local repository and `origin` does not
advertise the branch.

Current available evidence supports these invariant themes:

- Tenant and customer context are required in contract envelopes.
- Guardian decision references are required for action-bearing records.
- Approval-required paths use approval request/result/token/verification
  contracts rather than raw approval material.
- Evidence refs and evidence failure records are first-class outcomes.
- Worker quarantine/revoke state blocks task assignment in the Phase 1A mock
  queue.
- Live connector access, external sends, remediation, unrestricted tool access,
  cross-tenant memory, and production-system touch remain blocked by current
  docs, contracts, and Phase 1A policy stubs.

Remaining invariant gates before runtime expansion:

- Approval-token runtime record binding to the exact task, action class,
  resource refs, tenant, policy snapshot, and fresh operator intent. Later
  Phase 1A branch `approval-token-runtime-binding-design` addresses the
  mock/in-memory design.
- Guardian decision expiry and replay policy. Later Phase 1A branch
  `guardian-expiry-replay-policy-design` addresses the mock/in-memory design;
  durable replay storage remains future work.
- Health reason taxonomy across worker, Guardian, evidence, queue, connector,
  and LIMA IT handoff states.
- Durable evidence/export posture for audit, retention, redaction, customer
  exit/delete, and reconciliation.
- Durable memory posture for retention, delete/export, raw-content handling,
  prompt-injection review, and customer exit/delete.
- Model-routing defaults for local versus subscription/cloud provider classes
  and data classifications that force local-only handling or denial.

## Supervisor Health Baseline

The supervisor health baseline is still a mock/planning baseline. It includes
contract and test coverage for:

- Worker registration state.
- Heartbeat age and missed-heartbeat posture.
- Worker health states including healthy, degraded, offline, quarantined, and
  revoked.
- Queue depth and task assignment blocking.
- Guardian allow, deny, approval-required, block-MVP, and quarantine decisions.
- Evidence writer success/failure posture.
- Mock connector readiness as contract state only.
- LIMA IT handoff status as contract state only.

No operator console, health dashboard, daemon, metrics server, database, or
production monitoring service exists in the current repo.

## Explicit Non-Goals

- No live connectors.
- No OAuth/provider wiring.
- No external model API calls.
- No external email, text, chat, form submission, or customer-system send.
- No browser automation.
- No real IT remediation.
- No production server control.
- No durable database, queue, web server, UI framework, scheduler, or production
  service.
- No autonomous financial, legal, medical, HR, discipline, monitoring, or
  regulated-system decisions.
- No cross-tenant memory sharing.
- No hidden background actions.
- No marketing, pricing, sales, TAM, or production-readiness claims.

## Safety Boundaries

Safe automatic work remains limited to summarization, ticket classification,
drafting, form preparation, diagnostics gathering, internal note updates,
runbook suggestions, file organization planning, and draft customer-service
replies.

Approval is required for external sends, form submission, delete/overwrite,
customer record mutation, software install/update, remediation, sensitive data
access, production server touch, and regulated systems.

Blocked for MVP are autonomous financial decisions, autonomous employee
discipline or monitoring decisions, autonomous production server changes,
cross-tenant memory sharing, hidden background actions, and unrestricted
browser/file/network access.

## Remaining Open Questions

The organized blocker list is maintained in [Open Questions](OPEN_QUESTIONS.md).
The highest-priority blockers are:

- Operator IdP/MFA, breakglass, access review cadence, and LIMA IT approver
  separation.
- Retention defaults, redaction taxonomy, audit export, customer exit/delete,
  and durable evidence/export posture.
- Approval-token runtime record binding and Guardian expiry/replay are covered
  by later Phase 1A mock-hardening branches; durable evidence/export, final
  health reason taxonomy, worker attestation, and update rollback remain open.
- Connector consent/scope/revocation, model routing defaults, and first
  deployment posture.

## Next-Lane Decision Matrix

| Option | Safe now? | Purpose | Primary blocker | Recommendation |
| --- | --- | --- | --- | --- |
| A. Worker deployment blueprint | Yes, docs/contracts only | Define lab deployment shape for 1 Supervisor Server and 1-8 Arc workers. | Must avoid installers, agents, live services, and remediation. | Do first. |
| B. Governance policy details | Yes, docs/contracts only | Resolve IdP/MFA, breakglass, access review, LIMA IT approver separation, retention, redaction, audit export, and customer exit/delete policy. | Needs clear choices before runtime expansion. | Do second. |
| C. Operator console UX spec | Yes, spec only | Define health, approvals, evidence, quarantine, and runbook views without building UI. | Must not add UI framework or live actions. | Do third. |
| D. Phase 1B lab runtime expansion | No, not yet | Expand mock lab runtime only after critical gates are closed. | Durable replay/evidence/export posture, final health taxonomy, and governance/runtime gates. | Defer until gates are approved. |
| E. Merge strategy / mainline stabilization | Yes, repository hygiene only | Decide branch merge order and stabilize mainline docs/tests. | Missing cross-contract invariant source must be resolved or explicitly superseded. | Do alongside A/B as needed. |
