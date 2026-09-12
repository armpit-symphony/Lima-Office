# Supervisor Spec

## Purpose

The Supervisor Server is the LIMA Office OS control plane for one small-business tenant. It coordinates workers, applies policy, requests Guardian decisions, manages approvals, records evidence, and reports status.

## Orchestrator

The orchestrator owns task intake, state transitions, worker assignment, retry posture, timeout handling, and degraded-mode behavior. It cannot bypass Guardian.

## Task Router

The task router matches tasks to workers using:

- Worker role.
- Capability manifest.
- Health state.
- Tool-pack scope.
- Model options.
- Data classification.
- Current load.
- Guardian decision.
- Approval state.

## Policy Engine

The policy engine stores planning rules for:

- Autonomy boundaries.
- Risk tiers.
- Approval requirements.
- Blocked MVP actions.
- Connector readiness.
- Tenant isolation.
- LIMA IT handoff.

Guardian remains the syscall gate for action decisions.

## Approval Service

The approval service manages requests for privileged or high-risk work. Approval records include approver identity, scope, action class, risk tier, expiration, replay protection, and evidence references.

Approval review must also account for the governance policy scaffolding in
[Governance Docs](governance/README.md): identity/MFA posture, access review,
approver separation, breakglass denial, export/delete review, connector consent,
attestation, and update/rollback posture. Missing or ambiguous governance
posture blocks privileged runtime expansion.

The operator-facing control room is specified in
[Operator Console Spec](ux/OPERATOR_CONSOLE_SPEC.md). It defines dashboard
areas, approval inbox behavior, evidence visibility, worker fleet views, LIMA IT
handoff views, and fail-closed UX states without implementing UI code.

## Worker Registry

The worker registry tracks:

- Deployment ID.
- Worker ID.
- Device identity reference.
- Channel identity reference.
- Role.
- Hardware and OS profile refs.
- Supervisor endpoint ref.
- Capability manifest.
- Policy and model bundle refs.
- Health state.
- Last heartbeat timestamp.
- Missed heartbeat count.
- Assigned tasks.
- Quarantine/revoke status.
- Update version.
- Rollback state.
- Evidence refs.

The first Arc-facing inventory surface is an explicit foreground refresh, not
a passive or background dashboard poll. The authenticated operator cannot
choose the worker set or assert worker health, role, capability, eligibility,
classification, or authority. The Supervisor lists its own registry in stable
worker-ID order, derives a non-executing `status` preflight for each worker,
and returns at most eight signed entries.

A worker is eligible only when it is authenticated, registry-assignable, has a
fresh governed status result, and acknowledges the non-executing assignment
preview. Offline, degraded, quarantined, revoked, or rejected workers remain
ineligible. Guardian or LIMA unavailability denies the inventory and suppresses
worker details. Worker disconnects and quarantine remain isolated to the
affected worker while the other workers continue through their independent
request-bound decisions.

## Operator Evidence Trace

The Supervisor exposes one signed, loopback-only evidence-read operation for
Arc. The request accepts a target request ID but no worker choice, role,
classification, capability, or authority claim. The Supervisor selects an
authenticated worker, derives the evidence-read resource and safe-read
category, and routes a non-executing assignment through mandatory Guardian and
LIMA before reading SQLite.

Only redacted event metadata is returned. Tenant scope comes from the
authenticated channel and every target event must belong to the authenticated
actor. Missing and actor-mismatched targets are intentionally
indistinguishable to the caller. The authorization chain and the
`evidence_read` event are durable. No target events are returned if Guardian,
LIMA, Arc acknowledgement, or evidence writing fails.

## Model Router

The model router selects local or subscription/cloud provider class based on policy. It must record:

- Tenant.
- Task.
- Worker/helper identity.
- Data classification.
- Provider class.
- Guardian decision ID.
- Evidence artifact ID.

It does not make direct model calls without Guardian approval.

## Audit/Evidence Ledger

The ledger records references to evidence artifacts for:

- Guardian decisions.
- Approvals.
- Worker lifecycle events.
- Task transitions.
- Incidents.
- Connector readiness.
- LIMA IT handoff.

Evidence must be redaction-aware, export-aware, and retention-aware.
Audit export and customer exit/delete posture is defined as metadata-only in
[Audit Export And Customer Exit Policy](governance/AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md).

Console-visible health reason labels are scaffolded in
[Health Reason Taxonomy](ux/HEALTH_REASON_TAXONOMY.md).

## Tenant Memory Service

Tenant memory is scoped to one tenant and one customer context at a time. It must support:

- Tenant namespace.
- Source reference.
- Retention rule.
- Delete/export posture.
- Prompt injection handling for retrieved content.
- No cross-tenant sharing.

## Helper Agents

The supervisor may use 1-4 helper agents for memory review, file organization, background review, or LIMA IT assistance. Helper agents:

- Stay supervisor-side.
- Use scoped tasks.
- Require Guardian decisions for actions.
- Produce evidence.
- Do not receive unrestricted tools.
- Cannot directly mutate customer systems.

### Implemented Office Operations Helper Lab Lane (2026-09-07)

The first helper lane is one `office_operations_helper` attached to the
Supervisor. It reviews only the five fixed synthetic registration scenarios
already owned by the Arc training module. Each foreground review requires
explicit confirmation, a validated helper scope and assignment, Guardian
authorization, and evidence before and after deterministic evaluation.

Its result may contain issue fields, reason codes, recommendations, and proposed
non-executing task steps. It always requires owner review and never submits a
form. Model calls, tools, files, memory, approval-token access, connectors, Arc
dispatch, customer data, and external effects are contractually false.

### Implemented Synthetic Task Proposal Lane (2026-09-07)

The Supervisor may convert only the current in-process helper result into a
durable `supervisor.task.proposal`. The local SQLite store contains structured
synthetic metadata, not registration profiles or free-form business content. A
unique source-helper constraint prevents duplicate drafts.

The owner may edit only `low`/`normal` priority and the three fixed review-step
identifiers. Allowed state changes are `draft` to `proposed`, `draft` to
`cancelled`, and `proposed` to `accepted_for_future_approval`, `denied`, or
`cancelled`. Each mutation requires explicit confirmation, expected-revision
matching, Guardian authorization, pre/Guardian evidence, and an atomic
proposal/completion-evidence commit.

Acceptance is deliberately not an approval result: the record has no approval
token, worker assignment, execution scope, or dispatch authority. Arc, tools,
models, connectors, submissions, and external effects remain false.

### Implemented Tokenless Approval Preview Lane (2026-09-07)

One exact `accepted_for_future_approval` proposal revision may produce one
durable `supervisor.approval.preview`. The preview binds the source revision and
content hash and exposes a fixed, synthetic, plan-review-only scope. It records
that a future real request requires verified owner identity, fresh intent,
separation-of-duties review, a Guardian/proposal recheck, a 15-minute request
TTL, and a single-use token only if separately approved later.

The operator can mark the preview `reviewed_no_authority`, `denied`, or
`withdrawn`. Review requires an unexpired 15-minute preview and an unchanged
source proposal. Every mutation uses explicit confirmation, Guardian, sanitized
evidence, optimistic revision checks, and an atomic preview/completion-evidence
commit. The lane does not create an `approval.request`, approval result,
identity binding, nonce/replay record, approval binding, token, worker
assignment, or Arc dispatch.

### Implemented Non-Authorizing Approval Decisions (2026-09-09)

The durable synthetic request lane can now close a `pending_review` request as
`denied`, `cancelled`, or explicitly `expired`. Deny/cancel require an active
attended session, cancellation requires the original binding, and expiry is a
foreground reconciliation after TTL rather than a background job. The exact
request hash is required, Guardian gates the operation, and the request,
separate result, and completion evidence commit atomically. No path creates a
positive approval, approved scope, token, execution binding, replay record,
worker assignment, Arc dispatch, or external effect.

### Positive Approval Readiness Gate (Design Only, 2026-09-09)

The `approval.readiness` contract and
[readiness decision brief](POSITIVE_APPROVAL_READINESS_GATE.md) bind the next
design step to existing identity, RBAC, session, device, approval, token,
binding, verification, replay, Guardian, and evidence contracts. The current
state is blocked pending owner selection of an identity/separation profile.
This adds no Supervisor endpoint or runtime authority.

## Operator Dashboard

The attended lab implements the first narrow dashboard slice inside the Arc
operator UI: an explicit signed refresh of Supervisor-owned worker inventory
and an explicit signed read of one redacted evidence trace. Cached results are
process-memory projections only. Opening or refreshing ordinary Arc state does
not contact these Supervisor endpoints, and neither operation can execute work
or grant runtime authority.

### Business-Owner Console And Read-Only Conversation (2026-09-07)

The attended localhost harness also serves a separate LIMA Office view at
`/office`. It is a business-owner projection over existing Supervisor and Arc
state, not a second scheduler, registry, or source of authority. It provides
Today, Supervisor, Work, Approvals, Arc Workers, Evidence, and Settings views.

The console grants no execution authority. Its only model invocation is one
attended reasoning turn:

- State is fetched from a redacted same-origin projection.
- Worker inventory changes only after an explicit operator refresh.
- Codex subscription readiness checks only for local profile and CLI presence;
  it never reads or returns credential contents.
- Each Supervisor turn requires an explicit confirmation and public or
  non-sensitive internal classification.
- The model runs read-only and ephemeral with user config, rules, web, tools,
  memory, helpers, fallback, and Arc dispatch disabled.
- Pre-action and Guardian evidence must succeed before the call. Post-action
  evidence must succeed before the response is released. Evidence excludes raw
  owner and model text.
- Persistent conversation, helper runtime outside the fixed synthetic review,
  worker dispatch, approval issuance,
  external sends, form submission, and customer-record writes remain disabled.
- The existing Arc UI remains available at `/` and retains its bounded worker
  and training responsibilities.

The dashboard should show:

- Supervisor health.
- Worker status.
- Last heartbeat age.
- Active task count.
- Pending approvals.
- Guardian allow/deny/approval counts.
- Evidence write status.
- Mock connector readiness.
- Quarantine incidents.
- LIMA IT handoff status.

## LIMA IT Bridge

The bridge is future-facing and contract-only in Phase 0. It supports:

- Health-check context.
- Diagnostic handoff.
- Helpdesk triage.
- Approved remediation request.
- Incident evidence sharing.

Remediation requires human approval.

## Attended Lab Approval Intake

The implemented intake boundary binds the current personal-PC localhost process
to a pseudonymous operator ref for 30 minutes. It is not production identity,
does not survive restart, and grants no approval authority. From an unexpired
`reviewed_no_authority` preview, fresh intent can create one durable synthetic
form-review `approval.request` in `pending_review`. The Supervisor cannot decide
that request, issue a token, create an execution binding/replay record, assign a
worker, or dispatch Arc in this milestone.

## Health Checks

Supervisor health checks should cover:

- Service state.
- Worker heartbeat freshness.
- Queue depth.
- Evidence writer status.
- Approval queue age.
- Guardian decision flow.
- Disk, memory, CPU, and network posture.
- Mock connector readiness.
- Worker deployment record completeness.
- Policy/model bundle ref mismatch.
- Public inbound exposure or cross-worker trust flags in deployment records.

## Failure Modes

Planned failure modes:

- Worker offline.
- Worker degraded.
- Worker quarantined.
- Guardian unavailable.
- Evidence writer failure.
- Approval timeout.
- Model provider unavailable.
- Mock connector disabled.
- Supervisor restart.
- LIMA IT handoff unavailable.

Each failure must have visible status, evidence, and a runbook or open question.

## Deployment Planning

The Supervisor Server owns the worker deployment registry posture for lab and
planned local deployments. It must treat `worker.deployment` records as planning
metadata only, not execution permission. A deployment record cannot authorize
worker services, live connectors, external sends, external model calls,
remediation, software install/update execution, or production-system access.
