# Attestation Revocation Propagation

Status: runbook posture design. Not implemented automation.

## Purpose

Guide metadata-only operator handling when attestation trust inputs/results are
revoked, stale, conflicted, or expired and must propagate across worker/device/
model-route posture.

## When To Use

- Reference value revoked.
- Endorsement revoked.
- Appraisal policy revoked.
- Attestation result expired.
- Worker attestation failed.
- Update rollback required by trust posture.

## Operator Steps

1. Confirm tenant scope and affected `worker_id`/`deployment_id`.
2. Confirm the latest `attestation.result` and `attestation.result.lineage`.
3. Confirm authority posture from `attestation.authority`.
4. Update or validate quarantine posture in `worker.lifecycle`.
5. Validate device-trust posture in `governance.device_trust`.
6. Validate model-route blocked/degraded posture in `model.route`.
7. Validate rollback linkage in `update.rollback`.
8. Record propagation state (`pending`, `propagated`, `failed_closed`) with
   reason/evidence refs.

## Affected Records Checklist

- `attestation.result.lineage`
- `attestation.authority`
- `worker.lifecycle`
- `worker.heartbeat`
- `governance.device_trust`
- `model.route`
- `update.rollback`
- `transaction.boundary`
- `evidence.ledger.entry`

## Evidence To Capture

- Revocation trigger evidence
- Quarantine decision evidence
- Device-trust and model-route propagation evidence
- Rollback linkage evidence
- Failed-closed rationale evidence

## Quarantine / Rollback Actions

- Quarantine is metadata-only posture in this phase.
- Rollback is metadata-only posture in this phase.
- No live remediation/update/deployment actions are executed.

## Escalation

- Security reviewer when authority is missing/revoked.
- Field IT reviewer when worker trust posture degrades.
- Governance reviewer for SoD or policy conflicts.

## Done Criteria

- All affected metadata records align on fail-closed trust posture.
- Revocation propagation status is no longer ambiguous.
- Evidence refs are complete and tenant-consistent.
- No blocked-MVP state is represented as trusted or completed.
