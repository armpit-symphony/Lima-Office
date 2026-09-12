# Roadmap

## Phase 0: Architecture, Contracts, Security Baseline

### Goals

- Define the governed small-business control-plane architecture.
- Document Guardian syscall gate requirements.
- Define core contracts before implementation.
- Create security model, threat model, and runbook baseline.

### Deliverables

- Docs index.
- Architecture doc.
- MVP scope.
- Contracts.
- Security model.
- Threat model.
- Worker and supervisor specs.
- Autonomy boundaries.
- Decision log.
- Open questions.
- Initial runbooks.

### Acceptance Gates

- No live connectors.
- No runtime dispatch.
- No hardcoded secrets.
- Guardian contracts documented.
- Threat model covers prompt injection, worker compromise, connector overreach, and evidence tampering.
- `git diff --check` passes.

### Risks

- Scope drift into broad product surfaces.
- Connector assumptions before trust contracts.
- Marketing or production-readiness language.
- Runtime work before contracts.

### What Not To Build Yet

- Live connector code.
- Background workers.
- Model provider integration.
- Approval enforcement runtime.
- Customer data storage.
- Production deployment scripts.

## Phase 1: Lab MVP With Supervisor And 1-3 Workers

### Goals

- Validate the control-plane model in a lab.
- Exercise worker registration, heartbeat, task assignment records, and evidence records.
- Keep connectors mocked.

### Deliverables

Current lab implementation status (2026-09-07): the attended localhost preview
runs one Supervisor and one Arc worker as real child processes. Arc now exposes
an explicit operator-triggered Supervisor inventory refresh and a separately
authorized redacted evidence-trace read. Both use the existing signed operator
channel, Guardian and LIMA gates, durable Supervisor evidence, and fail-closed
client validation. There is no automatic dashboard polling, connector access,
external submission, or task-execution authority in this surface.

The same attended process now serves a separate business-owner console at
`/office`. It displays redacted Supervisor, Arc worker, approval, training,
evidence, build, and Codex subscription-readiness status. The lab.6 source now
adds one explicit, Guardian-gated, evidenced, read-only and ephemeral Supervisor
text turn through the saved ChatGPT/Codex session. The same attended process now
also runs one deterministic `office_operations_helper` for explicitly requested
reviews of the five fixed synthetic registration scenarios. The helper produces
findings, recommendations, and proposed task steps without model calls, tools,
memory, approvals, Arc dispatch, connector action, submission, or external
business side effects. The Supervisor can now turn the current in-process helper
result into a durable structured proposal, edit only fixed priority/steps, and
record propose, accept-for-future-approval, deny, or cancel decisions. Revision
checks and atomic proposal/completion-evidence commits are implemented. No
approval token, worker assignment, Arc dispatch, or external effect is enabled.
A separate tokenless approval-preview is now implemented. It binds the exact
accepted proposal revision/hash, shows scope, expiry, prohibited operations,
future identity/fresh-intent requirements, and supports reviewed-no-authority,
deny, and withdraw outcomes. It creates no real approval request/result,
binding, replay record, token, worker assignment, or Arc dispatch. Verified
operator session binding and creation of a real pending approval request are now
implemented for the synthetic form-review lane. The binding is pseudonymous,
localhost/process-bound, expires after 30 minutes, survives no restart, collects
no PIN/password, and explicitly does not claim production identity assurance.
The resulting `approval.request` is durable and fixed at `pending_review` with
external effect `none`, zero uses, and no approval token, execution binding,
replay record, worker assignment, or Arc dispatch. Durable non-authorizing
`denied`, `cancelled`, and explicitly recorded `expired` results are now
implemented with exact-record checks and atomic request/result/evidence commits.
The positive-approval readiness assessment contract and decision brief are now
implemented. Profile A, `attended_os_session_lab_only`, is selected temporarily
for whole-system synthetic testing with the low-risk single-owner exception.
The assessment is `blocked_controls_missing`: positive approval, approval
results, tokens, execution bindings, replay consumption, worker assignment,
Arc dispatch, and external effects remain disabled. Profile B or C and its
threat review are required before customer or production use.

- Phase 1A mock runtime scaffold for contract loading and validation.
- In-memory mock worker registry, heartbeat intake, task queue, Guardian decisions, and evidence writer.
- Runtime tests for fail-closed policy, validation, worker state, heartbeat, task, and evidence behavior.
- Phase 1A v2 cross-contract invariant checks and Supervisor health contract/reporting.
- Approval-token binding and Guardian expiry/replay mock-hardening
  checkpoints.
- Supervisor skeleton if separately approved beyond mock scaffolding.
- Worker skeleton if separately approved beyond mock scaffolding.
- Mock task queue.
- Mock Guardian decision log.
- Mock evidence ledger.
- Health dashboard prototype.

### Acceptance Gates

- 1 Supervisor Server and 1-3 lab workers represented.
- Worker registration and heartbeat states are visible.
- The localhost Arc UI can explicitly display the Supervisor-derived status of
  the registered worker and a redacted trace for a known request ID.
- Every task transition has a Guardian decision and evidence reference.
- Valid contracts cannot be combined into unsafe flows across Guardian,
  approval, token, evidence, taint, worker, tool, memory, helper, or LIMA IT
  records.
- Guardian decisions are time-bounded, one-time in mock tests, scoped to the
  requested tenant/task/worker/action/tool metadata, and fail closed on replay,
  stale age, expiry, clock-skew violation, taint, or blocked-MVP actions.
- No external writes or live connector calls.
- Runtime validation requires real `jsonschema` and fails closed without it.
- Mock queues remain synchronous in-memory records only; no tool execution, services, daemons, or background loops.

### Risks

- Lab scaffolding becoming implicit production behavior.
- Overfitting to one machine setup.
- Tool access escaping role scope.
- Treating metadata-only Supervisor health reports as production monitoring.

### What Not To Build Yet

- Real connector OAuth.
- Customer-system writes.
- Autonomous remediation.
- Production installer.
- External model API calls.
- Browser automation.

## Phase 2: Office MVP Workflows

### Goals

- Define first office workflows as draft-first, approval-gated processes.
- Add operator review patterns and evidence views.
- Keep external action mocked until connector trust is approved.

### Deliverables

- Workflow templates.
- Approval workflow spec.
- Evidence package spec.
- Mock connector workflow states.
- Operator dashboard refinements.

### Acceptance Gates

- Workflows are draft-only or mock-only.
- Approval-required actions cannot be marked automatic.
- Evidence export posture is documented.
- Data classification is applied.

### Risks

- Sensitive HR/finance/legal/medical workflows arriving before data handling policy.
- Operator UI implying actions occurred.
- Prompt injection through workflow inputs.

### What Not To Build Yet

- Live email send.
- CRM update.
- Billing or payment action.
- HR record mutation.

## Phase 3: LIMA IT Integration

### Goals

- Define LIMA IT diagnostic, helpdesk, health-check, and approved-remediation handoff.
- Separate diagnostics from remediation.
- Preserve Guardian, approval, and evidence requirements.

### Deliverables

- LIMA IT bridge contract.
- Diagnostic handoff runbook.
- Approved remediation request contract.
- Incident escalation flow.
- Device health summary spec.

### Acceptance Gates

- Diagnostics are read-only by default.
- Remediation requires approval.
- Evidence captures operator, device, action, policy, and result.
- Production servers remain out of scope unless explicitly approved later.

### Risks

- Endpoint or network control before policy.
- Secrets in logs.
- Support actions crossing tenant or customer boundaries.

### What Not To Build Yet

- Autonomous remediation.
- Production server changes.
- Network reconfiguration.
- Endpoint control agents.

## Phase 4: Pilot Package For One Small Business With 1-8 Workers

### Goals

- Package the lab-tested architecture for a controlled single-business pilot.
- Exercise 1-8 worker design with operator governance.
- Validate runbooks, evidence, and rollback posture.

### Deliverables

- Pilot readiness checklist.
- Deployment plan.
- Backup/restore and rollback plan.
- Operator training notes.
- Customer exit/delete plan.
- Evidence export plan.

### Acceptance Gates

- Threat model reviewed.
- Contracts reviewed.
- No live connector without connector trust approval.
- Human approvers assigned.
- Incident and quarantine runbooks rehearsed.

### Risks

- Treating pilot as production-ready.
- Live connector scope creep.
- Incomplete retention/delete policy.
- Underdefined support ownership.

### What Not To Build Yet

- Multi-tenant SaaS platform.
- Marketplace or plugin economy.
- Production claims.
- Enterprise-scale administration.
