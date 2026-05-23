# Approval Token Lifecycle Policy

## Purpose

Define the Phase 0 approval lifecycle for privileged and high-risk LIMA Office actions. This policy is scaffolding only and does not implement approval services or runtime token validation.

## Policy Metadata

- Policy ref: `policy.approval_token_lifecycle.phase0`
- Version: `policy-phase0-v1`
- Status: Draft scaffold.
- Owner role: Security reviewer.
- Applies to contracts: `guardian.decision`, `approval.request`,
  `approval.result`, `approval.token`, `token.verification`,
  `approval.binding`, `approval.chain`, `task.execution`, `tool.invocation`,
  `lima_it.handoff`, `incident.ops`, `evidence.artifact`.
- Evidence artifact types: `guardian_decision`, `approval_request`, `approval_token`, `denial`, `incident`.
- Fail-closed outcome: block action, deny token use, revoke related tokens, record evidence or evidence-failure incident.
- Runbook: [Approval Token Lifecycle Runbook](../runbooks/approval-token-lifecycle.md).
- Governance dependencies: [Identity And MFA Policy](../governance/IDENTITY_AND_MFA_POLICY.md),
  [Approver Separation Policy](../governance/APPROVER_SEPARATION_POLICY.md),
  and [Breakglass Policy](../governance/BREAKGLASS_POLICY.md). Missing or
  ambiguous identity, MFA, separation, or breakglass posture blocks privileged
  runtime expansion.

## Scope

Applies to actions marked approval-required in [Autonomy Boundaries](../AUTONOMY_BOUNDARIES.md), including external messages, form submission, file delete/overwrite, customer record mutation, software install/update, remediation, sensitive data access, production server touch, and regulated system use.

For Phase 0, production server touch, live connector writes, external sends, and remediation execution remain blocked from execution even when an approval request is represented as metadata.

## Must Not

- Do not use approval tokens as bearer credentials or standing permissions.
- Do not issue tokens for `blocked_mvp` actions.
- Do not use tokens to execute live connector writes, external sends, customer-system mutation, remediation, or production server touch in Phase 0.
- Do not approve broader scope than the original request.
- Do not allow worker, helper agent, model, tool, or supervisor self-approval.
- Do not proceed when evidence is missing or ambiguous.

## Approval Request Creation

An approval request may be created only after Guardian records `requires_approval` in `guardian.decision`.

Required records:

- `guardian.decision` with policy refs, risk tier, data classification, resource refs, and evidence.
- `approval.request` with requested scope, reason, approver roles, expiry, and evidence.
- Action-specific record such as `task.execution`, `tool.invocation`, `memory.access`, or `lima_it.handoff`.

Blocked MVP actions must be denied or `block_mvp`, not converted into approval requests.

## Approver Identity Assumptions

Phase 0 assumes an operator identity exists but does not choose an identity provider.

Minimum approver metadata:

- Approver operator ID.
- Approver role.
- Tenant ID.
- Time of decision.
- Approval or denial result.
- Evidence artifact refs.

Open questions remain for identity provider, MFA, access review cadence, and breakglass process.

## Approval Token Issuance

An approval token record may be issued only after:

1. `approval.request` is approved.
2. Guardian decision still matches the requested tenant, task, action, resource refs, risk tier, and data classification.
3. Evidence for request creation and approval decision has been written.
4. Token scope is no broader than the original approval request.

Approval tokens are metadata records only. They must never contain bearer token material, OAuth codes, API keys, cookies, signatures, passwords, private keys, or plaintext secrets.

Approval tokens are non-executing Phase 0 records. They do not unlock live external sends, live connector writes, customer-system mutation, remediation execution, or production server touch during Phase 0.

## Runtime Binding Record

Before any approval-required mock/dry-run path can proceed, the supervisor or
Guardian must produce and validate an `approval.binding` record. The binding
ties together the approval request, result, token, token verification, Guardian
decision, task, tool invocation where applicable, worker where applicable,
requester, approver, action type, tool scope, nonce ref, policy snapshot,
approved scope hash, and evidence refs.

The binding is not a bearer capability. It is a fail-closed comparison record.
If any requested action metadata differs from the binding, the action is
denied and evidence must be recorded.

For Phase 1A, the mock verifier tracks one-time nonce consumption in memory for
tests only. Durable atomic consumption, replay tables, and exportable replay
evidence remain future runtime work.

## Token TTL

Default Phase 0 placeholder TTL: policy decision needed.

Until a TTL is approved, privileged actions must use the shorter of:

- A policy-defined expiry in `approval.request.expires_at`.
- The approval token `expires_at`.
- The Guardian decision `expires_at`.

Expired tokens fail closed and produce evidence.

## Token Scope

Token scope must bind to:

- Tenant ID.
- Task ID.
- Action class.
- Resource refs.
- Requested operation.
- Approver role and operator ID.
- Guardian decision ID.
- Approval request ID.

The token cannot authorize a broader action than the original request. Any mismatch denies the action and records evidence.

## One-Time Use Vs Reusable Decision

Phase 0 and Phase 1A approval tokens are single-use.

Guardian decisions may be reused only as evidence references, not as execution authorization. If the same privileged action is attempted again, a new scoped approval request and token are required unless a future policy explicitly defines a bounded reusable approval class.

Reusable approvals are deferred.

Token use must be atomic in future runtime: validation and consumption happen
in one guarded transition. If consumption cannot be recorded with evidence, the
token is not considered safely consumed and the action must fail closed. The
current branch proves the rule with an in-memory mock verifier only; it does
not create durable replay protection.

## Token Revocation

Tokens must be revocable before use.

Revocation triggers:

- Operator cancellation.
- Task cancellation.
- Approval request supersession.
- Approval timeout.
- Worker quarantine or revoke.
- Scope mismatch.
- Evidence writer failure.
- Suspected prompt injection.
- Incident escalation.
- Expired or superseded request.
- Guardian decision expiry.
- Policy version change.
- Replay or reuse attempt.

Revocation produces evidence and must block action execution.

Worker quarantine cascades to token revocation for any token bound to that worker, task, action, or capability lease.

## Expired Token Behavior

If token expiry is reached:

- Mark token as expired.
- Block the privileged action.
- Record `evidence.artifact`.
- Leave the task in `needs_approval`, `blocked`, or `timed_out` state.
- Require a new approval request if the task is still valid.

## Denied Approval Behavior

If approval is denied:

- No approval token is issued.
- The task or action moves to `blocked`, `denied`, or equivalent terminal state.
- Denial reason is recorded without raw sensitive payloads.
- Evidence is recorded.
- Repeated attempts with the same denied scope may trigger `incident.ops`.

## Timeout And Supersession Behavior

If an approval request times out:

- Mark the request expired.
- Revoke any issued token.
- Block the action.
- Record evidence.

If an approval request is superseded:

- The previous request can no longer issue tokens.
- Any token from the previous request is revoked.
- The new request must carry narrowed or changed scope explicitly.

## Replay Rejection And Scope Mismatch

Replay, reuse, or mismatch must:

- Deny action.
- Revoke the token.
- Record evidence.
- Create an incident when suspicious or repeated.

Scope mismatch includes tenant, customer context, task, action, resource refs,
allowed operations, prohibited operations, capability lease, worker/helper
identity, approval request, approval result, approval token, token
verification, Guardian decision, policy version, policy snapshot, scope hash,
evidence refs, or data classification mismatch.

## Partial Approval Behavior

Partial approval is not execution authorization.

If an approver narrows scope, the system must create a superseding approval request or an explicit narrowed token whose scope is no broader than the approved subset. If scope cannot be represented clearly, the action fails closed.

## Emergency / Breakglass Placeholder

Breakglass is not implemented in Phase 0.

Any future breakglass policy must define:

- Eligible roles.
- Additional authentication assumptions.
- Maximum duration.
- Mandatory evidence.
- Post-review requirements.
- Incident linkage.
- Actions that remain blocked even during breakglass.

Until then, breakglass requests are denied or handled outside runtime.

Worker, helper agent, model, tool, or supervisor self-approval is not allowed. Only a human operator or approver role can approve.

## Evidence Required At Every Stage

Evidence is required for:

- Guardian `requires_approval`.
- Approval request creation.
- Approval review.
- Approval approval or denial.
- Token issuance.
- Token use.
- Token expiry.
- Token revocation.
- Scope mismatch.
- Replay or reuse attempt.
- Privileged action completion or block.

Approval evidence should include:

- Presented scope hash.
- Approved scope hash.
- Approver role snapshot.
- Approver identity assurance placeholder.
- Approval channel placeholder.
- Decision reason class.
- Whether tainted content was involved.

## Failure Behavior

Privileged action must fail closed if the token is:

- Missing.
- Expired.
- Revoked.
- Already used.
- Mismatched to tenant, task, action, resource, approver, Guardian decision, or request.
- Ambiguous.
- Unsupported by evidence.

## MVP Acceptance Gates

- Approval request and token records contain no secret material.
- External send remains draft/dry-run unless future approved policy permits live send.
- File deletion without matching approval is denied.
- LIMA IT remediation cannot proceed beyond draft/request metadata without approval and evidence; execution remains blocked in Phase 0.
- Expired, revoked, mismatched, or missing tokens block action execution.
- Approval lifecycle links to `guardian.decision`, `approval.request`, `approval.token`, action contract, and `evidence.artifact`.
- Approval-required mock runtime paths require `approval.binding`; token
  verification alone is not sufficient.
- Replay, scope widening, tenant mismatch, task mismatch, worker mismatch,
  action mismatch, Guardian mismatch, blocked-MVP action, tainted chain, and
  missing evidence fail closed in tests.
