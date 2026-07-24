# Phase 0 Policies

These policies are non-runtime scaffolding for LIMA Office OS. They define the controls that future runtime work must satisfy, but they do not implement services, connectors, model calls, approval enforcement, evidence storage, remediation, or background jobs.

Runtime must fail closed when policy is missing, ambiguous, expired, contradictory, or not linked to a Guardian decision and evidence record.

## Policy Index

| Policy ref | Version | Status | Owner role | Applies to contracts | Policy doc | Runbook |
| --- | --- | --- | --- | --- | --- | --- |
| `policy.approval_token_lifecycle.phase0` | `policy-phase0-v1` | Draft scaffold | Security reviewer | `guardian.decision`, `approval.request`, `approval.token`, `task.execution`, `tool.invocation`, `lima_it.handoff`, `evidence.artifact` | [Approval Token Lifecycle](approval-token-lifecycle.md) | [Approval Token Lifecycle Runbook](../runbooks/approval-token-lifecycle.md) |
| `policy.evidence_writer_failure.phase0` | `policy-phase0-v1` | Draft scaffold | Supervisor admin | `evidence.artifact`, `task.execution`, `tool.invocation`, `worker.heartbeat`, `worker.lifecycle`, `incident.ops` | [Evidence Writer Failure](evidence-writer-failure.md) | [Evidence Writer Failure Runbook](../runbooks/evidence-writer-failure.md) |
| `policy.retention_redaction.phase0` | `policy-phase0-v1` | Draft scaffold | Compliance reviewer | All v1 contracts with data classification, retention, redaction, export, or delete posture | [Retention And Redaction Matrix](retention-redaction-matrix.md) | [Customer Exit Delete Runbook](../runbooks/customer-exit-delete.md); [Export Delete Conflict Review](../runbooks/export-delete-conflict-review.md) |
| `policy.prompt_injection.phase0` | `policy-phase0-v1` | Draft scaffold | Security reviewer | `guardian.decision`, `model.route`, `tool.invocation`, `memory.access`, `connector.trust`, `incident.ops`, `evidence.artifact` | [Prompt Injection Handling](prompt-injection-handling.md) | [Prompt Injection Response Runbook](../runbooks/prompt-injection-response.md) |
| `policy.worker_quarantine_reenrollment.phase0` | `policy-phase0-v1` | Draft scaffold | Field IT reviewer | `worker.lifecycle`, `worker.heartbeat`, `task.execution`, `approval.token`, `incident.ops`, `evidence.artifact` | [Worker Quarantine And Re-Enrollment](worker-quarantine-reenrollment.md) | [Worker Re-Enrollment Runbook](../runbooks/worker-reenrollment.md) |
| `policy.lima_it_handoff.phase0` | `policy-phase0-v1` | Draft scaffold | Field IT reviewer | `lima_it.handoff`, `approval.request`, `approval.token`, `guardian.decision`, `incident.ops`, `evidence.artifact` | [LIMA IT Diagnostic And Remediation Handoff](lima-it-diagnostic-remediation-handoff.md) | [LIMA IT Handoff Runbook](../runbooks/lima-it-handoff.md) |
| `policy.governance_identity.phase0` | `policy-phase0-v1` | Draft scaffold | Security reviewer | `governance.identity`, `governance.access_review`, approval contracts | [Identity And MFA Policy](../governance/IDENTITY_AND_MFA_POLICY.md) | [Access Review Runbook](../runbooks/access-review.md) |
| `policy.approver_separation.phase0` | `policy-phase0-v1` | Draft scaffold | Security reviewer | `approval.request`, `approval.result`, `governance.access_review`, `lima_it.handoff` | [Approver Separation Policy](../governance/APPROVER_SEPARATION_POLICY.md) | [Access Review Runbook](../runbooks/access-review.md) |
| `policy.breakglass.phase0` | `policy-phase0-v1` | Blocked placeholder | Security reviewer | `governance.breakglass`, `incident.ops`, `evidence.artifact` | [Breakglass Policy](../governance/BREAKGLASS_POLICY.md) | [Breakglass Review Runbook](../runbooks/breakglass-review.md) |
| `policy.audit_export_customer_exit.phase0` | `policy-phase0-v1` | Draft scaffold | Compliance reviewer | `governance.audit_export`, `evidence.artifact`, `memory.access`, worker and connector records | [Audit Export And Customer Exit Policy](../governance/AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md) | [Customer Exit Delete Runbook](../runbooks/customer-exit-delete.md) |
| `policy.connector_consent_scope_revocation.phase0` | `policy-phase0-v1` | Draft scaffold | Security reviewer | `governance.connector_consent`, `connector.trust`, `taint.ref` | [Connector Consent Scope Revocation Policy](../governance/CONNECTOR_CONSENT_SCOPE_REVOCATION_POLICY.md) | [Connector Revocation Runbook](../runbooks/connector-revocation.md) |
| `policy.worker_attestation.phase0` | `policy-phase0-v1` | Placeholder scaffold | Security reviewer | `worker.deployment`, `worker.lifecycle`, `worker.heartbeat`, `governance.update_record` | [Worker Attestation Policy](../governance/WORKER_ATTESTATION_POLICY.md) | [Worker Attestation Failure Runbook](../runbooks/worker-attestation-failure.md) |
| `policy.signed_update_rollback.phase0` | `policy-phase0-v1` | Draft scaffold | Field IT reviewer | `governance.update_record`, `worker.deployment`, `worker.lifecycle`, `worker.heartbeat` | [Signed Update Rollback Policy](../governance/SIGNED_UPDATE_ROLLBACK_POLICY.md) | [Update Rollback Approval Runbook](../runbooks/update-rollback-approval.md) |
| `policy.console_ux.phase0` | `policy-phase0-v1` | Draft scaffold | Supervisor admin | `console.view`, `console.alert`, `console.action`, all operator-visible records | [Operator Console Spec](../ux/OPERATOR_CONSOLE_SPEC.md) | [Operator Workflows](../ux/OPERATOR_WORKFLOWS.md) |

## Policy Versioning

Every Guardian decision must link to stable `policy_refs` and a `policy_version`.

Phase 0 policy docs must define:

- Policy ref.
- Version.
- Status.
- Owner role.
- Applies-to contracts.
- Required evidence.
- Fail-closed outcome.
- Linked runbook.

Future runtime must capture a policy snapshot or hash reference in `guardian.decision.policy_snapshot_hash` and evidence artifacts when policy materially affects the outcome.

## Runtime Block Rule

Future runtime behavior is blocked until the relevant policy, contract, example, and runbook exist and agree.

Minimum required linkage for any Guardian-gated action:

- `guardian.decision` record with policy refs and policy result.
- Action contract record with tenant, actor, scope, risk tier, data classification, and failure behavior.
- Approval state when approval is required.
- Evidence artifact refs for allow, deny, approval, failure, quarantine, and handoff states.
- Incident linkage when policy violation, suspected compromise, or containment occurs.

If a policy does not define an outcome, Guardian must deny or block the action and record evidence.

## Phase 0 Safety Rules

- No live connectors.
- No OAuth or live provider wiring.
- No production remediation.
- No external message sending without future explicit approval policy.
- No cross-tenant memory access.
- No unrestricted browser, file, shell, connector, or network access.
- No plaintext secrets, tokens, API keys, cookies, or private keys in policy, contracts, logs, prompts, examples, or evidence summaries.
- No production-readiness, compliance-certification, marketing, pricing, financial, sales, or TAM claims.

## Policy Review Checklist

Before a policy can support runtime planning:

1. Confirm it stays inside one Supervisor Server and 1-8 Arc workers.
2. Confirm Guardian remains the syscall gate.
3. Confirm approval-required actions cannot execute without scoped approval.
4. Confirm evidence is required before and after privileged actions.
5. Confirm denied, failed, expired, revoked, blocked, and quarantined states are defined.
6. Confirm privacy, retention, redaction, export, and delete posture are explicit or marked as policy decisions needed.
7. Confirm runbook steps exist for operator handling.
