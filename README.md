# LIMA Office

Local-first business AI automation suite and control plane for guarded AI worker bots.

LIMA Office is the business automation layer for SparkPit Labs' LIMA ecosystem. It is designed to coordinate AI worker bots, business tasks, approvals, connectors, audit evidence, and local office nodes so businesses can operate more efficiently and securely while keeping control in-house.

LIMA Office is the business AI automation suite and local office control plane. It is the network/workings layer of the business suite, coordinating Arc Bots, approvals, connectors, tasks, office workflows, evidence, business policy, and local mini-PC nodes so a business can use AI worker bots safely without handing its whole operation to a hosted SaaS platform.

## System Relationship

- LIMA AI OS = universal reasoning/runtime operating system and safety substrate
- LIMA Office = business AI automation suite / local business control plane
- LIMA IT = IT service and security manager layered with LIMA Office
- Arc Bot Shell = customizable guarded worker-bot shell for business roles
- Sparkbot Shell = public open-source hobbyist/workstation shell, separate from LIMA Office

LIMA Office and LIMA IT are designed to work together as an all-in-one business AI automation and IT support system: cheaper to run, more efficient to operate, and safer for businesses that want local/in-house control where practical.

## What LIMA Office Is

- A business AI automation suite
- A local office control plane
- A coordinator for Arc Bots and future worker bots
- A task/approval/audit hub
- A connector and business workflow manager
- A local-node/mini-PC coordination layer
- A business-owned alternative to scattered SaaS automations
- Layered with LIMA IT for secure IT/service operations
- Powered conceptually by LIMA AI OS contracts and safety posture

## What LIMA Office Is Not

- Not Sparkbot
- Not Arc Bot itself
- Not LIMA IT itself
- Not LIMA AI OS itself
- Not a public hobbyist workstation
- Not an unmanaged automation runner
- Not a hidden background task system
- Not a replacement for approvals/audit
- Not a robot/IoT controller by default
- Not allowed to execute, dispatch, persist, or mutate business systems without future explicit approved wiring

## Core LIMA Office Surfaces

### Office Dashboard

- Business health overview
- Active bots
- Active tasks
- Pending approvals
- Connector health
- Risk/attention summary
- Recent evidence/audit activity

### Bot Registry

- Arc Bots and worker bots
- Bot role
- Client/department assignment
- Status
- Risk tier
- Allowed task categories
- Kill switch
- Last heartbeat later

### Task Queue

- Incoming business tasks
- Assigned bot
- Status
- Priority
- Risk
- Due date
- Blocked reason
- Approval requirement

### Approval Center

- Pending approvals
- Blocked actions
- PIN/breakglass-required actions
- Owner/operator decisions
- No real approval enforcement in roadmap shell yet

### Connector Center

- Gmail/Outlook
- Calendar
- Drive/OneDrive
- CRM
- Ticketing/helpdesk
- Accounting/billing
- Slack/Teams
- Custom business systems
- Configured/missing/disabled states
- Read/write scope posture

### Workflow Library

- Reusable office workflows
- Task templates
- Department templates
- Approval templates
- Escalation paths
- Client-specific workflows

### Evidence / Audit Center

- Task evidence
- Preview evidence
- Approval notes
- Run summaries later
- Redacted audit references
- Exportable business report later

### Client / Business Profile

- Company profile
- Departments
- Users/operators
- Policies
- Office hours
- Maintenance windows
- Connector profile
- Compliance notes
- Escalation contacts

### Local Node Manager

- Mini PCs
- Arc Bot nodes
- LIMA IT nodes
- Local service status
- Deployment notes
- Offline/degraded posture

### LIMA IT Panel

- IT health summary
- Security posture summary
- Support ticket summary
- Device/node risk summary
- Link to LIMA IT service layer later

## Planned Business Automation Capabilities

- Office task intake
- Task assignment to Arc Bots
- Approval routing
- Connector setup visibility
- Client/business profile management
- Workflow templates
- Meeting/action-item routing
- Document/report generation workflow
- Scheduling workflow
- Customer support workflow
- Billing/admin workflow
- HR intake workflow
- IT support handoff to LIMA IT
- Evidence/audit reporting
- Business health dashboard
- Local AI worker node coordination

## Strict Business Safety Posture

LIMA Office should make business automation safer, not more chaotic.

Default assumptions:

- Preview before action
- Explain-plan before risky work
- Approval before external writes
- Approval before connector writes
- Approval before scheduled automation
- Audit/evidence for business trust
- Clear connector setup status
- Local/business-owned deployment where possible
- No hidden background jobs
- No surprise external sends
- No unmanaged worker bots
- No secrets in logs
- No infrastructure changes without LIMA IT boundary
- No robotics/physical-world actions by default

## Business Action Classes

Planning vocabulary:

- `task_intake`
- `task_assignment`
- `draft_generation`
- `internal_note`
- `report_generation`
- `calendar_read`
- `calendar_write`
- `external_email`
- `document_read`
- `document_write`
- `crm_update`
- `ticket_create`
- `billing_task`
- `hr_intake`
- `approval_request`
- `scheduled_work`
- `connector_setup`
- `secret_use`
- `admin_action`
- `it_support_handoff`
- `blocked_action`

These are roadmap/planning categories only. This README does not imply real execution exists yet.

## Task Lifecycle

```text
task_created
  -> classified
  -> assigned_to_bot
  -> preview_ready
  -> approval_required or blocked or draft_ready
  -> approved_by_operator_later
  -> dispatch_ready_later
  -> completed_later
  -> evidence_recorded_later
```

The current roadmap may describe these states, but it must not implement connector calls, background jobs, dispatch, approval enforcement, persistence, external sends, business-system writes, network control, endpoint control, remediation, or live mutations until the surrounding LIMA Office/LIMA IT/LIMA AI OS contracts are explicitly approved.

## Separation Roadmap

### Phase 0 - Repo Foundation

- README roadmap
- Product boundary
- Business control-plane scope
- License/private distribution decision
- Internal collaboration placeholder
- Security policy placeholder

### Phase 1 - Office Surface Inventory

- Define Office Dashboard fields
- Define Bot Registry fields
- Define Task Queue states
- Define Approval Center labels
- Define Connector Center readiness states
- Define Workflow Library template categories
- Define Evidence / Audit Center fields
- Define Client / Business Profile fields
- Define Local Node Manager display fields
- Define LIMA IT Panel summary fields

### Phase 2 - Contract-First Safety Model

- Define LIMA AI OS runtime boundary assumptions
- Define LIMA IT infrastructure-change boundary assumptions
- Define Guardian-style approval/audit posture language
- Define connector read/write/admin risk tiers
- Define no-execution shell rules
- Define scheduled-work planning posture
- Define evidence requirements for business actions
- Define blocked action categories

### Phase 3 - Shell Skeleton Design

- Office Dashboard wireframe
- Bot Registry wireframe
- Task Queue wireframe
- Approval Center wireframe
- Connector Center wireframe
- Workflow Library wireframe
- Evidence / Audit Center wireframe
- Client / Business Profile wireframe
- Local Node Manager wireframe
- LIMA IT Panel wireframe

### Phase 4 - Sanitized Implementation Planning

- Import only approved LIMA Office shell-safe files when implementation begins
- Do not copy Sparkbot workstation behavior
- Do not copy Arc Bot internals
- Do not copy LIMA IT internals
- Do not copy proprietary LIMA runtime internals
- Do not add live adapters
- Do not add real connector calls, background jobs, network control, endpoint control, or remediation code
- Do not add execution, dispatch, approval enforcement, or persistence code
- Run secret scan before any public or client handoff
- Run dependency/license review before implementation grows

### Phase 5 - Business MVP Definition

- Read-only Office Dashboard
- Bot Registry display state
- Task Queue display state
- Approval Center display state
- Connector Center readiness state
- Workflow Library placeholders
- Evidence / Audit Center placeholder display
- Client / Business Profile screen
- Local Node Manager display state
- LIMA IT Panel summary placeholder
- No live writes, no hidden autonomy, no unmanaged execution

## Public/Private Boundary

LIMA Office is not the open-source hobbyist workstation. Sparkbot Shell owns the public community workstation story. Arc Bot Shell owns role-specific worker-bot shells. LIMA IT owns IT/security/service management. LIMA Office owns the business automation control plane that coordinates those business-facing pieces.

The roadmap should stay honest about the trust boundary: connector writes, external messages, scheduled work, admin actions, infrastructure changes, secrets, client workflows, audit evidence, and worker-bot coordination must remain behind approved LIMA Office, LIMA IT, LIMA AI OS, Guardian-style, Vault-style, and audit contracts.

## Repo Status

This repo is currently a roadmap/staging repo for the LIMA Office business AI automation suite and local control plane. It should remain documentation-only until the business safety model, client-safe configuration model, connector posture, and LIMA IT/LIMA AI OS integration contracts are approved.

## Development Principles

- Business-safe by default
- Local-first where practical
- Approval before risky action
- Evidence/audit for business trust
- Connector health visible
- Clear ownership and operator control
- No hidden background work
- No unmanaged execution
- No surprise external sends
- No surprise cloud dependency
- No secrets in logs
- No infrastructure changes without LIMA IT / Guardian-style approval boundaries
- No real connector calls, background jobs, network control, endpoint control, or remediation code in the roadmap shell

## Suggested Tagline Options

- "The local control plane for guarded AI worker bots."
- "Coordinate the work. Approve the risk. Keep the evidence."
- "Business automation without surrendering the office."
- "Arc Bots, approvals, connectors, and evidence in one local-first suite."

## Next Steps Checklist

- [ ] Confirm LIMA Office product boundary
- [ ] Decide repo visibility and license/distribution model
- [ ] Define first target business environment
- [ ] Define Office Dashboard fields
- [ ] Define Bot Registry fields
- [ ] Define Task Queue states
- [ ] Define Approval Center labels
- [ ] Define Connector Center readiness states
- [ ] Define Workflow Library template categories
- [ ] Define Evidence / Audit Center requirements
- [ ] Define Client / Business Profile schema
- [ ] Define Local Node Manager display fields
- [ ] Define LIMA IT Panel summary fields
- [ ] Create shell wireframes
- [ ] Create no-execution skeleton plan
- [ ] Review LIMA IT/LIMA AI OS contract assumptions
- [ ] Prepare first LIMA Office business MVP roadmap
