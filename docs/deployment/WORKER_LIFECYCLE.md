# Worker Lifecycle

## Purpose

Define the planned deployment lifecycle for Arc worker mini PCs. This lifecycle
maps to contracts and runbooks only; it does not implement runtime state
machines or worker services.

Attestation/update trust linkage in this lane is metadata-only via
`worker.attestation` and `update.rollback` records.

## Lifecycle States

| State | Meaning | Assignment posture |
| --- | --- | --- |
| `provisioned` | Hardware and OS are inventoried, but not enrolled. | No tasks |
| `enrolled` | Supervisor has worker identity, role, and policy refs. | No privileged tasks until heartbeat and Guardian posture pass |
| `active` | Worker heartbeat, policy refs, and evidence posture are acceptable. | Mock/read-only/draft tasks only |
| `degraded` | Health, heartbeat, evidence, update, or network warning exists. | New assignments limited or paused by policy |
| `quarantined` | Containment state after identity, capability, evidence, tool, update, or operator trigger. | No new assignments; privileged actions blocked |
| `revoked` | Worker trust and capability lease are removed. | No tasks |
| `re-enrollment pending` | Operator/security/field IT review required before return. | No tasks |
| `retired` | Worker is removed from service and local cache must be purged. | No tasks |

## Transition Rules

- `provisioned` to `enrolled`: requires operator enrollment evidence and worker
  deployment record.
- `enrolled` to `active`: requires heartbeat, policy bundle ref, capability
  manifest ref, encryption status, Guardian decision, and evidence refs.
- `active` to `degraded`: triggered by missed heartbeat, evidence writer
  degradation, resource pressure, network degradation, or update warning.
- `degraded` to `quarantined`: triggered by identity failure, capability
  mismatch, evidence writer failure, suspicious tool request, update
  verification failure, or operator containment.
- `quarantined` to `re-enrollment pending`: requires operator review and
  documented reason.
- `re-enrollment pending` to `enrolled`: requires identity recheck, capability
  review, policy review, cache purge evidence where required, and Guardian
  decision.
- Any non-terminal state to `revoked`: allowed for containment with evidence.
- `revoked` to `retired`: requires cache purge and inventory update evidence.

## Guardian/Policy Requirements

- Enrollment, re-enrollment, release from quarantine, update, rollback, and
  retirement require Guardian decision refs and evidence refs.
- Guardian remains the syscall gate for model calls, tools, files, network,
  connector posture, outbound messages, scheduled work, secrets, and privileged
  operations.
- Missing or ambiguous policy means fail closed.

## Evidence Requirements

Capture evidence refs for:

- Hardware inventory.
- OS readiness.
- Network readiness.
- Worker identity refs.
- Capability manifest refs.
- Policy/model bundle refs.
- First heartbeat.
- Quarantine and release request.
- Cache purge.
- Update and rollback staging.
- Revocation and retirement.

Evidence records must be metadata/ref-based and must not include secrets, raw
customer data, raw prompts, connector payloads, or approval token material.

## Operator Approvals

Operator approval is required for enrollment and re-enrollment. Security or
field IT review is required for identity mismatch, attestation failure, update
verification failure, or evidence writer failure. Software install/update and
remediation remain approval-required or blocked.

## Fail-Closed Behavior

Fail closed when:

- Worker identity is missing, failed, or ambiguous.
- Supervisor endpoint ref is missing.
- Policy bundle ref or capability manifest hash does not match expected state.
- Evidence writer fails before a privileged action.
- Guardian decision is missing, expired, or wrong scope.
- Worker is quarantined, revoked, retired, or wrong tenant.
