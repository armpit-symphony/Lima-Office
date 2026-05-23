# Approval Inbox Spec

The approval inbox lets an allowed human reviewer approve or deny metadata
requests. It does not execute work by itself.

## Approval Request Card

Each request card must show:

- Approval request ID.
- Task ID and affected worker/task/connector/system refs.
- Requested action.
- Requester identity ref.
- Approver role requirement.
- Risk tier.
- Data classification.
- Guardian decision ID.
- Guardian issued/effective/expires timestamps, decision nonce status, and
  replay-check status.
- Policy refs and policy version.
- Evidence/pre-evidence refs.
- Taint status.
- Token scope and scope hash.
- Expiration time.
- Current status.
- Runbook link.

## Risk Tier

- `medium`: approval may be possible if policy, evidence, role, and separation
  gates pass.
- `high`: require stronger review, evidence, and no self-approval.
- `blocked`: deny/block; no approval token.

## Policy Result

The card must show whether Guardian returned:

- `requires_approval`.
- `deny`.
- `block_mvp`.
- `quarantine_subject`.

Approve controls must not appear for deny, block-MVP, expired, revoked,
evidence-missing, token-mismatch, self-approval, or tainted blocked states.

## Evidence And Pre-Evidence

The inbox must show:

- Evidence artifact IDs.
- Evidence failure state.
- Redaction profile.
- Related incident ref if present.

If pre-action evidence is required and missing, the request is blocked.

## Taint Status

Tainted or suspected prompt-injection input must be visible. Tainted input
cannot create fresh approval intent and cannot directly authorize tool use,
external sends, durable memory writes, connector actions, or remediation.

## Token Scope

Approval tokens are metadata refs only. The card shows:

- Token ID when issued.
- Approval chain ID and binding ID when available.
- Scope hash.
- Max uses.
- Expiry.
- Revocation state.
- Token verification result where relevant.
- Binding mismatch reasons, nonce/replay status, and evidence refs.
- Guardian replay-check result and decision scope hash when available.

The inbox never displays bearer token material.

## Deny Reasons

Deny reasons must be selectable from policy-defined reason codes or entered as
redacted summaries. Denial creates evidence and must not expose raw customer
payloads or secrets.

## Blocked-MVP Labeling

Blocked-MVP requests must show:

- Blocked action class.
- Policy ref.
- Guardian decision.
- Evidence ref.
- Explanation that no approval token can be issued.

## Approve/Deny UX

Approve and deny are spec-only controls. Future implementation must:

- Require fresh operator intent.
- Re-check role and separation.
- Re-check Guardian decision, replay status, policy refs, evidence, expiry,
  clock-skew posture, and taint state.
- Record `approval.result`.
- Issue token metadata only when allowed by policy.
- Require a matching `approval.binding` before any mock/dry-run
  approval-required path can proceed; display-only approval is not execution
  authorization.

## Fail-Closed UX

Show blocked state and disable approval-capable controls when any required
field is missing, stale, contradictory, expired, revoked, mismatched, tainted,
replayed, future-effective beyond skew allowance, or outside role scope.
