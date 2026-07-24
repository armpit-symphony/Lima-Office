# Durable Attestation Result Lineage

Status: design-only, not implemented.

## Purpose

Define metadata-only lineage for attestation trust decisions so revocation,
quarantine, update/rollback, and model-route posture cannot drift across
contracts while still appearing individually valid.

## Durable Lineage Problem Statement

In-memory appraisal output is insufficient for future lab/production posture:

- stale attestation results can outlive revoked reference values;
- revoked endorsements can fail to propagate to device trust and route posture;
- rollback-required updates can diverge from worker trust state;
- reconciliation/audit chains can become ambiguous without explicit lineage.

## Lineage Graph

The canonical lineage chain is:

- `worker.attestation`
- `attestation.reference_value`
- `attestation.endorsement`
- `attestation.appraisal_policy`
- `attestation.result`
- `attestation.result.lineage`
- `attestation.authority`
- `governance.device_trust`
- `worker.lifecycle`
- `worker.heartbeat`
- `model.route`
- `update.rollback`
- `evidence.ledger.entry`
- `transaction.boundary`

## Verifier-Owner / Reference / Endorsement Authority Model

- Verifier-owner authority is modeled by `attestation.authority`.
- Reference-value approval/revocation authority is explicit metadata, not
  implicit role trust.
- Endorsement reviewer authority is explicit metadata with reason/evidence
  linkage.
- Authority revocation/suspension/expiry must fail closed for trust decisions.

## Freshness, Expiry, Revocation, and Quarantine Propagation

- `attestation.result.lineage.expires_at` is required for current trust posture.
- `lineage_status` and `revocation_propagation_status` model stale/revoked/
  conflicted/pending/failed-closed conditions.
- Pending or failed revocation propagation is non-authorizing and must block
  privileged model-route and worker capability posture.
- Quarantine-required lineage must bind `worker_lifecycle_ref` and evidence.

## Rollback/Update and Model-Route Trust Propagation

- `update.rollback` records must be linkable from lineage records.
- Model-route records should carry lineage/authority refs where trust-sensitive
  route selection is represented.
- Trust-conflicted, stale, revoked, or pending-propagation lineage must map to
  denied/blocked/degraded model-route outcomes only.

## Evidence and Ledger Linkage

- Lineage is metadata-only and refs-only.
- Each critical lineage transition must include `evidence_refs`.
- Ledger/transaction refs are required for durable chain reconstruction in
  future implementation phases.

## Reconciliation Drill Linkage

- `attestation.reconciliation` is the fail-closed reconciliation output that
  binds lineage + authority + reference-value + endorsement + appraisal +
  result posture to worker/device/model-route/transaction/evidence metadata.
- Drift classes (for example revoked reference with current lineage, selected
  route with untrusted lineage, or committed transaction with revoked
  attestation) must never be represented as trusted posture.
- Operator drill/runbook posture is defined in
  [ATTESTATION_REVOCATION_RECONCILIATION_DRILLS](../ATTESTATION_REVOCATION_RECONCILIATION_DRILLS.md)
  and
  [attestation-reconciliation-drill](../runbooks/attestation-reconciliation-drill.md).

## Export/Delete Placeholders

- Export/delete behavior remains placeholder-only.
- Future export/delete implementations must preserve lineage integrity and
  capture delete-conflict evidence without raw content/secrets.

## Fail-Closed Rules

- Missing verifier authority: fail closed.
- Revoked/suspended/expired authority for trust decisions: fail closed.
- Stale/revoked/conflicted lineage: fail closed for privileged posture.
- Revocation propagation pending/failed-closed: fail closed.
- Blocked-MVP lineage/authority states cannot be represented as trusted.

## MVP Non-Goals

- No durable storage implementation.
- No TPM/quote verification.
- No certificate/signature verification service.
- No runtime authorization expansion.
- No update distribution/rollback automation.

## Future Implementation Gates

- Durable storage and atomic propagation across lineage/authority/device trust.
- Explicit revocation-generation monotonicity controls.
- Verified owner-of-authority governance and access-review integration.
- Durable evidence export chain with delete-conflict proof posture.

## Acceptance Gates Before Implementation

- All lineage/authority schemas and examples validate.
- Cross-contract tests prove fail-closed propagation behavior.
- Reason-code registry parity includes lineage/authority codes.
- Runbook coverage exists for revocation propagation operations.
