# Breakglass Policy

## Purpose

Define the emergency access placeholder for LIMA Office OS while keeping
breakglass blocked until a future explicit implementation gate.

Policy ref: `policy.breakglass.phase0`

Status: blocked placeholder. No breakglass runtime path is implemented or
authorized.

## When It May Be Used

Future breakglass may be considered only for:

- Restoring operator access during identity provider outage.
- Containing a security incident when normal approval workflow is unavailable.
- Quarantining or revoking a suspected compromised worker.
- Preserving evidence when the normal evidence path is degraded.

These are planning examples, not runtime authorization.

## When It Must Not Be Used

Breakglass must not be used to:

- Send external email/text/chat or submit forms.
- Enable live connectors or OAuth/provider wiring.
- Access or mutate production systems.
- Execute remediation, software install/update, endpoint control, or network
  changes.
- Bypass tenant isolation, prompt-injection controls, evidence, or audit.
- Approve financial, legal, HR discipline, medical, payment, or regulated-system
  decisions.

## Required Approver And Evidence

Future breakglass requires:

- Requester identity ref.
- Independent emergency approver identity ref.
- MFA or emergency identity proof posture.
- Reason code.
- Scope and expiry.
- Guardian decision.
- Incident link.
- Evidence refs.
- Post-use review assignment.

Missing evidence or ambiguous approver posture fails closed.

## Expiry

- Breakglass must be short-lived.
- Exact TTL is unresolved.
- Expired breakglass cannot be renewed automatically.
- Any renewal must create a new request, evidence, and review record.

## Post-Use Review

Post-use review must capture:

- Who invoked breakglass.
- Who approved it.
- What scope was granted.
- What actions occurred.
- What evidence was preserved.
- Which actions were denied or blocked.
- Whether access was revoked on time.
- Follow-up incident or policy changes.

## Revocation

- Breakglass must be revocable before expiry.
- Revocation must invalidate remaining scope.
- Revocation must create audit evidence.
- Unknown revocation state fails closed.

## Audit Requirements

- Breakglass request, decision, expiry, revoke, and review records must be
  export-aware and redaction-aware.
- Audit records must not contain credentials, secrets, raw customer payloads,
  or private token material.
- Breakglass records must link to incident and evidence refs.

## MVP Placeholder Status

Breakglass in this repo is represented only by
`governance.breakglass` metadata and the [Breakglass Review](../runbooks/breakglass-review.md)
runbook. It is not an executable capability.

## Blocked Runtime Behavior

Until future policy, contracts, tests, and implementation gates explicitly
approve breakglass:

- No breakglass token is valid.
- No breakglass session can perform actions.
- No MVP-blocked action can be reclassified as allowed.
- Runtime must deny or block when breakglass state is missing, active but
  unimplemented, expired, ambiguous, or lacking evidence.
