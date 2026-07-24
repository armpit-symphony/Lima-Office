# Evidence Writer Failure Policy

## Purpose

Define fail-closed behavior when required evidence cannot be written. This policy is scaffolding only and does not implement an evidence ledger, queue, retry worker, or storage backend.

## Policy Metadata

- Policy ref: `policy.evidence_writer_failure.phase0`
- Version: `policy-phase0-v1`
- Status: Draft scaffold.
- Owner role: Supervisor admin.
- Applies to contracts: `evidence.artifact`, `task.execution`, `tool.invocation`, `worker.heartbeat`, `worker.lifecycle`, `approval.token`, `incident.ops`, `lima_it.handoff`.
- Evidence artifact types: `incident`, `denial`, `worker_heartbeat`, `quarantine`.
- Fail-closed outcome: block privileged actions, prevent approval token issue/use, create operator-visible incident when possible.
- Runbook: [Evidence Writer Failure Runbook](../runbooks/evidence-writer-failure.md).

## Evidence Writer Role

The evidence writer records metadata-only evidence artifacts for Guardian decisions, approvals, task transitions, worker lifecycle events, tool/model/memory/connector actions, LIMA IT handoffs, incidents, denials, and quarantines.

Workers may report evidence events, but the Supervisor evidence ledger remains the trust boundary. Worker-submitted evidence is untrusted until accepted, integrity checked, and linked by the Supervisor.

## What Counts As Evidence

Evidence is a redaction-aware record or protected reference that shows:

- Who requested or performed an action.
- Tenant and customer context.
- Guardian policy result.
- Approval state where relevant.
- Action scope.
- Risk tier and data classification.
- Outcome, denial, failure, or quarantine state.
- Integrity hash or reference.
- Retention and redaction posture.

Evidence must not contain plaintext secrets, raw customer payloads, raw prompts, raw tool output, OAuth tokens, API keys, cookies, passwords, or private keys.

## Must Not

- Do not allow privileged actions to proceed when required evidence cannot be written.
- Do not issue, consume, or reuse approval tokens while evidence is unavailable.
- Do not treat local emergency spool records as a substitute for normal evidence reconciliation.
- Do not write raw secrets, raw prompts, raw tool output, or sensitive payloads into fallback notes.
- Do not silently continue after evidence integrity failure.

## Pre-Action Evidence

Pre-action evidence is required before:

- Privileged tool invocation.
- External message send path.
- File delete or overwrite.
- Customer record mutation.
- Software install/update.
- Remediation request.
- Sensitive data access.
- LIMA IT remediation handoff.
- Worker quarantine release.

If pre-action evidence cannot be written, the action must not proceed.

## Post-Action Evidence

Post-action evidence records action result, denial, failure, timeout, or cancellation.

If post-action evidence fails after a permitted read-only or draft-only action:

- Mark the task degraded or evidence-failed.
- Block further side-effecting work.
- Queue a retry.
- Notify operator.
- Consider worker quarantine if the worker cannot confirm evidence handoff.

Privileged actions should be designed so pre-action evidence is recorded before any external effect.

## Failure Before Action

When evidence is required and cannot be written before action:

- Guardian must deny or block the action.
- Task status moves to `blocked_evidence_unavailable` or equivalent.
- Approval token cannot be issued or consumed.
- Tool invocation, model route, memory access, connector action, or LIMA IT remediation must not proceed.
- Operator dashboard must show evidence unavailable.

## Authoritative Failure Record

If the primary evidence writer cannot write to the normal ledger, the future runtime must use an operator-visible emergency failure record before any recovery action.

Phase 0 placeholder requirements for that future emergency spool:

- Local append-only metadata refs only.
- Tenant ID, customer context, correlation ID, task/action ID, worker ID if applicable.
- Failure code.
- Last successful evidence artifact ID if known.
- No raw secrets or raw sensitive payloads.
- Bounded spool depth.
- Disk-full behavior that fails closed.
- Reconciliation steps before any blocked task resumes.

Spool depth, retry interval, and disk thresholds remain policy decisions needed before runtime.

## Failure After Action

If evidence fails after a non-privileged read-only/draft action:

- Stop follow-on work for that task.
- Preserve local metadata refs for retry.
- Do not execute privileged next steps.
- Create an incident when evidence cannot be recovered.

If evidence fails after a privileged action despite pre-action evidence:

- Treat as high severity incident.
- Block additional privileged actions.
- Revoke related approval tokens.
- Quarantine the worker if worker-side evidence handling is suspect.
- Require operator and security review.

## Degraded Mode

Degraded mode allows only:

- Operator-visible status review.
- Read-only health checks.
- Evidence retry attempts.
- Incident triage.
- Worker quarantine or revoke.

Degraded mode blocks:

- External sends.
- File mutation.
- Connector writes.
- Customer record mutation.
- Software install/update.
- Remediation.
- Durable memory writes from unverified content.

## Retry Behavior

Retry behavior is a future implementation detail, but Phase 0 policy requires:

- Bounded retry count.
- Backoff between retries.
- Queue depth visibility.
- Correlation ID preservation.
- Idempotency key preservation.
- No duplicate approval token consumption.
- Operator-visible failure after retry exhaustion.

## Failure Codes

Required policy outcomes:

| Failure code | Outcome |
| --- | --- |
| `ledger_unavailable` | Block privileged actions, queue metadata-only retry, alert operator. |
| `integrity_check_failed` | Block all affected actions, create incident, quarantine affected worker if worker-local. |
| `permission_denied` | Block affected action, create incident, require supervisor admin/security review. |
| `storage_full` | Block privileged actions, alert operator, field IT review before retry. |
| `unknown` | Block affected action and escalate. |

## Queue And Backoff Expectations

The future queue must be tenant-scoped and evidence-scoped. Queue entries must contain refs, hashes, and metadata only. Queue contents must not include plaintext secrets or raw sensitive payloads.

Backoff defaults are policy decisions needed before runtime.

## When Task Must Be Blocked

Block the task when:

- Evidence is required before action and write fails.
- Evidence writer status is failed.
- Evidence integrity hash cannot be produced or verified.
- Evidence destination is unavailable past retry threshold.
- Evidence policy is missing or ambiguous.
- Action is privileged and evidence linkage is missing.

## When Worker Must Be Quarantined

Quarantine worker when:

- Worker repeatedly fails to submit evidence events.
- Worker reports success but evidence refs are missing.
- Evidence chain integrity fails.
- Worker attempts privileged action while evidence is unavailable.
- Worker capability hash changes during evidence failure.
- Operator or Guardian suspects tampering.

Initial quarantine threshold placeholder: repeated evidence writer failure or integrity mismatch on the same worker requires quarantine. Exact count and time window are policy decisions needed before runtime.

## Evidence Hash / Reference Behavior

Evidence records must use:

- `artifact_id`.
- `storage_ref`.
- `payload_hash`.
- `integrity_ref`.
- `previous_artifact_id` where chaining applies.
- `redaction_status`.
- `retention_policy_ref`.
- `raw_content_included: false`.
- `secret_material_included: false`.

Replay denial and fail-closed records should also carry:

- `replay_record_id`.
- `replay_artifact_id`.
- `denial_evidence_ref` where denial is authoritative.
- `pre_action_evidence_refs` and `post_action_evidence_refs` where applicable.

Raw payload storage location, hash method, and integrity chain implementation remain future decisions.

## Replay Denial And Fail-Closed Evidence

When replay checks deny, expire, stale, revoke, or fail closed:

- Create denial-path evidence metadata.
- Link `guardian.decision`, `guardian.replay`, and `replay.store.record` IDs.
- Include mismatch/failure reason codes.
- Include tenant/task/action/tool scope refs.
- Include evidence refs required by schema conditionals.

If replay-store state is unavailable or ambiguous, represent
`atomicity_status: failed_closed` and block action.

## Export Manifest Linkage

Evidence records marked exportable must support refs-only export posture through
`evidence.export_manifest` metadata:

- include redaction profile refs;
- include retention policy refs;
- include delete conflict refs for denied/blocked export outcomes.

No export manifest may contain raw customer payloads or secret material.

## MVP Acceptance Gates

- Required evidence unavailable means privileged action does not proceed.
- Evidence failure creates visible task state.
- Evidence failure can trigger worker quarantine.
- Evidence retry is bounded and operator-visible.
- Evidence records use refs and hashes, not raw secret or customer payloads.
- Replay denial and failed-closed paths are evidenced as first-class outcomes.
- Export posture remains refs-only with conflict placeholders.
- Runbook exists for operator handling.
