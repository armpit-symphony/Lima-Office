# LIMA Office OS Docs

This directory contains Phase 0 architecture, security, contracts, planning, Phase 1A mock runtime scaffolding notes, and runbook docs for LIMA Office OS.

## Core Docs

- [Current status](../STATUS.md)
- [Canonical baseline](BASELINE.md)
- [Architecture](ARCHITECTURE.md)
- [MVP scope](MVP_SCOPE.md)
- [Roadmap](ROADMAP.md)
- [Contracts](CONTRACTS.md)
- [Security model](SECURITY_MODEL.md)
- [Threat model](THREAT_MODEL.md)
- [Worker node spec](WORKER_NODE_SPEC.md)
- [Supervisor spec](SUPERVISOR_SPEC.md)
- [Autonomy boundaries](AUTONOMY_BOUNDARIES.md)
- [Decisions](DECISIONS.md)
- [Open questions](OPEN_QUESTIONS.md)
- [Validation](VALIDATION.md)
- [Phase 1A runtime scaffolding](PHASE_1A_RUNTIME_SCAFFOLDING.md)
- [Phase 0 / Phase 1A closeout](PHASE_0_1A_CLOSEOUT.md)
- [Next phase plan](NEXT_PHASE_PLAN.md)
- [Runtime boundaries](RUNTIME_BOUNDARIES.md)
- [Validation evidence](VALIDATION_EVIDENCE.md)

## Deployment Docs

- [Deployment index](deployment/README.md)
- [Worker deployment blueprint](deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)
- [Network blueprint](deployment/NETWORK_BLUEPRINT.md)
- [Worker hardware baseline](deployment/WORKER_HARDWARE_BASELINE.md)
- [Worker install layout](deployment/WORKER_INSTALL_LAYOUT.md)
- [Worker lifecycle](deployment/WORKER_LIFECYCLE.md)
- [Update rollback blueprint](deployment/UPDATE_ROLLBACK_BLUEPRINT.md)
- [Field IT checklist](deployment/FIELD_IT_CHECKLIST.md)

## Governance Docs

- [Governance index](governance/README.md)
- [Identity and MFA policy](governance/IDENTITY_AND_MFA_POLICY.md)
- [Approver separation policy](governance/APPROVER_SEPARATION_POLICY.md)
- [Breakglass policy](governance/BREAKGLASS_POLICY.md)
- [Retention redaction policy](governance/RETENTION_REDACTION_POLICY.md)
- [Audit export and customer exit policy](governance/AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md)
- [Connector consent scope revocation policy](governance/CONNECTOR_CONSENT_SCOPE_REVOCATION_POLICY.md)
- [Worker attestation policy](governance/WORKER_ATTESTATION_POLICY.md)
- [Signed update rollback policy](governance/SIGNED_UPDATE_ROLLBACK_POLICY.md)

## UX / Control-Room Docs

- [UX index](ux/README.md)
- [Operator console spec](ux/OPERATOR_CONSOLE_SPEC.md)
- [Operator workflows](ux/OPERATOR_WORKFLOWS.md)
- [Console information architecture](ux/CONSOLE_INFORMATION_ARCHITECTURE.md)
- [Console permission model](ux/CONSOLE_PERMISSION_MODEL.md)
- [Approval inbox spec](ux/APPROVAL_INBOX_SPEC.md)
- [Evidence viewer spec](ux/EVIDENCE_VIEWER_SPEC.md)
- [Worker fleet spec](ux/WORKER_FLEET_SPEC.md)
- [LIMA IT panel spec](ux/LIMA_IT_PANEL_SPEC.md)
- [Health reason taxonomy](ux/HEALTH_REASON_TAXONOMY.md)

## Runbooks

- [Access review](runbooks/access-review.md)
- [Breakglass review](runbooks/breakglass-review.md)
- [Customer exit delete](runbooks/customer-exit-delete.md)
- [Connector revocation](runbooks/connector-revocation.md)
- [Worker attestation failure](runbooks/worker-attestation-failure.md)
- [Update rollback approval](runbooks/update-rollback-approval.md)
- [Worker onboarding](runbooks/worker-onboarding.md)
- [Worker deployment](runbooks/worker-deployment.md)
- [Worker quarantine](runbooks/worker-quarantine.md)
- [Worker re-enrollment](runbooks/worker-reenrollment.md)
- [Worker update rollback](runbooks/worker-update-rollback.md)
- [Field IT preflight](runbooks/field-it-preflight.md)
- [Approval flow](runbooks/approval-flow.md)
- [Approval token lifecycle](runbooks/approval-token-lifecycle.md)
- [Security incident](runbooks/security-incident.md)
- [Health checks](runbooks/health-checks.md)
- [Evidence writer failure](runbooks/evidence-writer-failure.md)
- [Prompt injection response](runbooks/prompt-injection-response.md)
- [LIMA IT handoff](runbooks/lima-it-handoff.md)

## Policies

- [Policy index](policies/README.md)
- [Approval token lifecycle](policies/approval-token-lifecycle.md)
- [Evidence writer failure](policies/evidence-writer-failure.md)
- [Retention and redaction matrix](policies/retention-redaction-matrix.md)
- [Prompt injection handling](policies/prompt-injection-handling.md)
- [Worker quarantine and re-enrollment](policies/worker-quarantine-reenrollment.md)
- [LIMA IT diagnostic and remediation handoff](policies/lima-it-diagnostic-remediation-handoff.md)

## Agent Role Docs

- [Software architect](agents/software-architect.md)
- [Security architect](agents/security-architect.md)
- [SRE / Field IT](agents/sre-field-it.md)
- [AI runtime engineer](agents/ai-runtime-engineer.md)
- [Compliance reviewer](agents/compliance-reviewer.md)
- [Product scope guardian](agents/product-scope-guardian.md)

## Phase Rule

These docs define boundaries, contracts, and mock scaffolding. They do not approve live connectors, external sends, customer-system mutation, hidden background work, remediation execution, or production operation.
