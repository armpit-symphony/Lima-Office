# UX And Control-Room Docs

These docs specify the planned LIMA Office Supervisor operator console. They
are UX and control-room specifications only.

No frontend code, UI framework, web server, browser automation, runtime
feature, live connector, OAuth/provider wiring, external send path, remediation
path, database, queue, scheduler, or production operation is implemented here.

The console does not authorize behavior by display alone. Risky actions remain
Guardian, policy, approval, evidence, and audit gated. If the console cannot
show the required Guardian decision, policy refs, approval state, evidence refs,
or runbook, the UX must show a blocked or fail-closed state.

## Specs

- [Operator Console Spec](OPERATOR_CONSOLE_SPEC.md)
- [Operator Workflows](OPERATOR_WORKFLOWS.md)
- [Console Information Architecture](CONSOLE_INFORMATION_ARCHITECTURE.md)
- [Console Permission Model](CONSOLE_PERMISSION_MODEL.md)
- [Approval Inbox Spec](APPROVAL_INBOX_SPEC.md)
- [Evidence Viewer Spec](EVIDENCE_VIEWER_SPEC.md)
- [Worker Fleet Spec](WORKER_FLEET_SPEC.md)
- [LIMA IT Panel Spec](LIMA_IT_PANEL_SPEC.md)
- [Health Reason Taxonomy](HEALTH_REASON_TAXONOMY.md)

## Supporting Contracts

- [console.view](../../contracts/v1/console.view.schema.json)
- [console.alert](../../contracts/v1/console.alert.schema.json)
- [console.action](../../contracts/v1/console.action.schema.json)
