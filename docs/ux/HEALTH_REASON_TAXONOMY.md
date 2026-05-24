# Health Reason Taxonomy

This is initial taxonomy scaffolding for console status and alert labels. It is
not production monitoring, an alerting service, or production runtime
implementation. Phase 1A v2 uses these codes in metadata-only
`supervisor.health` mock reports.

| Reason code | Category | Meaning | Expected UX state | Primary records | Runbook |
| --- | --- | --- | --- | --- | --- |
| `worker_stale` | Worker | Heartbeat age or missed heartbeat count exceeded planning threshold | High alert, task assignment blocked or review-required | `worker.heartbeat`, `worker.lifecycle`, `console.alert` | [Health checks](../runbooks/health-checks.md) |
| `worker_quarantined` | Worker | Worker is quarantined by Guardian/operator/security review | Blocked for new assignments | `worker.lifecycle`, `incident.ops`, `console.action` | [Worker quarantine](../runbooks/worker-quarantine.md) |
| `worker_revoked` | Worker | Worker identity or lease is revoked | Blocked and terminal until replacement | `worker.lifecycle`, `worker.deployment` | [Worker re-enrollment](../runbooks/worker-reenrollment.md) |
| `evidence_missing` | Evidence | Required evidence ref is absent | Blocked for privileged action | `evidence.failure`, `task.execution`, `console.alert` | [Evidence writer failure](../runbooks/evidence-writer-failure.md) |
| `evidence_writer_degraded` | Evidence | Evidence writer degraded or failed | High alert; pre-action privileged work blocked when evidence is required | `evidence.failure`, `worker.heartbeat` | [Evidence writer failure](../runbooks/evidence-writer-failure.md) |
| `guardian_denied` | Guardian | Guardian decision is deny, block-MVP, or quarantine | Blocked | `guardian.decision` | [Approval flow](../runbooks/approval-flow.md) |
| `guardian_decision_expired` | Guardian | Guardian decision expired before use | Blocked; new decision required | `guardian.decision`, `guardian.replay` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `guardian_decision_stale` | Guardian | Guardian decision exceeded max age or clock-skew window | Blocked; triage queue and worker clock posture | `guardian.decision`, `guardian.replay`, `worker.heartbeat` | [Health checks](../runbooks/health-checks.md) |
| `guardian_replay_denied` | Guardian | One-time Guardian decision nonce was reused or replay status is non-authorizing | Blocked; review for incident threshold | `guardian.replay`, `incident.ops` | [Security incident](../runbooks/security-incident.md) |
| `approval_expired` | Approval | Approval request or token expired | Blocked; new request required | `approval.request`, `approval.token`, `token.verification` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `approval_revoked` | Approval | Approval token or decision authority revoked | Blocked | `approval.token`, `token.verification` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `token_mismatch` | Approval | Token verification fails scope, task, tenant, resource, or action binding | Blocked | `token.verification`, `approval.token` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `tainted_input` | Guardian | Prompt-injection or untrusted input detected | Warning/high; privileged actions blocked or require review | `taint.ref`, `guardian.decision` | [Prompt injection response](../runbooks/prompt-injection-response.md) |
| `connector_revoked` | Connector | Connector consent/trust state revoked | Blocked for connector use | `connector.trust`, `governance.connector_consent` | [Connector revocation](../runbooks/connector-revocation.md) |
| `attestation_failed` | Worker/deployment | Worker attestation, identity, policy hash, or model hash failed | High alert; quarantine/re-enrollment review | `worker.deployment`, `worker.lifecycle`, `governance.update_record` | [Worker attestation failure](../runbooks/worker-attestation-failure.md) |
| `update_rollback_required` | Deployment/update | Update review requires rollback or pause | High alert; no automatic update | `governance.update_record`, `worker.heartbeat` | [Update rollback approval](../runbooks/update-rollback-approval.md) |
| `lima_it_remediation_blocked` | LIMA IT | Remediation request is blocked or non-executing metadata only | Blocked-MVP label | `lima_it.handoff`, `approval.result` | [LIMA IT handoff](../runbooks/lima-it-handoff.md) |
| `retention_policy_missing` | Governance/data | Retention posture missing for record or action | Blocked for durable write/export/delete | `governance.audit_export`, `evidence.artifact`, `memory.access` | [Customer exit delete](../runbooks/customer-exit-delete.md) |
| `export_delete_policy_missing` | Governance/data | Export/delete posture missing or preservation conflict unresolved | Blocked for export/delete | `governance.audit_export` | [Customer exit delete](../runbooks/customer-exit-delete.md) |
| `idp_mfa_missing` | Governance/identity | Identity provider or MFA posture missing for privileged role | Blocked for approval-capable view | `governance.identity`, `governance.access_review` | [Access review](../runbooks/access-review.md) |
| `task_blocked` | Task | Task is blocked, denied, or evidence-unavailable after policy/invariant review | Blocked | `task.execution`, `supervisor.health` | [Approval flow](../runbooks/approval-flow.md) |

## UX Rules

- Missing data is not healthy.
- Blocked-MVP states cannot be converted to approval-capable states by the
  console.
- Every reason code must map to a runbook and evidence or evidence-failure ref.
- Future runtime must treat unknown reason codes as review-required or blocked.
- Governance/export/delete reason-code alignment is defined in
  [Reconciliation Reason Taxonomy](../taxonomy/RECONCILIATION_REASON_TAXONOMY.md)
  and [Evidence Reason Taxonomy](../taxonomy/EVIDENCE_REASON_TAXONOMY.md).
