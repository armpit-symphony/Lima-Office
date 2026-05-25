# Attestation Reference Value Governance

## Purpose

Define governance controls for appraisal policies, reference values, and
endorsement metadata used by future worker attestation verification.

Status: metadata-only policy posture. No verifier runtime is implemented.

## Ownership and Accountability

- Create reference values: worker owner or field IT reviewer.
- Approve reference values: security reviewer or designated approver.
- Revoke reference values: security reviewer with evidence and incident linkage.
- Verifier-owner placeholder: SparkPit/operator policy authority.

No single actor should create and approve high-impact trust metadata without
separation-of-duties review.

## Reference Value Lifecycle

- `proposed`
- `approved`
- `active`
- `deprecated`
- `revoked`
- `blocked_mvp`

`active` requires approval ref, policy refs, evidence refs, and timestamped
approval event.

## Endorsement Lifecycle

- `collected`
- `trusted_placeholder`
- `untrusted`
- `revoked`
- `expired`
- `blocked_mvp`

`trusted_placeholder` is metadata-only and not equivalent to cryptographic trust
implementation.

## Reference Governance Scope

- model bundle references
- runtime bundle references
- policy bundle references
- config references
- update artifact references
- rollback target references

Each class must preserve evidence linkage and revocation trail.

## Separation of Duties

- Proposer cannot self-approve for high-risk trust-root changes.
- Revocation and reactivation cannot be performed by the same identity in a
  single review chain.
- Privileged model-route posture cannot rely on unapproved or revoked reference
  values.

## Evidence Requirements

- proposed/approved/active/deprecated/revoked transitions require evidence refs.
- revocation requires reason codes and revocation timestamp.
- trust-affecting decisions require policy refs and reviewer identity refs.

## Audit and Export Posture

- Attestation governance records must remain metadata-only.
- Evidence exports remain policy-governed and blocked from raw secret/customer
  payload inclusion.
- Historical trust changes must remain auditable through reason/evidence refs.

## MVP Blocked Behavior

- Missing trust metadata: fail closed.
- Revoked/deprecated trust metadata in privileged paths: blocked or quarantine.
- Blocked-MVP states cannot be interpreted as trusted.
- No live update distribution, signing service, verifier service, or TPM runtime.

Verifier-owner and authority lifecycle controls are expanded in
[Verifier Owner Authority Policy](VERIFIER_OWNER_AUTHORITY_POLICY.md).
