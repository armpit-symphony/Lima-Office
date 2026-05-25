# Worker Attestation Policy

## Purpose

Define the worker identity and attestation posture required before Arc worker
re-enrollment or higher-trust lab runtime expansion.

Policy ref: `policy.worker_attestation.phase0`

Status: placeholder scaffold. No hardware attestation implementation exists.

## Worker Identity

Worker identity requires:

- `worker_id`.
- Device identity ref.
- Channel identity ref.
- Deployment ID.
- Tenant/customer context.
- Capability manifest hash ref.
- Policy bundle hash ref.
- Model bundle hash ref when applicable.
- Evidence refs.

Worker identity cannot approve human actions and cannot replace operator MFA.

## Hardware/TPM/Secure Boot Future Preference

- TPM or equivalent device identity support is preferred.
- Secure boot posture should be recorded where available.
- Hardware attestation method is not selected yet.
- `not_required_phase0` means weak lab trust, not elevated trust.

## Policy Hash Verification

- Worker policy bundle hash must match the Supervisor-approved policy ref.
- Hash mismatch causes degrade, quarantine, or re-enrollment pending state.
- Missing policy hash blocks assignment.

## Model Hash Verification

- Local model bundles require model bundle ref and hash ref.
- Cloud/subscription-model posture remains metadata-only.
- External model calls remain blocked until model routing policy and egress
  gates are approved.

## Runtime Version Hash Placeholder

- Worker runtime version hash is a future requirement.
- This policy records the expectation only.
- No updater, daemon, or runtime verification service is implemented.

## Deployment Contract Link

Attestation posture is recorded in:

- [worker.deployment.schema.json](../../contracts/v1/worker.deployment.schema.json)
- [worker.lifecycle.schema.json](../../contracts/v1/worker.lifecycle.schema.json)
- [worker.heartbeat.schema.json](../../contracts/v1/worker.heartbeat.schema.json)
- [governance.device_trust.schema.json](../../contracts/v1/governance.device_trust.schema.json)
- [worker.attestation.schema.json](../../contracts/v1/worker.attestation.schema.json)
- [attestation.reference_value.schema.json](../../contracts/v1/attestation.reference_value.schema.json)
- [attestation.endorsement.schema.json](../../contracts/v1/attestation.endorsement.schema.json)
- [attestation.appraisal_policy.schema.json](../../contracts/v1/attestation.appraisal_policy.schema.json)
- [attestation.result.schema.json](../../contracts/v1/attestation.result.schema.json)
- [attestation.result.lineage.schema.json](../../contracts/v1/attestation.result.lineage.schema.json)
- [attestation.authority.schema.json](../../contracts/v1/attestation.authority.schema.json)
- [attestation.reconciliation.schema.json](../../contracts/v1/attestation.reconciliation.schema.json)
- [Attestation Reference Value Governance](ATTESTATION_REFERENCE_VALUE_GOVERNANCE.md)
- [Verifier Owner Authority Policy](VERIFIER_OWNER_AUTHORITY_POLICY.md)

## Failed Attestation Behavior

Failed, missing, ambiguous, or mismatched attestation posture requires:

- Quarantine or revoke.
- Assignment block.
- Evidence refs.
- Security reviewer review.
- Re-enrollment runbook.
- `reason_codes` indicating `attestation_required` or `attestation_failed`.

## Quarantine/Re-Enrollment Linkage

Attestation failure links to:

- [Worker Lifecycle](../deployment/WORKER_LIFECYCLE.md)
- [Worker Deployment Blueprint](../deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)
- [Worker Attestation Failure Runbook](../runbooks/worker-attestation-failure.md)
- [Worker Attestation Review Runbook](../runbooks/worker-attestation-review.md)
- [Attestation Reconciliation Drill](../runbooks/attestation-reconciliation-drill.md)
- [Worker Quarantine And Re-Enrollment](../policies/worker-quarantine-reenrollment.md)

## MVP Placeholder Status

This policy does not automate attestation or re-enrollment. Until attestation
method, trust bootstrap, key lifecycle, and re-enrollment gates are resolved,
attestation failures stay fail-closed and automated release remains blocked.

Revocation/reconciliation drift also stays fail closed. Selected privileged
model-route posture, active worker posture, and committed transaction posture
cannot remain valid when `attestation.reconciliation` reports `drift_detected`,
`revocation_pending`, `quarantine_required`, or `failed_closed`.
