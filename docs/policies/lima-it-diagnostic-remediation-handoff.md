# LIMA IT Diagnostic And Remediation Handoff Policy

## Purpose

Define the Phase 0 boundary between LIMA Office and LIMA IT. This policy is scaffolding only and does not implement LIMA IT integration, ticketing, remote access, remediation, endpoint control, or production operations.

## Policy Metadata

- Policy ref: `policy.lima_it_handoff.phase0`
- Version: `policy-phase0-v1`
- Status: Draft scaffold.
- Owner role: Field IT reviewer.
- Applies to contracts: `lima_it.handoff`, `approval.request`, `approval.token`, `guardian.decision`, `incident.ops`, `evidence.artifact`.
- Evidence artifact types: `lima_it_handoff`, `guardian_decision`, `approval_request`, `approval_token`, `incident`.
- Fail-closed outcome: diagnostics remain read-only; remediation remains draft/request-only; production touch is blocked.
- Runbook: [LIMA IT Handoff Runbook](../runbooks/lima-it-handoff.md).
- Governance dependency: [Approver Separation Policy](../governance/APPROVER_SEPARATION_POLICY.md)
  blocks self-approval and keeps LIMA IT remediation execution non-authorized
  for MVP.

## Must Not

- Do not execute remediation in Phase 0.
- Do not touch production servers.
- Do not install/update software or change endpoint/network settings through this handoff.
- Do not use live connectors or OAuth.
- Do not classify a mutating action as diagnostic.
- Do not proceed when evidence cannot be written.

## Boundary

LIMA Office may prepare and hand off:

- Read-only diagnostics.
- Helpdesk triage context.
- Incident escalation context.
- Remediation requests that require approval and remain non-executing in Phase 0.

LIMA Office must not directly execute production remediation in MVP.

## Read-Only Diagnostics

Read-only diagnostics may be allowed under low or medium risk policy when:

- Guardian allows the diagnostic scope.
- Data classification is understood.
- Diagnostic scope lists allowed checks.
- Prohibited actions are explicit.
- Evidence can be written.
- Operator can see the handoff.

Read-only diagnostics must not mutate files, settings, records, software, production servers, or customer systems.

## Approval-Required Remediation

Remediation always requires approval in MVP.

Required before a remediation request can proceed beyond draft/request state:

- Guardian decision.
- `approval.request`.
- Scoped `approval.token` if future policy permits execution path.
- Operator owner.
- Field IT reviewer or approver role.
- Incident linkage where applicable.
- Evidence before and after decision.
- Rollback plan placeholder.

Phase 0 does not execute remediation.

## Blocked Remediation For MVP

Blocked in MVP:

- Autonomous remediation.
- Production server changes.
- Endpoint changes.
- Software install/update execution.
- Network/firewall changes.
- Payment, legal, regulated, HR, finance, or medical system changes.
- Hidden background remediation.

## Required Fields From `lima_it.handoff`

LIMA IT handoff records must include:

- `tenant_id`.
- `customer_context_id`.
- `handoff_id`.
- `task_id` or `incident_id`.
- `handoff_type`.
- `status`.
- `requested_by`.
- `operator_owner`.
- `handoff_owner_role`.
- `target_system_ref`.
- `data_classification`.
- `risk_tier`.
- `read_only_diagnostic`.
- `diagnostic_scope`.
- `remediation_authorized`.
- `remediation_scope`.
- `guardian_decision_id`.
- `approval_required`.
- `approval_request_id`.
- `approval_token_id`.
- `evidence_artifact_ids`.

Schema reference: [lima_it.handoff.schema.json](../../contracts/v1/lima_it.handoff.schema.json).

## Runbook Linkage

Operators use [LIMA IT Handoff Runbook](../runbooks/lima-it-handoff.md).

Incident-linked handoffs also use [Security Incident Runbook](../runbooks/security-incident.md).

## Human Approver Role

Phase 0 allowed approver roles:

- Operator for read-only diagnostic handoff review.
- Field IT reviewer for diagnostic/remediation assessment.
- Supervisor admin or approver for approval-required remediation request.
- Security reviewer when the handoff is incident-related.

Who can approve LIMA IT remediation remains an open policy question before runtime.

## Evidence Required

Evidence is required for:

- Guardian handoff decision.
- Diagnostic scope.
- Handoff request.
- Handoff acceptance or denial.
- Approval request and result.
- Remediation request.
- Incident linkage.
- Rollback plan placeholder.
- Handoff closure.

## Rollback Requirement

Any future remediation policy must require rollback plan metadata before approval.

Until rollback requirements are defined, remediation remains draft/request-only.

## Incident Linkage

Create or link `incident.ops` when:

- Remediation misuse is suspected.
- Diagnostic scope is exceeded.
- Evidence cannot be written.
- Target system or production touch is ambiguous.
- Worker or helper agent initiated an unsafe handoff.

## MVP Acceptance Gates

- Read-only diagnostics can be represented without mutation.
- Remediation is approval-required and non-executing in Phase 0.
- Production server changes are blocked unless explicitly authorized by a future policy and contract.
- Handoff records link Guardian, approval state, evidence, operator owner, and incident where relevant.
- Operator runbook exists.
