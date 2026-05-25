# Signed Update Rollback Trust

Status: design-only / not implemented.

## Purpose

Define metadata-only trust boundaries for signed update and rollback posture for
worker/runtime/policy/model/config artifacts.

## Conceptual Standards Posture

- NIST SSDF: secure update lifecycle expectations.
- SLSA: provenance and artifact-integrity metadata expectations.
- TUF-inspired trust boundaries: signing roles, rollback metadata, key
  compromise resilience placeholders.

This document is conceptual mapping only and does not claim implementation or
certification.

Attestation appraisal/reference-value linkage details are defined in
[ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md](ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md).

## Update Artifact Types

- `policy_bundle`
- `arc_runtime_bundle`
- `model_bundle`
- `config_bundle`
- `supervisor_policy_snapshot`

## Trust Metadata

- artifact hash
- signer ref
- signing key ref
- provenance ref
- transparency log ref placeholder
- update channel
- rollback target ref

No private key material, signatures, tokens, or live download URLs are stored.

## Update Lifecycle

- `planned`
- `staged`
- `verified`
- `applied`
- `failed`
- `rolled_back`
- `blocked_mvp`

## Rollback Lifecycle

- detect verification/runtime failure
- classify rollback required
- record rollback target and reasons
- capture rollback evidence
- remain fail-closed on ambiguity

## Key Revocation Placeholder

Key rotation/revocation is represented by refs and reason codes only in this
lane; no signing infrastructure is implemented.

## Staged Rollout Expectations

- canary-first metadata posture
- pause on verification/evidence mismatch
- no automatic update execution in MVP

## Evidence Requirements

- verified/applied records require hash/signer/key/provenance/evidence refs.
- rollback records require target/reason/timestamp/evidence refs.
- failed/blocked outcomes require fail-closed reasons and evidence refs.

## Non-Goals

- No signing service.
- No package distribution service.
- No update agent/runtime.
- No rollback automation.

## Future Implementation Gates

1. Signing root and key lifecycle selection.
2. Durable provenance/transparency design.
3. Update distribution and staged rollout runtime design.
4. Automated rollback orchestration with evidence integrity guarantees.
