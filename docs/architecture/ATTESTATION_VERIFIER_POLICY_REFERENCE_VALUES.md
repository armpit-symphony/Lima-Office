# Attestation Verifier Policy Reference Values

Status: design-only / not implemented.

## Purpose

Define a metadata-only, fail-closed verifier posture for worker attestation
using appraisal policy, reference values, endorsements, and attestation results.

## RATS Role Mapping

- Arc worker node: Attester.
- Supervisor: Relying Party.
- Future verifier component: Verifier.
- SparkPit/operator policy owner: Verifier Owner / Relying Party Owner
  placeholder.

## Evidence Inputs

- `worker.attestation`
- `worker.deployment`
- `worker.lifecycle`
- `worker.heartbeat`
- `update.rollback`
- `governance.device_trust`
- `model.route`

## Appraisal Policy Model

Appraisal policy is represented by `attestation.appraisal_policy` and defines:

- required reference-value types
- required endorsement types
- required evidence types
- freshness and clock-skew thresholds
- fail-closed behavior for missing/stale inputs
- worker-role and action-type applicability

Inactive, revoked, deprecated, or missing appraisal policy is fail-closed.

## Reference Value Model

Reference values are represented by `attestation.reference_value` and define
approved hash metadata for:

- OS image
- Arc runtime bundle
- policy bundle
- model bundle
- config bundle
- update artifacts
- rollback targets

Raw artifact payloads are out of scope and blocked in MVP.

## Endorsement Model

Endorsements are represented by `attestation.endorsement` as metadata-only
placeholder trust signals. No certificate parsing, chain validation, OCSP/CRL,
or hardware attestation service exists in this lane.

## Attestation Result Model

Attestation output is represented by `attestation.result`:

- appraisal outcome (`pass`, `fail`, `inconclusive`, `expired`, `blocked_mvp`)
- trust effect (`trusted_metadata_only`, `degraded`, `quarantine_required`,
  `revoked`, `blocked_mvp`)
- reason and evidence refs
- expiry boundaries

`trusted_metadata_only` is informational and never runtime authorization.

## Trust-Boundary Model

- Worker evidence is untrusted input until appraised.
- Reference values and appraisal policy are governance-controlled metadata.
- Endorsements are placeholder metadata only; unknown/revoked/expired signals
  fail closed.
- Supervisor consumes attestation result metadata; it does not perform real
  attestation verification in this phase.

## Freshness and Expiry Rules

- Attestation evidence freshness is policy-driven (`freshness_seconds` plus
  `clock_skew_allowance_seconds`).
- Expired results or stale reference values force degrade/quarantine posture.
- Missing timestamps or ambiguous ordering fail closed.

## Versioning Rules

- `taxonomy_version` is required on all reason-bearing records.
- Appraisal policy, reference values, and endorsements are versioned via IDs and
  status lifecycle fields.
- Revocation/deprecation must preserve prior evidence lineage.

## Failed Appraisal Behavior

- `appraisal_result: fail` requires reason/evidence refs.
- Worker is marked degraded or quarantine-required.
- Privileged model-route metadata is blocked when appraisal or trust refs fail.

## Quarantine Behavior

- Failed/expired/inconclusive trust posture maps to worker lifecycle
  degradation/quarantine states.
- New privileged assignments remain blocked.
- Recovery requires new attestation metadata and reviewer evidence.

## Model-Route Block Behavior

When attestation/ref-value/endorsement/appraisal is missing, stale, revoked, or
inconclusive for privileged contexts:

- route must be denied/blocked/unavailable
- route reason codes must include trust-appraisal reason signals
- evidence refs are required

No model execution is performed.

## Rollback and Update Linkage

- `update.rollback` records provide artifact trust metadata that can influence
  appraisal and route blocking.
- Untrusted model/runtime/policy bundle updates must fail closed in attestation
  and model-route posture.

## Evidence Requirements

- All fail/degrade/block decisions require evidence refs.
- Result records include references to policy, endorsement, reference-value, and
  source attestation metadata.
- No raw TPM quotes, certs, private keys, signatures, or secrets are stored.

## Non-Goals

- Real TPM access or quote verification.
- Real verifier service.
- Real cryptographic or certificate validation.
- Real update/rollback execution.
- Runtime authorization.

## Future Implementation Gates

1. Select attestation method and trust-root authority.
2. Implement verifier service and appraisal engine.
3. Implement real endorsement source validation and revocation checks.
4. Add durable attestation/result history and reconciliation storage.
5. Bind runtime task/model routing to verified trust state under explicit
   approval.

## Acceptance Gates

- Contracts and examples exist for reference values, endorsements, appraisal
  policy, and attestation results.
- Fail-closed tests cover missing/stale/revoked policy inputs.
- Model-route privileged metadata paths block on failed attestation appraisal.
- No runtime attestation/verifier/signature/update behavior is implemented.

## Durable Lineage Extension

Durable lineage and authority hardening is defined in
[Durable Attestation Result Lineage](DURABLE_ATTESTATION_RESULT_LINEAGE.md) and
[Verifier Owner Authority Policy](../governance/VERIFIER_OWNER_AUTHORITY_POLICY.md),
with operator drill posture in
[Attestation Revocation Propagation](../runbooks/attestation-revocation-propagation.md).
