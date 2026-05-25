# Attestation Verifier Review

## Purpose

Provide operator/security review steps for metadata-only attestation verifier
posture and reference-value governance checks.

This runbook describes design-time review posture. It does not implement
automated attestation, certificate verification, TPM access, or rollback
execution.

## When To Use

- before approving trust metadata changes
- after attestation failure or inconclusive appraisal records
- before privileged route posture review in lab simulations

## Prerequisites

- access to relevant contracts/examples and policy docs
- reviewer role assignment (security reviewer + field IT as needed)
- evidence destination refs prepared

## Review Appraisal Policy Metadata

1. Confirm policy status is active/approved for intended context.
2. Verify required reference-value, endorsement, and evidence type arrays exist.
3. Verify freshness/clock-skew posture is present.
4. Confirm fail-closed flags are enabled for missing/stale inputs.

## Review Reference Values

1. Confirm reference status and lifecycle state are valid for use.
2. Check value hash and hash algorithm metadata are populated.
3. Confirm approval refs, policy refs, and evidence refs exist for active state.
4. Validate scope applicability (worker roles/IDs/deployment IDs).

## Review Endorsements

1. Confirm endorsement type and status.
2. For trusted placeholder state, confirm issuer/validity/policy/evidence refs.
3. Deny usage if revoked/expired/untrusted/blocked-MVP.

## Review Attestation Results

1. Verify appraisal policy linkage and reference/endorsement refs are present.
2. Validate result expiry and evidence refs.
3. Confirm trust effect aligns with appraisal result and reason codes.
4. Ensure blocked-MVP results are not interpreted as trusted metadata.

## Failure Scenarios

- missing reference value
- stale reference value
- revoked endorsement
- mismatched worker hash
- expired attestation result
- model bundle untrusted
- rollback target mismatch

## Operator Steps

1. Mark impacted worker as degraded or quarantine-required in metadata.
2. Block privileged route metadata for impacted worker scope.
3. Record reason codes and evidence refs.
4. Request security review for trust-root/policy changes.
5. Request field IT review if device/runtime integrity drift is suspected.

## Evidence To Capture

- reference value record IDs and status transitions
- endorsement record IDs and validity status
- appraisal policy ID and version
- attestation result IDs and trust effects
- model-route block records and reason codes
- update/rollback linkage refs

## Quarantine/Rollback Steps

- set worker lifecycle posture to degraded or quarantined
- preserve update/rollback metadata references
- maintain fail-closed state until policy inputs are reconciled

## Escalation

- security architect for trust-root or policy revocation decisions
- SRE/field IT for worker isolation and recovery planning
- governance reviewer for evidence/audit gaps

## Done Criteria

- all missing/stale/revoked inputs are classified with fail-closed metadata
- evidence refs are captured for each decision
- privileged routes remain blocked until trust posture is restored
- no runtime attestation/update action was executed
