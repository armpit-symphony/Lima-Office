# Security Model

## Baseline

LIMA Office OS uses a Zero Trust baseline for one small-business tenant at a time. No worker, helper agent, connector, model provider, local file, browser page, tool output, or operator action is trusted by default.

Guardian is the syscall gate for model, tool, file, network, connector, outbound, scheduled, and privileged actions.

## Authenticated Worker-Supervisor Channel

Supervisor-to-worker communication must use authenticated device identity before any runtime work is approved. The plan should include:

- Device enrollment.
- mTLS or equivalent authenticated channel.
- Capability leases.
- Key rotation.
- Revocation.
- Quarantine.
- Replacement flow.

The [Network Blueprint](deployment/NETWORK_BLUEPRINT.md) keeps worker
communication local-supervisor-first, denies public inbound worker exposure, and
blocks direct cross-worker trust. The trust bootstrap, CA/certificate lifecycle,
key storage, rotation, and recovery process remain open governance/security
items.

## Worker Identity And Attestation Plan

Each Arc worker must have:

- Stable worker ID.
- Device identity reference.
- Channel identity reference.
- Role assignment.
- Capability manifest.
- Capability lease.
- Approved tenant binding.
- Health and heartbeat record.
- Quarantine/revoke state.

Hardware attestation is an open question for Phase 0.

Phase 1A trust-root metadata hardening is documented in
[Worker Attestation Trust Root](architecture/WORKER_ATTESTATION_TRUST_ROOT.md)
and represented by
[worker.attestation.schema.json](../contracts/v1/worker.attestation.schema.json).
Verifier appraisal/reference-value governance is documented in
[Attestation Verifier Policy Reference Values](architecture/ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md)
and
[Attestation Reference Value Governance](governance/ATTESTATION_REFERENCE_VALUE_GOVERNANCE.md),
with metadata contracts for `attestation.reference_value`,
`attestation.endorsement`, `attestation.appraisal_policy`, and
`attestation.result`.

Deployment planning records may use `attestation_status: not_required_phase0`
or `manual_review_only`. These values mean weak lab trust only; they do not
allow privileged work, automated re-enrollment, live connector access, or
production operation.

## Secret Storage Rules

- No hardcoded secrets.
- No plaintext API keys.
- No tokens in docs, logs, screenshots, prompts, or evidence summaries.
- Use secret references, not secret values.
- Approval token contracts store metadata and digest/reference fields only, not bearer token material.
- Connector trust uses `secrets_ref` only and `secret_material_present: false` in Phase 0.
- Future secret storage must support rotation, revocation, least privilege, and audit.

## Least Privilege

Workers and helper agents receive only the tool packs needed for the task, role, tenant, and approval state. Default access is deny.

## RBAC

Initial roles:

- Operator.
- Approver.
- Supervisor admin.
- Field IT reviewer.
- Security reviewer.
- Worker node.
- Helper agent.

Privileged actions require role checks, Guardian decision, approval when required, and evidence.

Governance scaffolding for identity, MFA, access review, and role separation is
documented in [Identity And MFA Policy](governance/IDENTITY_AND_MFA_POLICY.md)
and [Approver Separation Policy](governance/APPROVER_SEPARATION_POLICY.md).
The canonical role/action/session/device-trust matrix is documented in
[RBAC IdP MFA Session Device Trust Matrix](governance/RBAC_IDP_MFA_SESSION_DEVICE_TRUST_MATRIX.md)
and represented by `governance.rbac_matrix`, `governance.session_policy`, and
`governance.device_trust` contracts.
The exact IdP, MFA mechanism, session TTL, device trust rule, and runtime RBAC
enforcement remain unresolved and must fail closed.

## Tenant Isolation

Even with one tenant at a time, the system must design tenant isolation from day one:

- Tenant ID on contracts and evidence.
- Tenant-scoped memory.
- Tenant-scoped connector readiness.
- Tenant-scoped worker assignments.
- Tenant-scoped audit export.
- Customer exit/delete/reset posture.

Cross-tenant memory sharing is blocked for MVP.

## Data Classification

Initial classifications:

- `public`
- `internal`
- `customer_confidential`
- `sensitive_hr`
- `sensitive_finance`
- `sensitive_legal`
- `sensitive_medical`
- `secret`

Sensitive HR, finance, legal, medical, and secret data require approval or remain blocked until policy is complete.

## Logging And Audit Requirements

Audit records must capture:

- Actor.
- Tenant.
- Worker/helper identity.
- Action class.
- Resource reference.
- Guardian decision.
- Approval result.
- Risk tier.
- Redaction status.
- Evidence artifact ID.
- Timestamp.
- Correlation ID.

Logs must avoid secrets, tokens, raw sensitive payloads, and plaintext API keys.

## Approval-Gated Privileged Actions

Approval is mandatory for:

- External messages.
- Connector writes.
- File delete/overwrite.
- Customer record mutation.
- Software install/update.
- Remediation.
- Production server touch.
- Payment, legal, or regulated systems.
- Sensitive HR/finance/legal/medical access.

Approval-token lifecycle policy is defined in [Approval Token Lifecycle](policies/approval-token-lifecycle.md), with binding details in [Approval Token Runtime Binding](APPROVAL_TOKEN_RUNTIME_BINDING.md). Approval tokens are metadata-only, single-use, scoped, expiring, revocable, and non-executing in Phase 0/Phase 1A.

Approval result, token verification, and binding records are separate controls. `approval.result` records the human decision outcome; `token.verification` records a point-in-time fail-closed check; `approval.binding` proves the request/result/token/verification/Guardian/task/tool/worker/evidence chain matches before an approval-required mock path can proceed. Token verification alone is not enough.

The [Approval Inbox Spec](ux/APPROVAL_INBOX_SPEC.md) requires the console to
show Guardian decision, policy refs, evidence refs, taint status, scope hash,
expiry, and separation checks before any approval metadata can be recorded.
Blocked-MVP, stale, missing-evidence, tainted, self-approval, and token-mismatch
states remain fail closed.

## Guardian Expiry And Replay

Guardian decisions are time-bounded and context-bound in Phase 1A mock
hardening. [Guardian Expiry And Replay Policy](GUARDIAN_EXPIRY_REPLAY_POLICY.md)
requires `issued_at`, `effective_at`, `expires_at`, `max_age_seconds`,
`clock_skew_allowance_seconds`, one-time `decision_nonce`, decision scope hash,
bound tenant/task/worker/action/tool scope, approval binding, token
verification, and evidence refs.

The mock `GuardianDecisionReplayVerifier` tracks consumed decision nonces in
memory for tests only. A usable decision must be fresh, one-time, non-replayed,
non-revoked, non-tainted, and exact to the requested action. Durable replay
storage, atomic distributed consumption, idempotency, and non-test operations
thresholds remain open gates.

Phase 1A now also defines metadata contracts for future durable replay posture:

- [replay.store.record.schema.json](../contracts/v1/replay.store.record.schema.json)
  models nonce reservation/consumption/replay-denial/fail-closed outcomes.
- `failed_closed` atomicity, missing denial evidence, or tenant/action/scope
  mismatch must block authorization.
- [DURABLE_REPLAY_EVIDENCE_POSTURE.md](DURABLE_REPLAY_EVIDENCE_POSTURE.md)
  defines gates before any side-effecting runtime can exist.

## Secure Update And Rollback

Update and rollback posture must include:

- Signed or verified update source.
- Known-good version.
- Rollback trigger.
- Evidence capture.
- Operator visibility.
- Approval for software changes.
- Quarantine on failed or suspicious update.

The [Update Rollback Blueprint](deployment/UPDATE_ROLLBACK_BLUEPRINT.md)
defines update channels as policy bundle, worker runtime, model bundle, and
config refs. Automatic update execution is blocked for MVP. Software
install/update remains approval-required and non-executing in this docs lane.
Governance metadata for update review is represented by
[governance.update_record.schema.json](../contracts/v1/governance.update_record.schema.json)
and [Signed Update Rollback Policy](governance/SIGNED_UPDATE_ROLLBACK_POLICY.md).
Phase 1A also adds metadata-only
[update.rollback.schema.json](../contracts/v1/update.rollback.schema.json) and
[Signed Update Rollback Trust](architecture/SIGNED_UPDATE_ROLLBACK_TRUST.md).

## Connector Trust Program

Connectors remain mock/readiness-only in Phase 0. Future connector trust must document:

- Consent.
- OAuth/scope review.
- Read/write/admin tier.
- Token storage reference.
- Revocation.
- Data classification.
- Prompt injection exposure.
- Audit/evidence.

[Connector Consent Scope Revocation Policy](governance/CONNECTOR_CONSENT_SCOPE_REVOCATION_POLICY.md)
defines the current fail-closed consent, scope, and revocation posture. It does
not authorize live connector access.

[Live Connector Criteria](architecture/LIVE_CONNECTOR_CRITERIA.md) and
[Live Connector Readiness Review](runbooks/live-connector-readiness-review.md)
define the metadata-only readiness lifecycle, least-privilege/object/property
authorization checks, outbound policy gates, and revocation drill posture
required before any future lab-live connector implementation lane.

[Connector Provider Risk Profiles](architecture/CONNECTOR_PROVIDER_RISK_PROFILES.md)
and [Connector Revocation Disable Drills](CONNECTOR_REVOCATION_DISABLE_DRILLS.md)
extend this posture with provider-specific risk levels, disable-switch and
revocation verification placeholders, and fail-closed drill evidence linkage.
No connector provider integration, token runtime, or external API calls are
implemented.

## Breakglass

Breakglass is a blocked placeholder in MVP. Requests can be represented by
[governance.breakglass.schema.json](../contracts/v1/governance.breakglass.schema.json)
and [Breakglass Policy](governance/BREAKGLASS_POLICY.md), but no breakglass
session, bypass, or emergency runtime authority exists.

## Audit Export And Customer Exit

Audit export and customer exit/delete posture is documented in
[Audit Export And Customer Exit Policy](governance/AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md)
and [Retention Redaction Policy](governance/RETENTION_REDACTION_POLICY.md).
Final legal retention periods, storage design, and delete conflict rules remain
open; ambiguous export/delete requests fail closed.

`evidence.export_manifest` now represents refs-only export metadata and requires
redaction/retention placeholders. Denied or blocked export/delete outcomes
require explicit conflict refs.

## Production Action Rule

No production actions are allowed without policy, Guardian decision, required approval, evidence capture, and explicit future authorization.

Current Phase 0 policy docs keep production server touch and remediation execution blocked. LIMA IT diagnostics are read-only; remediation remains draft/request-only until future policy and contracts explicitly authorize more.

## Policy Runtime Blockers

Before runtime scaffolding, the following policies must be resolved or carried as explicit fail-closed blockers:

- [Evidence Writer Failure](policies/evidence-writer-failure.md)
- [Retention And Redaction Matrix](policies/retention-redaction-matrix.md)
- [Prompt Injection Handling](policies/prompt-injection-handling.md)
- [Worker Quarantine And Re-Enrollment](policies/worker-quarantine-reenrollment.md)
- [LIMA IT Diagnostic And Remediation Handoff](policies/lima-it-diagnostic-remediation-handoff.md)
- [Governance Policies](governance/README.md)

## Schema Control Points

The Phase 0 field-level schemas in [contracts/v1](../contracts/v1) define the minimum security metadata for future runtime work:

- Approval token: [approval.token.schema.json](../contracts/v1/approval.token.schema.json) requires task/action/resource binding, expiry, one-time use, replay-protection refs, revocation state, and evidence. It must not contain token material.
- Guardian replay: [guardian.replay.schema.json](../contracts/v1/guardian.replay.schema.json)
  records metadata-only valid first-use, replay denial, expiry, mismatch, and
  blocked-MVP check outcomes. It does not authorize execution.
- Replay store record:
  [replay.store.record.schema.json](../contracts/v1/replay.store.record.schema.json)
  records nonce status and atomicity posture for future durable replay design.
  It is metadata-only and fail-closed on inconsistency.
- Approval result: [approval.result.schema.json](../contracts/v1/approval.result.schema.json) records approved, denied, expired, cancelled, superseded, partial, and blocked-MVP outcomes with evidence.
- Token verification: [token.verification.schema.json](../contracts/v1/token.verification.schema.json) records valid and fail-closed results for expired, revoked, used, missing, mismatched, ambiguous, and wrong-scope tokens.
- Helper scope: [helper.scope.schema.json](../contracts/v1/helper.scope.schema.json) keeps helper agents supervisor-side, leased, narrowly scoped, and unable to inherit worker trust.
- Taint reference: [taint.ref.schema.json](../contracts/v1/taint.ref.schema.json) propagates prompt-injection and untrusted-content state across model, task, tool, memory, approval, and evidence records.
- Worker identity: [worker.lifecycle.schema.json](../contracts/v1/worker.lifecycle.schema.json), [worker.heartbeat.schema.json](../contracts/v1/worker.heartbeat.schema.json), and [worker.deployment.schema.json](../contracts/v1/worker.deployment.schema.json) require device identity refs, channel identity refs, deployment refs, capability lease/hash posture, heartbeat sequence, supervisor receive time, evidence writer state, quarantine, revoke, update/rollback, and deployment metadata.
- Model routing: [model.route.schema.json](../contracts/v1/model.route.schema.json)
  records fail-closed route posture (`mock_only`, `local_planned`,
  `subscription_planned`, `blocked_mvp`), route status/reason codes, taint/risk
  gating, RBAC/session/device trust refs, fallback constraints, and evidence.
  High-risk selected routes now also require attestation/update appraisal refs
  (`worker_attestation_ref`, `attestation_result_ref`, `appraisal_policy_ref`,
  `update_rollback_ref`) so trust drift blocks privileged routing metadata.
  It explicitly blocks live provider calls and local inference execution in
  Phase 1A metadata lanes.
- Attestation lineage/authority:
  [attestation.result.lineage.schema.json](../contracts/v1/attestation.result.lineage.schema.json)
  and
  [attestation.authority.schema.json](../contracts/v1/attestation.authority.schema.json)
  bind verifier-owner/reference-approver metadata, revocation propagation
  posture, and fail-closed trust-effect transitions.
- Attestation reconciliation:
  [attestation.reconciliation.schema.json](../contracts/v1/attestation.reconciliation.schema.json)
  binds lineage/authority/reference/endorsement/appraisal/result metadata to
  model-route, worker, transaction, and evidence-ledger refs, and fails closed
  on drift classes such as cross-tenant linkage, revocation-not-propagated, and
  committed-transaction-with-revoked-attestation.
- Tool invocation: [tool.invocation.schema.json](../contracts/v1/tool.invocation.schema.json) requires tool pack/version, sandbox profile, side-effect class, file/network/connector scope, dry-run posture, approval token/binding linkage where needed, and evidence.
- Memory access: [memory.access.schema.json](../contracts/v1/memory.access.schema.json) requires tenant namespace, purpose, retention class, delete/export posture, prompt-injection scan state, and `cross_tenant_access: false`.
- Connector trust: [connector.trust.schema.json](../contracts/v1/connector.trust.schema.json) is mock/readiness-only in Phase 0 with `mock_only: true`, `live_access_enabled: false`, `secret_material_present: false`, consent/scope review posture, and revocation state.
- Connector readiness and scope review:
  [connector.readiness.schema.json](../contracts/v1/connector.readiness.schema.json)
  and
  [connector.scope_review.schema.json](../contracts/v1/connector.scope_review.schema.json)
  define metadata-only lifecycle/readiness gates, least-privilege review,
  object/property authorization mapping, blocked-MVP connector classes, and
  fail-closed reason/evidence posture.
- Evidence artifact: [evidence.artifact.schema.json](../contracts/v1/evidence.artifact.schema.json) defines redaction, retention, payload/integrity refs, export/delete posture, access-control refs, and evidence chain metadata.
- Evidence failure: [evidence.failure.schema.json](../contracts/v1/evidence.failure.schema.json) records pre-action blocks, post-action degraded state, emergency spool refs, reconciliation, incidents, and quarantine/token-revoke posture.
- Evidence export manifest:
  [evidence.export_manifest.schema.json](../contracts/v1/evidence.export_manifest.schema.json)
  records refs-only export metadata, included/excluded evidence refs, redaction
  profile refs, retention refs, and delete-conflict refs.
- LIMA IT handoff: [lima_it.handoff.schema.json](../contracts/v1/lima_it.handoff.schema.json) separates read-only diagnostics from approval-required remediation and blocks production touch in MVP.
- LIMA IT remediation-denied example: [lima_it.handoff.remediation-denied-mvp.example.json](../contracts/examples/lima_it.handoff.remediation-denied-mvp.example.json) shows remediation request metadata denied for Phase 0 with no execution authorization.
- Governance identity/access review/breakglass/audit export/connector consent/update records: [governance.identity.schema.json](../contracts/v1/governance.identity.schema.json), [governance.access_review.schema.json](../contracts/v1/governance.access_review.schema.json), [governance.breakglass.schema.json](../contracts/v1/governance.breakglass.schema.json), [governance.audit_export.schema.json](../contracts/v1/governance.audit_export.schema.json), [governance.connector_consent.schema.json](../contracts/v1/governance.connector_consent.schema.json), and [governance.update_record.schema.json](../contracts/v1/governance.update_record.schema.json) record governance posture without implementing live capabilities.
- Console view/alert/action records: [console.view.schema.json](../contracts/v1/console.view.schema.json), [console.alert.schema.json](../contracts/v1/console.alert.schema.json), and [console.action.schema.json](../contracts/v1/console.action.schema.json) record metadata-only console posture without implementing UI or runtime controls.

## Conceptual Standards Mapping

This mapping is conceptual and does not claim certification or compliance.

- NIST CSF 2.0: Govern, identify, protect, detect, respond, and recover are reflected in contracts, risk tiers, evidence, incident runbooks, and recovery posture.
- NIST AI RMF: Govern, map, measure, and manage are reflected in Guardian decisions, model routing records, human approval, evidence, and open risk tracking.
- NIST SP 800-207 Zero Trust: Never trust by default; verify worker identity, operator role, connector scope, and every action request.
- CISA Secure by Design: Favor least privilege, secure defaults, auditability, update/rollback posture, and no hardcoded secrets.
