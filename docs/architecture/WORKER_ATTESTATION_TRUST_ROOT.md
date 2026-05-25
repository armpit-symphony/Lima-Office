# Worker Attestation Trust Root

Status: design-only / not implemented.

## Purpose

Define a fail-closed metadata posture for Arc worker attestation and trust-root
inputs before any real TPM, secure-boot, or attestation verifier exists.

## RATS-Style Role Mapping

- Arc worker: attester.
- Supervisor: relying party.
- SparkPit/operator policy: verifier/appraisal policy placeholder.
- Endorsements/reference values: metadata placeholders only.

## Trust-Root Model

- `hardware_root_placeholder`
- `secure_boot_placeholder`
- `tpm_quote_placeholder`
- OS image hash
- Arc runtime hash
- policy bundle hash
- model bundle hash
- config hash

No raw TPM quote, private key, or secret material is stored in contracts/examples.

## Attestation Lifecycle

- `unenrolled`
- `enrolled_unverified`
- `attestation_required`
- `attested`
- `attestation_failed`
- `quarantined`
- `revoked`

Mapped in this lane to `worker.attestation`, `worker.lifecycle`,
`worker.heartbeat`, and `governance.device_trust` metadata.

## Fail-Closed Behavior

- Missing/expired/failed/ambiguous attestation blocks privileged metadata
  posture.
- Failed trust-root status blocks privileged route selection and triggers
  quarantine/review posture.
- Unknown trust-root values are degraded/blocked, never trusted.

## Contract Relationships

- `worker.attestation`: canonical attestation metadata record.
- `worker.deployment`: deployment-time trust-root placeholders and refs.
- `worker.heartbeat`: ongoing trust drift signals and escalation refs.
- `model.route`: trust-aware routing refs (`worker_attestation_ref`,
  `update_rollback_ref`) and blocked reason codes.

## Evidence Requirements

- All failed/expired/blocked attestation outcomes require `evidence_refs`.
- Attested outcomes require appraisal-policy refs and evidence refs.
- Quarantine/revoke/re-enrollment references must be linkable from evidence.

## Non-Goals

- No TPM runtime integration.
- No secure-boot verifier.
- No attestation service.
- No automated enrollment/release engine.

## Future Implementation Gates

1. Final attestation method and trust root.
2. Verifier/appraisal implementation and evidence integrity checks.
3. Durable storage for attestation history and revocation lineage.
4. Runtime-enforced quarantine/re-enrollment automation.
