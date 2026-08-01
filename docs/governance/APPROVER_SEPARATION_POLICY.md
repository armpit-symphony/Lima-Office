# Approver Separation Policy

## Purpose

Define who may approve high-risk LIMA Office actions and which self-approval
or conflict cases remain blocked.

Policy ref: `policy.approver_separation.phase0`

Status: draft scaffold. This policy does not implement an approval service or
authorize runtime action.

Companion matrix: [RBAC IdP MFA Session Device Trust Matrix](RBAC_IDP_MFA_SESSION_DEVICE_TRUST_MATRIX.md).

## Who May Approve What

| Action class | Required approver posture | MVP posture |
| --- | --- | --- |
| Low-risk internal draft | Operator review may be enough when policy allows | Mock/draft only |
| File delete, overwrite, export, or customer record mutation | Approver distinct from requester; evidence required | Approval-required or blocked |
| External email/text/chat or form submission | Approver distinct from requester; fresh intent required | Blocked for MVP |
| Live connector scope change | Connector owner plus security reviewer | Blocked for MVP |
| Sensitive HR, finance, legal, medical, or secret access | Approver plus security/compliance reviewer as policy requires | Approval-required or blocked |
| Worker enrollment, release, revoke, or re-enrollment | Operator plus field IT or security reviewer depending on reason | Manual docs/runbook only |
| Software install/update or rollback | Field IT reviewer plus operator approval | Non-executing docs/runbook only |
| LIMA IT remediation request | LIMA IT reviewer cannot be sole approver for execution | Remediation execution blocked |

## LIMA IT Remediation Approver Separation

- The person requesting LIMA IT remediation cannot be the sole approver.
- The LIMA IT reviewer preparing diagnostic handoff cannot approve execution of
  their own remediation recommendation.
- Production server touch, endpoint control, network change, software install,
  and remediation execution remain blocked in MVP even when a request record
  exists.
- Read-only diagnostic handoff may be reviewed separately from remediation
  requests.

## Worker Owner Vs Approver Separation

- A worker owner may request enrollment, release, or re-enrollment.
- Security quarantine release requires a security reviewer separate from the
  worker owner.
- Field IT readiness approval should be separate from the operator requesting
  assignment.
- Identity mismatch, attestation failure, evidence failure, or suspicious
  capability drift cannot be self-approved.

## Emergency/Breakglass Exception Placeholder

- Breakglass remains placeholder-only and blocked for runtime.
- Future breakglass must define separate emergency approver, expiry, evidence,
  incident linkage, and post-use review.
- Breakglass cannot permit MVP-blocked actions such as live connectors,
  external sends, production touch, or remediation execution.

## Conflict Of Interest Handling

Conflict indicators:

- Requester and approver identity refs match.
- Approver owns the target worker, connector, system, or evidence record.
- Approver is the direct beneficiary of the action.
- Approver created or modified the policy bundle under review.

Conflict handling:

- Mark the approval request as conflicted.
- Require an independent approver or security/compliance reviewer.
- Record evidence and denial or supersession when no independent approver is
  available.

## Approval Evidence Requirements

- Approval request ID.
- Guardian decision ID.
- Approver identity ref and role ref.
- Scope hash.
- Policy refs.
- Evidence refs.
- Decision time.
- Denial, expiry, cancellation, or conflict reason when not approved.

Approval evidence must not contain credentials, secret values, raw sensitive
payloads, or bearer token material.

## Blocked Self-Approval Cases

- Requester approves their own high-risk action.
- Worker owner releases their own worker from security quarantine.
- LIMA IT reviewer approves their own remediation execution.
- Connector owner expands connector scope without security review.
- Supervisor admin approves their own privileged role escalation.
- Breakglass invocation approves itself.

## MVP Acceptance Gates

- Approval records include distinct requester and approver refs where required.
- `governance.rbac_matrix` records mark `approve_lima_it_remediation` as either
  `blocked_mvp` or separation-of-duties-required metadata only.
- `approval.binding` records include requester/approver refs, approver role,
  separation check result, identity assurance refs, and evidence refs before
  any approval-required mock path can proceed.
- Self-approval and conflicted approval records fail closed.
- LIMA IT remediation execution remains blocked.
- All approval outcomes create evidence.
- Policy ambiguity results in denial or blocked-MVP metadata.
