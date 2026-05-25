# LIMA Office Contract Schemas

This directory contains Phase 0 contract schemas and sanitized example objects for LIMA Office OS. These files are planning artifacts only. They do not implement runtime services, live connectors, model calls, tool execution, external messaging, or remediation.

## Versioning

- Contract versions use semantic versioning in `contract_version`.
- Schema files live under versioned folders such as [v1](v1).
- The Phase 0 baseline is `1.0.0`.
- Additive optional fields may be added in a minor version when existing consumers can ignore them.
- Required fields, enum removals, state semantic changes, or renamed fields require a major version.
- Phase 1A pre-production mock hardening may tighten v1 schemas when the
  matching examples, tests, and docs are updated. This does not authorize live
  runtime consumers.

## Compatibility Rules

- Producers must emit only fields allowed by the schema. Schemas default to `additionalProperties: false`.
- A new runtime behavior is blocked until the matching contract schema and example exist.
- Runtime must fail closed when a contract is missing, policy is missing, state is ambiguous, evidence cannot be written, a token verification fails, or taint is unresolved for a privileged path.
- Guardian, approval, evidence, tenant isolation, and failure behavior are compatibility-sensitive. They cannot be weakened in a minor version.
- Consumers must fail closed on unknown contract versions, missing Guardian decisions, missing approval tokens, missing evidence, tenant mismatches, expired approvals, or evidence writer failure.
- Approval token records are metadata only. They must never contain bearer token material, OAuth codes, API keys, signatures, passwords, PINs, cookies, or plaintext secrets.
- Reason-bearing contracts/examples must include `taxonomy_version`.

## Schema Location

Version 1 schemas are in [v1](v1):

- [worker.lifecycle.schema.json](v1/worker.lifecycle.schema.json)
- [worker.heartbeat.schema.json](v1/worker.heartbeat.schema.json)
- [worker.deployment.schema.json](v1/worker.deployment.schema.json)
- [worker.attestation.schema.json](v1/worker.attestation.schema.json)
- [attestation.reference_value.schema.json](v1/attestation.reference_value.schema.json)
- [attestation.endorsement.schema.json](v1/attestation.endorsement.schema.json)
- [attestation.appraisal_policy.schema.json](v1/attestation.appraisal_policy.schema.json)
- [attestation.result.schema.json](v1/attestation.result.schema.json)
- [attestation.result.lineage.schema.json](v1/attestation.result.lineage.schema.json)
- [attestation.authority.schema.json](v1/attestation.authority.schema.json)
- [attestation.reconciliation.schema.json](v1/attestation.reconciliation.schema.json)
- [update.rollback.schema.json](v1/update.rollback.schema.json)
- [supervisor.health.schema.json](v1/supervisor.health.schema.json)
- [governance.identity.schema.json](v1/governance.identity.schema.json)
- [governance.access_review.schema.json](v1/governance.access_review.schema.json)
- [governance.breakglass.schema.json](v1/governance.breakglass.schema.json)
- [governance.rbac_matrix.schema.json](v1/governance.rbac_matrix.schema.json)
- [governance.session_policy.schema.json](v1/governance.session_policy.schema.json)
- [governance.device_trust.schema.json](v1/governance.device_trust.schema.json)
- [governance.audit_export.schema.json](v1/governance.audit_export.schema.json)
- [governance.export_delete_review.schema.json](v1/governance.export_delete_review.schema.json)
- [reason.code.registry.schema.json](v1/reason.code.registry.schema.json)
- [reason.code.compatibility.schema.json](v1/reason.code.compatibility.schema.json)
- [governance.connector_consent.schema.json](v1/governance.connector_consent.schema.json)
- [governance.update_record.schema.json](v1/governance.update_record.schema.json)
- [console.view.schema.json](v1/console.view.schema.json)
- [console.alert.schema.json](v1/console.alert.schema.json)
- [console.action.schema.json](v1/console.action.schema.json)
- [task.execution.schema.json](v1/task.execution.schema.json)
- [guardian.decision.schema.json](v1/guardian.decision.schema.json)
- [guardian.replay.schema.json](v1/guardian.replay.schema.json)
- [replay.store.record.schema.json](v1/replay.store.record.schema.json)
- [transaction.boundary.schema.json](v1/transaction.boundary.schema.json)
- [transaction.coordinator.event.schema.json](v1/transaction.coordinator.event.schema.json)
- [approval.request.schema.json](v1/approval.request.schema.json)
- [approval.result.schema.json](v1/approval.result.schema.json)
- [approval.token.schema.json](v1/approval.token.schema.json)
- [token.verification.schema.json](v1/token.verification.schema.json)
- [approval.binding.schema.json](v1/approval.binding.schema.json)
- [approval.chain.schema.json](v1/approval.chain.schema.json)
- [model.route.schema.json](v1/model.route.schema.json)
- [tool.invocation.schema.json](v1/tool.invocation.schema.json)
- [memory.access.schema.json](v1/memory.access.schema.json)
- [helper.scope.schema.json](v1/helper.scope.schema.json)
- [taint.ref.schema.json](v1/taint.ref.schema.json)
- [connector.trust.schema.json](v1/connector.trust.schema.json)
- [connector.readiness.schema.json](v1/connector.readiness.schema.json)
- [connector.scope_review.schema.json](v1/connector.scope_review.schema.json)
- [connector.provider_profile.schema.json](v1/connector.provider_profile.schema.json)
- [connector.revocation_drill.schema.json](v1/connector.revocation_drill.schema.json)
- [connector.reconciliation.schema.json](v1/connector.reconciliation.schema.json)
- [connector.acceptance_score.schema.json](v1/connector.acceptance_score.schema.json)
- [connector.reconciliation_slo.schema.json](v1/connector.reconciliation_slo.schema.json)
- [connector.ownership.schema.json](v1/connector.ownership.schema.json)
- [connector.escalation.schema.json](v1/connector.escalation.schema.json)
- [evidence.artifact.schema.json](v1/evidence.artifact.schema.json)
- [evidence.ledger.entry.schema.json](v1/evidence.ledger.entry.schema.json)
- [evidence.failure.schema.json](v1/evidence.failure.schema.json)
- [evidence.export_manifest.schema.json](v1/evidence.export_manifest.schema.json)
- [incident.ops.schema.json](v1/incident.ops.schema.json)
- [sla.slo.schema.json](v1/sla.slo.schema.json)
- [lima_it.handoff.schema.json](v1/lima_it.handoff.schema.json)

## Example Location

Sanitized example objects are in [examples](examples):

- [worker.lifecycle.example.json](examples/worker.lifecycle.example.json)
- [worker.heartbeat.example.json](examples/worker.heartbeat.example.json)
- [worker.deployment.lightweight.example.json](examples/worker.deployment.lightweight.example.json)
- [worker.deployment.local-model.example.json](examples/worker.deployment.local-model.example.json)
- [worker.deployment.quarantined.example.json](examples/worker.deployment.quarantined.example.json)
- [worker.attestation.attested-metadata-only.example.json](examples/worker.attestation.attested-metadata-only.example.json)
- [worker.attestation.failed-quarantine-required.example.json](examples/worker.attestation.failed-quarantine-required.example.json)
- [worker.attestation.expired.example.json](examples/worker.attestation.expired.example.json)
- [attestation.reference_value.active-runtime.example.json](examples/attestation.reference_value.active-runtime.example.json)
- [attestation.reference_value.revoked-model-bundle.example.json](examples/attestation.reference_value.revoked-model-bundle.example.json)
- [attestation.endorsement.trusted-placeholder.example.json](examples/attestation.endorsement.trusted-placeholder.example.json)
- [attestation.endorsement.revoked.example.json](examples/attestation.endorsement.revoked.example.json)
- [attestation.appraisal_policy.active-worker.example.json](examples/attestation.appraisal_policy.active-worker.example.json)
- [attestation.appraisal_policy.blocked-mvp.example.json](examples/attestation.appraisal_policy.blocked-mvp.example.json)
- [attestation.result.pass-metadata-only.example.json](examples/attestation.result.pass-metadata-only.example.json)
- [attestation.result.fail-quarantine-required.example.json](examples/attestation.result.fail-quarantine-required.example.json)
- [attestation.result.inconclusive-degraded.example.json](examples/attestation.result.inconclusive-degraded.example.json)
- [attestation.result.lineage.current.example.json](examples/attestation.result.lineage.current.example.json)
- [attestation.result.lineage.revoked-propagation-pending.example.json](examples/attestation.result.lineage.revoked-propagation-pending.example.json)
- [attestation.result.lineage.quarantine-required.example.json](examples/attestation.result.lineage.quarantine-required.example.json)
- [attestation.authority.verifier-owner-active.example.json](examples/attestation.authority.verifier-owner-active.example.json)
- [attestation.authority.reference-value-approver-active.example.json](examples/attestation.authority.reference-value-approver-active.example.json)
- [attestation.authority.revoked.example.json](examples/attestation.authority.revoked.example.json)
- [attestation.reconciliation.reconciled.example.json](examples/attestation.reconciliation.reconciled.example.json)
- [attestation.reconciliation.reference-revoked-drift.example.json](examples/attestation.reconciliation.reference-revoked-drift.example.json)
- [attestation.reconciliation.quarantine-required.example.json](examples/attestation.reconciliation.quarantine-required.example.json)
- [attestation.reconciliation.failed-closed-cross-tenant.example.json](examples/attestation.reconciliation.failed-closed-cross-tenant.example.json)
- [update.rollback.policy-bundle-verified.example.json](examples/update.rollback.policy-bundle-verified.example.json)
- [update.rollback.model-bundle-blocked-mvp.example.json](examples/update.rollback.model-bundle-blocked-mvp.example.json)
- [update.rollback.runtime-rollback-required.example.json](examples/update.rollback.runtime-rollback-required.example.json)
- [update.rollback.failed-signature.example.json](examples/update.rollback.failed-signature.example.json)
- [supervisor.health.healthy.example.json](examples/supervisor.health.healthy.example.json)
- [supervisor.health.degraded.example.json](examples/supervisor.health.degraded.example.json)
- [supervisor.health.blocked.example.json](examples/supervisor.health.blocked.example.json)
- [supervisor.health.model-route-degraded.example.json](examples/supervisor.health.model-route-degraded.example.json)
- [supervisor.health.attestation-degraded.example.json](examples/supervisor.health.attestation-degraded.example.json)
- [supervisor.health.attestation-appraisal-degraded.example.json](examples/supervisor.health.attestation-appraisal-degraded.example.json)
- [supervisor.health.attestation-lineage-blocked.example.json](examples/supervisor.health.attestation-lineage-blocked.example.json)
- [supervisor.health.attestation-reconciliation-blocked.example.json](examples/supervisor.health.attestation-reconciliation-blocked.example.json)
- [governance.identity.operator-mfa-required.example.json](examples/governance.identity.operator-mfa-required.example.json)
- [governance.access_review.quarterly-placeholder.example.json](examples/governance.access_review.quarterly-placeholder.example.json)
- [governance.breakglass.blocked-mvp.example.json](examples/governance.breakglass.blocked-mvp.example.json)
- [governance.rbac_matrix.approver-privileged.example.json](examples/governance.rbac_matrix.approver-privileged.example.json)
- [governance.rbac_matrix.auditor-readonly.example.json](examples/governance.rbac_matrix.auditor-readonly.example.json)
- [governance.rbac_matrix.field-it-remediation-blocked.example.json](examples/governance.rbac_matrix.field-it-remediation-blocked.example.json)
- [governance.session_policy.step-up-required.example.json](examples/governance.session_policy.step-up-required.example.json)
- [governance.session_policy.revoked-on-role-change.example.json](examples/governance.session_policy.revoked-on-role-change.example.json)
- [governance.device_trust.operator-managed.example.json](examples/governance.device_trust.operator-managed.example.json)
- [governance.device_trust.worker-attestation-required.example.json](examples/governance.device_trust.worker-attestation-required.example.json)
- [governance.device_trust.untrusted-blocked.example.json](examples/governance.device_trust.untrusted-blocked.example.json)
- [governance.audit_export.requested-placeholder.example.json](examples/governance.audit_export.requested-placeholder.example.json)
- [governance.audit_export.delete-conflict.example.json](examples/governance.audit_export.delete-conflict.example.json)
- [governance.audit_export.export-denied.example.json](examples/governance.audit_export.export-denied.example.json)
- [governance.export_delete_review.export-approved-redacted.example.json](examples/governance.export_delete_review.export-approved-redacted.example.json)
- [governance.export_delete_review.delete-conflict-denied.example.json](examples/governance.export_delete_review.delete-conflict-denied.example.json)
- [governance.export_delete_review.blocked-mvp.example.json](examples/governance.export_delete_review.blocked-mvp.example.json)
- [reason.code.registry.reconciliation-active.example.json](examples/reason.code.registry.reconciliation-active.example.json)
- [reason.code.registry.evidence-blocked.example.json](examples/reason.code.registry.evidence-blocked.example.json)
- [reason.code.registry.export-delete-deprecated.example.json](examples/reason.code.registry.export-delete-deprecated.example.json)
- [reason.code.registry.blocked-mvp.example.json](examples/reason.code.registry.blocked-mvp.example.json)
- [reason.code.compatibility.add-compatible.example.json](examples/reason.code.compatibility.add-compatible.example.json)
- [reason.code.compatibility.deprecate-alias.example.json](examples/reason.code.compatibility.deprecate-alias.example.json)
- [reason.code.compatibility.breaking-change-blocked.example.json](examples/reason.code.compatibility.breaking-change-blocked.example.json)
- [governance.connector_consent.revoked.example.json](examples/governance.connector_consent.revoked.example.json)
- [governance.update_record.rollback-required.example.json](examples/governance.update_record.rollback-required.example.json)
- [console.view.operator-dashboard.example.json](examples/console.view.operator-dashboard.example.json)
- [console.alert.worker-stale.example.json](examples/console.alert.worker-stale.example.json)
- [console.alert.evidence-missing.example.json](examples/console.alert.evidence-missing.example.json)
- [console.alert.model-route-blocked.example.json](examples/console.alert.model-route-blocked.example.json)
- [console.alert.attestation-failed.example.json](examples/console.alert.attestation-failed.example.json)
- [console.alert.attestation-appraisal-failed.example.json](examples/console.alert.attestation-appraisal-failed.example.json)
- [console.alert.attestation-revocation-propagation.example.json](examples/console.alert.attestation-revocation-propagation.example.json)
- [console.alert.attestation-reconciliation-drift.example.json](examples/console.alert.attestation-reconciliation-drift.example.json)
- [console.action.approval-denied.example.json](examples/console.action.approval-denied.example.json)
- [console.action.worker-quarantine-requested.example.json](examples/console.action.worker-quarantine-requested.example.json)
- [task.execution.example.json](examples/task.execution.example.json)
- [guardian.decision.example.json](examples/guardian.decision.example.json)
- [guardian.decision.allowed-one-time.example.json](examples/guardian.decision.allowed-one-time.example.json)
- [guardian.decision.expired-denied.example.json](examples/guardian.decision.expired-denied.example.json)
- [guardian.decision.replay-denied.example.json](examples/guardian.decision.replay-denied.example.json)
- [guardian.decision.blocked-mvp.example.json](examples/guardian.decision.blocked-mvp.example.json)
- [guardian.decision.clock-skew-denied.example.json](examples/guardian.decision.clock-skew-denied.example.json)
- [guardian.decision.lima-it-remediation-denied.example.json](examples/guardian.decision.lima-it-remediation-denied.example.json)
- [guardian.replay.valid-first-use.example.json](examples/guardian.replay.valid-first-use.example.json)
- [guardian.replay.replay-denied.example.json](examples/guardian.replay.replay-denied.example.json)
- [guardian.replay.expired.example.json](examples/guardian.replay.expired.example.json)
- [guardian.replay.scope-mismatch.example.json](examples/guardian.replay.scope-mismatch.example.json)
- [guardian.replay.blocked-mvp.example.json](examples/guardian.replay.blocked-mvp.example.json)
- [replay.store.record.consumed.example.json](examples/replay.store.record.consumed.example.json)
- [replay.store.record.replay-denied.example.json](examples/replay.store.record.replay-denied.example.json)
- [replay.store.record.failed-closed.example.json](examples/replay.store.record.failed-closed.example.json)
- [transaction.boundary.guardian-replay-consume.example.json](examples/transaction.boundary.guardian-replay-consume.example.json)
- [transaction.boundary.failed-closed.example.json](examples/transaction.boundary.failed-closed.example.json)
- [transaction.boundary.export-manifest-prepare.example.json](examples/transaction.boundary.export-manifest-prepare.example.json)
- [transaction.coordinator.event.started.example.json](examples/transaction.coordinator.event.started.example.json)
- [transaction.coordinator.event.nonce-reserved.example.json](examples/transaction.coordinator.event.nonce-reserved.example.json)
- [transaction.coordinator.event.committed.example.json](examples/transaction.coordinator.event.committed.example.json)
- [transaction.coordinator.event.failed-closed.example.json](examples/transaction.coordinator.event.failed-closed.example.json)
- [transaction.coordinator.event.duplicate-request.example.json](examples/transaction.coordinator.event.duplicate-request.example.json)
- [transaction.coordinator.event.reconciliation-completed.example.json](examples/transaction.coordinator.event.reconciliation-completed.example.json)
- [approval.request.example.json](examples/approval.request.example.json)
- [approval.result.approved.example.json](examples/approval.result.approved.example.json)
- [approval.result.denied-blocked-mvp.example.json](examples/approval.result.denied-blocked-mvp.example.json)
- [approval.token.example.json](examples/approval.token.example.json)
- [token.verification.valid.example.json](examples/token.verification.valid.example.json)
- [token.verification.expired.example.json](examples/token.verification.expired.example.json)
- [token.verification.revoked.example.json](examples/token.verification.revoked.example.json)
- [approval.binding.bound-valid.example.json](examples/approval.binding.bound-valid.example.json)
- [approval.binding.consumed-one-time.example.json](examples/approval.binding.consumed-one-time.example.json)
- [approval.binding.replay-denied.example.json](examples/approval.binding.replay-denied.example.json)
- [approval.binding.scope-mismatch.example.json](examples/approval.binding.scope-mismatch.example.json)
- [approval.binding.blocked-mvp.example.json](examples/approval.binding.blocked-mvp.example.json)
- [approval.chain.valid-one-time.example.json](examples/approval.chain.valid-one-time.example.json)
- [approval.chain.denied-blocked-mvp.example.json](examples/approval.chain.denied-blocked-mvp.example.json)
- [approval.chain.expired-token-denied.example.json](examples/approval.chain.expired-token-denied.example.json)
- [approval.chain.revoked-token-denied.example.json](examples/approval.chain.revoked-token-denied.example.json)
- [approval.chain.scope-mismatch-denied.example.json](examples/approval.chain.scope-mismatch-denied.example.json)
- [approval.chain.tenant-mismatch-denied.example.json](examples/approval.chain.tenant-mismatch-denied.example.json)
- [approval.chain.replay-denied.example.json](examples/approval.chain.replay-denied.example.json)
- [approval.chain.lima-it-remediation-blocked.example.json](examples/approval.chain.lima-it-remediation-blocked.example.json)
- [approval.chain.tainted-input-denied.example.json](examples/approval.chain.tainted-input-denied.example.json)
- [model.route.example.json](examples/model.route.example.json)
- [model.route.mock-only-selected.example.json](examples/model.route.mock-only-selected.example.json)
- [model.route.tainted-privileged-denied.example.json](examples/model.route.tainted-privileged-denied.example.json)
- [model.route.subscription-planned-blocked-mvp.example.json](examples/model.route.subscription-planned-blocked-mvp.example.json)
- [model.route.local-planned-degraded.example.json](examples/model.route.local-planned-degraded.example.json)
- [tool.invocation.example.json](examples/tool.invocation.example.json)
- [tool.invocation.tainted-input-denied.example.json](examples/tool.invocation.tainted-input-denied.example.json)
- [memory.access.example.json](examples/memory.access.example.json)
- [helper.scope.file-helper.example.json](examples/helper.scope.file-helper.example.json)
- [helper.scope.memory-helper.example.json](examples/helper.scope.memory-helper.example.json)
- [helper.scope.it-helper-readonly.example.json](examples/helper.scope.it-helper-readonly.example.json)
- [taint.ref.prompt-injection-email.example.json](examples/taint.ref.prompt-injection-email.example.json)
- [connector.trust.example.json](examples/connector.trust.example.json)
- [connector.readiness.email-approved-for-lab.example.json](examples/connector.readiness.email-approved-for-lab.example.json)
- [connector.readiness.browser-blocked-mvp.example.json](examples/connector.readiness.browser-blocked-mvp.example.json)
- [connector.readiness.rmm-it-approval-required.example.json](examples/connector.readiness.rmm-it-approval-required.example.json)
- [connector.readiness.revoked.example.json](examples/connector.readiness.revoked.example.json)
- [connector.scope_review.least-privilege-satisfied.example.json](examples/connector.scope_review.least-privilege-satisfied.example.json)
- [connector.scope_review.overbroad-denied.example.json](examples/connector.scope_review.overbroad-denied.example.json)
- [connector.scope_review.object-auth-missing-failed-closed.example.json](examples/connector.scope_review.object-auth-missing-failed-closed.example.json)
- [connector.provider_profile.email-medium-risk.example.json](examples/connector.provider_profile.email-medium-risk.example.json)
- [connector.provider_profile.browser-blocked-mvp.example.json](examples/connector.provider_profile.browser-blocked-mvp.example.json)
- [connector.provider_profile.rmm-it-critical-review-required.example.json](examples/connector.provider_profile.rmm-it-critical-review-required.example.json)
- [connector.provider_profile.revoked.example.json](examples/connector.provider_profile.revoked.example.json)
- [connector.revocation_drill.revocation-passed.example.json](examples/connector.revocation_drill.revocation-passed.example.json)
- [connector.revocation_drill.disable-switch-failed-closed.example.json](examples/connector.revocation_drill.disable-switch-failed-closed.example.json)
- [connector.revocation_drill.cross-tenant-blocked.example.json](examples/connector.revocation_drill.cross-tenant-blocked.example.json)
- [connector.revocation_drill.prompt-injection-blocked.example.json](examples/connector.revocation_drill.prompt-injection-blocked.example.json)
- [connector.reconciliation.reconciled.example.json](examples/connector.reconciliation.reconciled.example.json)
- [connector.reconciliation.consent-revoked-drift.example.json](examples/connector.reconciliation.consent-revoked-drift.example.json)
- [connector.reconciliation.scope-overbroad-blocked.example.json](examples/connector.reconciliation.scope-overbroad-blocked.example.json)
- [connector.reconciliation.provider-critical-failed-closed.example.json](examples/connector.reconciliation.provider-critical-failed-closed.example.json)
- [connector.reconciliation.cross-tenant-blocked.example.json](examples/connector.reconciliation.cross-tenant-blocked.example.json)
- [connector.acceptance_score.email-approved-for-lab.example.json](examples/connector.acceptance_score.email-approved-for-lab.example.json)
- [connector.acceptance_score.provider-critical-review-required.example.json](examples/connector.acceptance_score.provider-critical-review-required.example.json)
- [connector.acceptance_score.revoked.example.json](examples/connector.acceptance_score.revoked.example.json)
- [connector.acceptance_score.failed-closed.example.json](examples/connector.acceptance_score.failed-closed.example.json)
- [connector.reconciliation_slo.current.example.json](examples/connector.reconciliation_slo.current.example.json)
- [connector.reconciliation_slo.revocation-pending.example.json](examples/connector.reconciliation_slo.revocation-pending.example.json)
- [connector.reconciliation_slo.missed-failed-closed.example.json](examples/connector.reconciliation_slo.missed-failed-closed.example.json)
- [connector.ownership.active.example.json](examples/connector.ownership.active.example.json)
- [connector.ownership.stale-failed-closed.example.json](examples/connector.ownership.stale-failed-closed.example.json)
- [connector.ownership.sod-violation.example.json](examples/connector.ownership.sod-violation.example.json)
- [connector.escalation.stale-owner-opened.example.json](examples/connector.escalation.stale-owner-opened.example.json)
- [connector.escalation.revocation-overdue-failed-closed.example.json](examples/connector.escalation.revocation-overdue-failed-closed.example.json)
- [connector.escalation.resolved-placeholder.example.json](examples/connector.escalation.resolved-placeholder.example.json)
- [console.alert.connector-provider-risk-critical.example.json](examples/console.alert.connector-provider-risk-critical.example.json)
- [console.alert.connector-reconciliation-drift.example.json](examples/console.alert.connector-reconciliation-drift.example.json)
- [console.alert.connector-score-degraded.example.json](examples/console.alert.connector-score-degraded.example.json)
- [console.alert.connector-owner-stale.example.json](examples/console.alert.connector-owner-stale.example.json)
- [supervisor.health.connector-risk-degraded.example.json](examples/supervisor.health.connector-risk-degraded.example.json)
- [supervisor.health.connector-reconciliation-blocked.example.json](examples/supervisor.health.connector-reconciliation-blocked.example.json)
- [supervisor.health.connector-slo-missed.example.json](examples/supervisor.health.connector-slo-missed.example.json)
- [supervisor.health.connector-ownership-degraded.example.json](examples/supervisor.health.connector-ownership-degraded.example.json)
- [evidence.artifact.example.json](examples/evidence.artifact.example.json)
- [evidence.artifact.denial-path.example.json](examples/evidence.artifact.denial-path.example.json)
- [evidence.artifact.chained-pre-post.example.json](examples/evidence.artifact.chained-pre-post.example.json)
- [evidence.ledger.entry.pre-action.example.json](examples/evidence.ledger.entry.pre-action.example.json)
- [evidence.ledger.entry.replay-denial.example.json](examples/evidence.ledger.entry.replay-denial.example.json)
- [evidence.ledger.entry.export-manifest.example.json](examples/evidence.ledger.entry.export-manifest.example.json)
- [evidence.ledger.entry.rollback.example.json](examples/evidence.ledger.entry.rollback.example.json)
- [evidence.ledger.entry.delete-review.example.json](examples/evidence.ledger.entry.delete-review.example.json)
- [evidence.ledger.entry.failed-closed-export.example.json](examples/evidence.ledger.entry.failed-closed-export.example.json)
- [evidence.failure.pre-action-blocked.example.json](examples/evidence.failure.pre-action-blocked.example.json)
- [evidence.failure.post-action-degraded.example.json](examples/evidence.failure.post-action-degraded.example.json)
- [evidence.failure.replay-store-unavailable.example.json](examples/evidence.failure.replay-store-unavailable.example.json)
- [evidence.export_manifest.prepared-redacted.example.json](examples/evidence.export_manifest.prepared-redacted.example.json)
- [evidence.export_manifest.denied-delete-conflict.example.json](examples/evidence.export_manifest.denied-delete-conflict.example.json)
- [evidence.export_manifest.blocked-delete-conflict.example.json](examples/evidence.export_manifest.blocked-delete-conflict.example.json)
- [evidence.export_manifest.exported-redacted-metadata-only.example.json](examples/evidence.export_manifest.exported-redacted-metadata-only.example.json)
- [incident.ops.example.json](examples/incident.ops.example.json)
- [sla.slo.example.json](examples/sla.slo.example.json)
- [lima_it.handoff.example.json](examples/lima_it.handoff.example.json)
- [lima_it.handoff.remediation-denied-mvp.example.json](examples/lima_it.handoff.remediation-denied-mvp.example.json)
- [task.execution.evidence-required-blocked.example.json](examples/task.execution.evidence-required-blocked.example.json)

Examples are sample records only. Runtime may not treat an example object as authorization, approval, evidence, policy, identity, token validity, connector readiness, or remediation permission.

## Validation

Contract validation is documented in [Phase 0 Validation](../docs/VALIDATION.md).

Run locally:

```powershell
python scripts/validate-contracts.py
python scripts/check-reason-codes.py
python scripts/check-doc-links.py
```

For full JSON Schema draft 2020-12 validation with format checks, install the development validation dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

CI runs strict validation with:

```bash
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
```

Reason-code conformance blocks:

- unknown reason codes in schemas/examples
- deprecated reason codes without compatibility records
- blocked reason codes in successful/completed/exported contexts
- breaking-change compatibility records without `affected_contracts` and
  `evidence_refs`
- missing `taxonomy_version` in any reason-bearing schema/example
- unsupported `taxonomy_version` values in reason-bearing examples

Examples map to schemas by explicit override table, declared `$schema_ref`,
`schema_ref`, `contract_name`, `contract_type`, or `type`, then by filename
longest-prefix convention. Current examples use `contract_name`, and each
schema must have at least one mapped example.

If `jsonschema` is unavailable locally, the validator falls back to JSON syntax,
schema structure, mapping, required top-level fields, unknown top-level fields,
example coverage, and unsafe-content scanning. That fallback is advisory only
and does not prove nested constraints, conditionals, enums, formats, or all type
rules. CI requires `jsonschema` and format-check support, so full JSON Schema validation runs there.

Validation does not authorize runtime behavior. It does not make live connectors,
external sends, software updates, remediation, production operations, or
privileged actions safe or approved. Future runtime behavior still needs
Guardian classification, approval policy, evidence capture, and fail-closed
handling.

## Shared Envelope

Every v1 schema requires a shared envelope:

- `contract_name`
- `contract_version`
- `schema_version`
- `tenant_id`
- `customer_context_id`
- `environment`
- `correlation_id`
- `causation_id`
- `idempotency_key`
- `producer`
- `policy_version`
- timestamps relevant to the event or record

Most action-bearing schemas also require:

- `data_classification`
- `risk_tier`
- `guardian_decision_id`
- `approval_required`
- `approval_request_id`
- `approval_token_id`
- `evidence_artifact_id` or `evidence_artifact_ids`

## Conditional Hardening

The v1 schemas use JSON Schema draft 2020-12 conditionals to block unsafe state combinations:

- `approval.request`, `approval.result`, `approval.token`, `token.verification`,
  and `approval.binding` bind approval status, approver identity, token state,
  token verification, one-time nonce use, denial, expiry, revoke, replay,
  scope mismatch, and blocked-MVP outcomes.
- `approval.chain` examples summarize valid and denied approval-chain bundles
  for review. They do not authorize runtime behavior.
- `guardian.decision` binds policy result, expiry, replay nonce, clock-skew
  allowance, action/task/worker/tool scope, approval binding, token
  verification, taint, evidence refs, and denial/failure reasons.
- `guardian.replay` records metadata-only replay-check outcomes for valid
  first use, replay denial, expiry, scope mismatch, and blocked-MVP checks.
- `replay.store.record` models future durable nonce/replay state and
  fail-closed atomicity metadata without implementing storage.
- `transaction.boundary` models future atomic transaction boundaries and
  status transitions as metadata-only records.
- `transaction.coordinator.event` models append-only coordinator lifecycle
  events, transition ordering, tenant-scoped idempotency scope, duplicate
  detection, and fail-closed reconciliation metadata.
- Cross-contract transaction/replay/evidence records include linkage refs plus
  `linkage_status` and `linkage_failure_reasons` so individually valid records
  cannot silently drift into an unsafe combined chain.
- Approval/Guardian contracts include reconciliation drill metadata
  (`reconciliation_status`, failure reasons, canonical IDs, and reconciliation
  evidence refs) to model fail-closed linkage classification across approval
  chain, Guardian replay, replay-store records, and transaction boundaries.
- `task.execution`, `tool.invocation`, `memory.access`, and `model.route` bind policy result, approval state, taint refs, evidence failure, terminal states, and denial/failure reasons.
- `worker.lifecycle`, `worker.heartbeat`, and `worker.deployment` bind identity failure, quarantine, revoke, evidence-writer failure, deployment refs, update/rollback posture, and healthy states.
- `supervisor.health` summarizes mock/lab worker, task, Guardian, and evidence
  state with reason codes. It is metadata-only reporting, not production
  monitoring.
- Governance schemas bind identity/MFA placeholder posture, access review,
  breakglass denial, audit export/delete request posture, connector consent and
  revocation, and signed update/rollback metadata. They do not implement
  identity providers, breakglass sessions, export/delete services, live
  connectors, update agents, or attestation mechanisms.
- Console schemas bind operator-visible views, alerts, and review actions to
  actor refs, role, related contract refs, policy refs, risk tier, evidence refs,
  status, and no-runtime-effect posture. They do not implement UI code or
  console runtime behavior.
- `lima_it.handoff` keeps diagnostics read-only and keeps remediation non-executing for Phase 0.
- `evidence.artifact` and `evidence.failure` bind redaction, evidence-writer failure, emergency spool refs, reconciliation, incident, and quarantine fields.
- `evidence.ledger.entry` models append-only ledger metadata with hash-chain
  linkage and raw/secret exclusion.
- `evidence.export_manifest` models export metadata using refs-only payloads
  with redaction/retention/delete-conflict placeholders.
- Governance/evidence contracts now include taxonomy-versioned reason-code fields
  so export/delete conflict, reconciliation drift, and denial evidence posture
  can fail closed with consistent vocabulary.
- Reason-code registry and compatibility contracts define canonical code status,
  severity, visibility, alias/deprecation posture, and breaking-change records
  so cross-contract reason semantics do not drift silently.

See [Schema Hardening Notes](../docs/SCHEMA_HARDENING_NOTES.md) for the reasoning and Phase 1A test expectations.

## Schema-Hardening Rules

- Blocked-MVP actions produce denial metadata, not approval tokens.
- Software install/update, remediation execution, production server touch, and regulated-system use remain blocked-MVP outcomes in v1 approval request/result/token records.
- Approval tokens are never bearer tokens and never broaden the approved scope.
- Token verification and approval binding fail closed for missing, expired,
  revoked, used, replayed, mismatched, ambiguous, wrong-scope, tainted, or
  blocked-MVP tokens and actions.
- Guardian decisions fail closed for missing expiry, ambiguous timestamps,
  future-effective timestamps beyond skew allowance, stale age, replayed
  decision nonce, revoked/consumed replay status, tenant/task/worker/action/
  tool-scope mismatch, approval-binding mismatch, token-verification mismatch,
  tainted input, and blocked-MVP action classes.
- Tainted content cannot directly authorize tool use, durable memory writes, external sends, approval scope, or remediation.
- Evidence-required privileged actions cannot proceed when evidence cannot be written.
- Cross-contract invariant checks fail closed when individually valid records
  disagree across tenant, customer context, task, Guardian decision, token
  verification, evidence, worker capability, taint, helper scope, memory, tool,
  or LIMA IT handoff boundaries.
- Helper scopes are supervisor-side, leased, narrow, visible, and cannot inherit worker trust.
- LIMA IT remediation remains request/denial metadata only in Phase 0; diagnostics are read-only.

## Review Process

Before a schema can unlock runtime design:

1. Confirm the contract stays inside the 1 Supervisor Server and 1-8 Arc worker MVP frame.
2. Confirm Guardian is the syscall gate for the action.
3. Confirm approval-required and blocked actions match [Autonomy Boundaries](../docs/AUTONOMY_BOUNDARIES.md).
4. Confirm evidence capture, redaction, retention, and export/delete posture are explicit.
5. Confirm no schema allows unrestricted tool execution, live connector use, external sends without approval, cross-tenant memory access, direct production remediation, or plaintext secrets.
6. Confirm the relevant threat scenario in [Threat Model](../docs/THREAT_MODEL.md) has a matching schema/control.
7. Run Phase 0 validation for schemas, examples, local Markdown links, and unsafe content.

## Policy References

Phase 0 policies are indexed in [docs/policies/README.md](../docs/policies/README.md). Contract consumers must treat these policies as pre-runtime requirements:

- [Approval Token Lifecycle](../docs/policies/approval-token-lifecycle.md)
- [Evidence Writer Failure](../docs/policies/evidence-writer-failure.md)
- [Retention And Redaction Matrix](../docs/policies/retention-redaction-matrix.md)
- [Prompt Injection Handling](../docs/policies/prompt-injection-handling.md)
- [Worker Quarantine And Re-Enrollment](../docs/policies/worker-quarantine-reenrollment.md)
- [LIMA IT Diagnostic And Remediation Handoff](../docs/policies/lima-it-diagnostic-remediation-handoff.md)
- [Governance Policies](../docs/governance/README.md)

Guardian decisions must link to relevant `policy_refs`, `policy_version`, approval state, and evidence artifact refs. If the needed policy is missing or ambiguous, consumers fail closed.

## Runtime Block Rule

Runtime cannot be built for a behavior until the relevant contract is present, reviewed, and linked to Guardian, approval, evidence, failure, and MVP acceptance gates.

Phase 0 schemas are not permission to implement services. They are the minimum interface boundary future runtime work must satisfy.

## Taxonomy Catalog

- [reason-code-registry.catalog.json](taxonomy/reason-code-registry.catalog.json)
  records model-route, health, worker-attestation, and signed-update/rollback
  reason-code catalog snapshots for docs/contracts/tests consistency.
