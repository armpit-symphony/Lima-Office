# Evidence Writer Failure Runbook

## Purpose

Guide operator response when required evidence cannot be written or verified.

## Policy Traceability

- Policy ref: `policy.evidence_writer_failure.phase0`
- Version: `policy-phase0-v1`
- Triggering contracts: `worker.heartbeat`, `task.execution`, `tool.invocation`, `approval.token`, `incident.ops`, `evidence.artifact`.
- Required fields: tenant/customer context, worker/task/action refs, evidence writer status, failure code, last successful evidence artifact ID if known, correlation ID.
- Fail-closed outcome: block privileged action, prevent approval token issue/use, create operator-visible incident or emergency spool record.

## When To Use

Use this runbook when:

- Worker heartbeat reports `evidence_writer_status` degraded or failed.
- Task status is `blocked_evidence_unavailable`.
- Tool invocation status is `evidence_failed`.
- Guardian denies an action due to missing evidence.
- Evidence integrity hash or ref verification fails.

## Prerequisites

- Identify tenant ID, customer context, worker ID, task ID, correlation ID, and affected action.
- Check whether action is read-only/draft-only or privileged.
- Confirm last successful evidence artifact ID if available.
- Check whether any approval tokens are active for affected tasks or worker.

## Must Not

- Do not allow privileged actions to proceed without required evidence.
- Do not issue or consume approval tokens while evidence is unavailable.
- Do not retry by writing raw sensitive payloads into logs or notes.
- Do not silently continue with external sends, file mutation, connector writes, software updates, or remediation.

## Procedure

1. Mark affected task or action as evidence unavailable.
2. Stop privileged follow-on actions.
3. Confirm Guardian decision and evidence requirement.
4. Capture an operator-visible failure note with metadata only.
5. Revoke approval tokens bound to affected task, worker, or action.
6. Check evidence spool depth and last evidence error code.
7. Attempt bounded retry if policy permits and no privileged action has proceeded.
8. If retry succeeds, record recovery evidence and resume only read-only or draft work.
9. If retry fails or integrity check fails, create `incident.ops`.
10. Quarantine the worker if worker-side evidence handling is suspect.

## Approval Requirements

No approval can override required evidence failure for privileged action execution. Approval may authorize operator review or future recovery work only after evidence capability is restored.

## Evidence To Capture

- Evidence failure reason.
- Last successful evidence artifact ID.
- Affected task/tool/model/memory/connector/handoff IDs.
- Approval token revocations.
- Worker quarantine decision if applied.
- Retry attempts and outcome.
- Incident ID when created.

## Containment / Rollback

- Block privileged tasks.
- Revoke related approval tokens.
- Quarantine affected worker if evidence failure is repeated or suspicious.
- Keep local queue metadata refs only.
- Do not delete evidence failure records.

## Escalation

Escalate to:

- Security reviewer for integrity mismatch, missing evidence after privileged action, or suspected tampering.
- Field IT reviewer for worker disk/network/health failure.
- Supervisor admin if multiple workers or supervisor ledger are affected.

## Done Criteria

- Affected privileged actions are blocked.
- Evidence failure is visible to operator.
- Related tokens are revoked.
- Incident exists when required.
- Worker quarantine decision is recorded when applicable.
- Recovery evidence or unresolved-block evidence is linked.
