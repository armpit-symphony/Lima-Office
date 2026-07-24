# Verifier Owner Authority Policy

Status: design-only governance policy for Phase 1A metadata hardening.

## Purpose

Define who can approve/revoke attestation trust inputs and who can accept or
reject attestation trust results in a fail-closed, separation-of-duties model.

## Roles

- Verifier owner
- Relying party owner
- Reference-value approver
- Endorsement reviewer
- Device-trust reviewer
- Security reviewer
- Field IT reviewer

## Separation of Duties

- High-impact trust actions require separation of duties metadata.
- Quarantine-clearance authority requires explicit SoD metadata.
- No self-approval requirement bypasses are allowed.
- Breakglass remains blocked in MVP.

## Authority Controls

- Who can approve reference values: reference-value approver authority only.
- Who can revoke reference values: reference-value approver authority only.
- Who can approve appraisal policies: verifier owner or relying-party owner
  authority.
- Who can accept attestation results: verifier owner authority.
- Who can clear quarantine: explicit authority with SoD required.
- Who can override trust failures in MVP: no one.

## Evidence Requirements

- Approval/revocation/suspension/expiry actions require evidence refs.
- Failed-closed and blocked-MVP transitions require reason/evidence linkage.
- Access review and authority lifecycle decisions must be evidence-linked.

## Access Review Linkage

- Authority records should map to governance access-review posture and RBAC
  role metadata.
- Revoked/expired authority must propagate to trust posture and model-route
  blocked/degraded outcomes.

## MVP Acceptance Gates

- `attestation.authority` schema/examples validated.
- SoD-required actions represented and tested.
- Revoked/expired authority fail-closed behavior tested.
- No breakglass override path for trust decisions in MVP.

## Reconciliation Linkage

- Authority lifecycle state must reconcile against
  `attestation.result.lineage` and `attestation.reconciliation`.
- Revoked/suspended/expired verifier-owner authority cannot coexist with active
  appraisal acceptance; this must produce fail-closed reconciliation drift.
- Drill posture is defined in
  [ATTESTATION_REVOCATION_RECONCILIATION_DRILLS](../ATTESTATION_REVOCATION_RECONCILIATION_DRILLS.md)
  and
  [attestation-reconciliation-drill](../runbooks/attestation-reconciliation-drill.md).
