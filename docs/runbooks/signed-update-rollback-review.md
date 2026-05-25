# Signed Update Rollback Review

Status: design/runbook posture only. No update/rollback automation is implemented.

## Purpose

Guide metadata-only review for signed update verification and rollback posture.

## When To Use

- `governance.update_record` indicates verification failure, rollback required,
  or blocked status.
- `update.rollback` records indicate failed, rolled_back, or blocked_mvp states.

## Prerequisites

- Update/governance/worker records are available.
- Reviewer roles are assigned.
- Evidence refs are available.

## Operator Steps

1. Confirm artifact type, hash ref, signer/key/provenance refs, and channel
   metadata.
2. Verify failure/rollback reason codes and evidence refs.
3. Confirm rollback target references known-good metadata.
4. Verify linked worker attestation/device-trust posture for impacted workers.
5. Keep update posture blocked when signature/provenance metadata is missing or
   invalid.

## Evidence To Capture

- Update record and update rollback IDs.
- Verification/rollback reason codes.
- Hash/signer/signing-key/provenance refs.
- Post-rollback health evidence refs.

## Quarantine / Rollback Steps

- Mark update path fail-closed in metadata.
- Link rollback-required/rolled-back records and worker containment posture.
- Maintain blocked privileged route posture for untrusted model/runtime/policy
  bundles.

## Escalation

- Security reviewer: signature/provenance trust failures.
- Field IT reviewer: worker impact and rollback coordination.
- Governance reviewer: unresolved evidence or policy mismatch.

## Done Criteria

- Rollback/blocked state is represented consistently across update and worker
  contracts.
- Required evidence refs are attached.
- No record implies successful live update execution in MVP.
