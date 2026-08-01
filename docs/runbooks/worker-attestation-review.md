# Worker Attestation Review

Status: design/runbook posture only. No automation is implemented.

## Purpose

Guide operator/security review for worker attestation metadata failures,
expirations, and trust-root drift.

## When To Use

- `worker.attestation` is `failed`, `expired`, `revoked`, or `blocked_mvp`.
- `worker.heartbeat` indicates attestation drift.
- `governance.device_trust` reports `attestation_failed`.

## Prerequisites

- Relevant contract records and evidence refs are present.
- Guardian and policy references are available.
- Reviewer roles are assigned.

## Operator Steps

1. Confirm tenant/worker/deployment correlation across attestation, lifecycle,
   heartbeat, and device-trust records.
2. Verify reason codes and evidence refs are present and non-ambiguous.
3. Classify state: degraded, quarantine required, revoke required, or
   re-enrollment pending.
4. Record containment decision and runbook linkage in evidence metadata.
5. If trust-root failure is present, keep privileged metadata routing blocked.

## Evidence To Capture

- Attestation record ID and status.
- Trust-root status and hash-manifest refs.
- Related lifecycle/heartbeat records.
- Quarantine/revoke/re-enrollment decision refs.

## Quarantine / Rollback Steps

- Move worker posture to quarantined/revoked metadata as policy requires.
- Revoke privileged metadata routing eligibility.
- Link update rollback refs if trust drift is tied to update failure.

## Escalation

- Escalate to security reviewer for trust-root failures.
- Escalate to field IT reviewer for repeated heartbeat drift.
- Escalate to governance reviewer when evidence is missing or ambiguous.

## Done Criteria

- Fail-closed state is represented consistently across linked contracts.
- Evidence refs are complete.
- Privileged route posture remains blocked until explicit review closure.
