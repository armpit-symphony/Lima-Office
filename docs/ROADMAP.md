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

- Phase 1A mock runtime scaffold for contract loading and validation.
- In-memory mock worker registry, heartbeat intake, task queue, Guardian decisions, and evidence writer.
- Runtime tests for fail-closed policy, validation, worker state, heartbeat, task, and evidence behavior.
- Phase 1A v2 cross-contract invariant checks and Supervisor health contract/reporting.
- Supervisor skeleton if separately approved beyond mock scaffolding.
- Worker skeleton if separately approved beyond mock scaffolding.
- Mock task queue.
- Mock Guardian decision log.
- Mock evidence ledger.
- Health dashboard prototype.

### Acceptance Gates

- 1 Supervisor Server and 1-3 lab workers represented.
- Worker registration and heartbeat states are visible.
- Every task transition has a Guardian decision and evidence reference.
- Valid contracts cannot be combined into unsafe flows across Guardian,
  approval, token, evidence, taint, worker, tool, memory, helper, or LIMA IT
  records.
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
