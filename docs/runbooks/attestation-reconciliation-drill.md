# Attestation Reconciliation Drill

Status: runbook posture design. Not implemented automation.

## Purpose

Provide an operator drill to detect and contain drift between attestation
lineage/authority metadata and route/transaction/evidence posture.

## When To Run

- After any attestation revocation metadata update.
- During periodic security posture validation.
- After model-route trust incidents involving attestation inputs.
- After transaction/evidence reconciliation failures for attestation-linked
  actions.

## Preconditions

- Operator has read access to attestation, worker, route, transaction, and
  evidence metadata contracts.
- Required runbooks are available:
  - `attestation-revocation-propagation`
  - `transaction-recovery-reconciliation`
- Any privileged containment action remains approval-gated and blocked for real
  runtime execution in MVP.

## Drill Scenarios

- Reference value revoked but lineage still current.
- Endorsement revoked while result remains trusted.
- Appraisal policy revoked while model route is selected.
- Attestation result expired while worker lifecycle is active.
- Revocation propagation pending while privileged route is selected.
- Quarantine required while worker remains active.
- Transaction marked committed while attestation is revoked.
- Cross-tenant attestation linkage drift.
- Revoked verifier authority while appraisal remains active.

## Operator Steps

1. Locate lineage record and verify `lineage_status`, `trust_effect`, and
   `revocation_propagation_status`.
2. Verify verifier-owner and reviewer authority metadata for active/non-revoked
   posture.
3. Verify reference values, endorsements, and appraisal policy status.
4. Verify attestation result expiry and trust effect.
5. Check worker lifecycle, heartbeat, and device-trust posture for quarantine
   consistency.
6. Check related model-route records for denied/blocked posture under trust
   drift.
7. Check related transaction/coordinator/ledger records for no committed success
   state under revoked trust.
8. Validate evidence refs exist for each detected drift or revocation decision.
9. Record reconciliation output as metadata-only (`reconciled`, `drift_detected`,
   `revocation_pending`, `quarantine_required`, `failed_closed`, `blocked_mvp`).

## Records To Inspect

- `attestation.result.lineage`
- `attestation.authority`
- `attestation.reference_value`
- `attestation.endorsement`
- `attestation.appraisal_policy`
- `attestation.result`
- `worker.attestation`
- `worker.lifecycle`
- `worker.heartbeat`
- `governance.device_trust`
- `model.route`
- `transaction.boundary`
- `transaction.coordinator.event`
- `evidence.ledger.entry`

## Evidence To Capture

- Revocation trigger evidence refs.
- Authority status evidence refs.
- Route blocking evidence refs.
- Quarantine consistency evidence refs.
- Transaction/ledger drift evidence refs.
- Reconciliation decision evidence refs.

## Expected Fail-Closed Outcomes

- Drifted or revoked trust never appears as privileged route success.
- Cross-tenant linkage always returns failed_closed posture.
- Missing revocation evidence forces failed_closed posture.
- Revoked verifier authority blocks trust acceptance.

## Quarantine/Rollback Review

- Confirm quarantine-required posture appears in worker lifecycle metadata.
- Confirm rollback-required metadata is represented for impacted updates.
- Do not execute remediation in this runbook; only record required follow-up.

## Escalation

- Security reviewer for authority or cross-tenant drift.
- SRE/Field IT reviewer for quarantine lifecycle drift.
- Software architect for transaction/ledger consistency drift.

## Done Criteria

- Reconciliation status recorded with evidence refs.
- Drift classes and reason codes captured for each scenario.
- No metadata path reports successful trusted posture when drift exists.
- All outcomes remain metadata-only and non-authorizing.
