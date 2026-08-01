# Attestation Revocation Reconciliation Drills

Status: design-only metadata posture, not implemented runtime automation.

## Purpose

Define fail-closed reconciliation drills so attestation revocation and trust
propagation cannot drift across lineage, authority, worker/device trust,
model-route posture, transactions, and evidence metadata.

## Problem Statement

Individually valid contracts can still be unsafe together if revocation,
expiry, quarantine, authority, and transaction/evidence linkage disagree.
This drill posture ensures those disagreements are classed as drift and
blocked.

## Lineage Reconciliation Graph

- `attestation.result.lineage`
- `attestation.authority`
- `attestation.reference_value`
- `attestation.endorsement`
- `attestation.appraisal_policy`
- `attestation.result`
- `worker.attestation`
- `governance.device_trust`
- `model.route`
- `worker.lifecycle`
- `worker.heartbeat`
- `update.rollback`
- `transaction.boundary`
- `transaction.coordinator.event`
- `evidence.ledger.entry`

## Drift Classes

- `reference_value_revoked_but_lineage_current`
- `endorsement_revoked_but_result_trusted`
- `appraisal_policy_revoked_but_route_selected`
- `attestation_result_expired_but_worker_active`
- `revocation_pending_but_privileged_route_selected`
- `quarantine_required_but_worker_active`
- `model_route_selected_with_untrusted_lineage`
- `transaction_committed_with_revoked_attestation`
- `evidence_missing_for_revocation`
- `cross_tenant_attestation_linkage`
- `verifier_authority_revoked_but_appraisal_active`

## Fail-Closed Reconciliation Rules

- Any cross-tenant attestation linkage is `failed_closed`.
- Any revoked/stale/conflicted lineage in privileged route contexts is blocked.
- Revocation-pending lineage cannot be treated as selected privileged
  model-route posture.
- Revoked verifier authority cannot coexist with active appraisal acceptance.
- Committed transaction metadata cannot coexist with revoked/untrusted
  attestation trust effects.
- Missing revocation evidence in revocation/replay-denial/drift paths is
  blocked.
- Quarantine-required trust posture cannot coexist with active worker execution
  posture.

## Evidence Requirements

- Reconciled results require evidence refs for lineage and authority inputs.
- Drift, `revocation_pending`, `quarantine_required`, and `failed_closed`
  outcomes require evidence refs.
- Revocation propagation steps must bind to evidence ledger refs and
  transaction/coordinator refs where available.

## Operator Visibility

- Console and supervisor health records must expose reconciliation drift and
  blocked posture using canonical reason codes.
- Reconciliation outcomes are metadata-only and never authorize runtime action.

## Drill Scenarios

- Revoke a reference value while lineage stays `current`.
- Revoke an endorsement while attestation result remains trusted.
- Revoke appraisal policy while route remains selected.
- Expire attestation result while worker remains active.
- Keep revocation propagation pending while privileged route is selected.
- Require quarantine while worker lifecycle remains active.
- Force transaction committed while lineage is revoked.
- Remove denial/revocation evidence refs and verify fail-closed response.
- Inject cross-tenant lineage and verify failed_closed classification.

## MVP Non-Goals

- No real TPM access or attestation verification.
- No real verifier service or cryptographic checks.
- No real update/rollback execution.
- No durable production storage, queues, or orchestration services.
- No runtime authorization or remediation execution.
