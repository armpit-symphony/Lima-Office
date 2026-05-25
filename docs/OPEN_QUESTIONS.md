# Open Questions

This file tracks remaining blockers after the Phase 0 / Phase 1A closeout. The
questions below must stay visible until they are resolved in docs, contracts,
policies, runbooks, and tests. None of these items approve live connectors,
external sends, real remediation, production operations, or customer-system
mutation.

Current canonical integration status is tracked in [Baseline](BASELINE.md). The
missing cross-contract invariant checkpoint remains absent from this checkout
and from `origin`; [Cross-Contract Invariants](CROSS_CONTRACT_INVARIANTS.md)
documents the reachable v2 checkpoint that supersedes it.

## Security / Governance

- Operator IdP/MFA implementation: which IdP, MFA mechanism, session TTL,
  device trust posture, and identity assurance evidence should back the
  placeholders in [Identity And MFA Policy](governance/IDENTITY_AND_MFA_POLICY.md)?
- Access review cadence: should the quarterly placeholder in
  [Access Review](runbooks/access-review.md) become the default cadence, and
  which events trigger additional reviews?
- Runtime RBAC matrix: what exact role/action matrix applies after the operator
  IdP is selected? Phase 1A now defines metadata posture in
  [RBAC IdP MFA Session Device Trust Matrix](governance/RBAC_IDP_MFA_SESSION_DEVICE_TRUST_MATRIX.md);
  open question is implementation-time enforcement and review ownership.
- Breakglass implementation decision: breakglass is currently blocked in
  [Breakglass Policy](governance/BREAKGLASS_POLICY.md). Should a future lane
  implement any emergency path, and which action classes remain blocked?
- LIMA IT approver separation implementation: [Approver Separation Policy](governance/APPROVER_SEPARATION_POLICY.md)
  defines self-approval and conflict blocks, but who is the final independent
  remediation approver if remediation is ever reviewed after MVP?

## Data / Compliance

- Retention defaults: what concrete retention periods replace the placeholders
  in [Retention Redaction Policy](governance/RETENTION_REDACTION_POLICY.md)?
- Redaction taxonomy: are the initial profiles in
  [Retention Redaction Policy](governance/RETENTION_REDACTION_POLICY.md)
  sufficient, and what redaction rule applies to each free-text field?
- Export/delete taxonomy governance: Phase 1A now defines canonical reason-code
  docs in [Reconciliation Reason Taxonomy](taxonomy/RECONCILIATION_REASON_TAXONOMY.md)
  and [Evidence Reason Taxonomy](taxonomy/EVIDENCE_REASON_TAXONOMY.md); what
  final legal/compliance review and versioning governance is required before
  durable implementation?
- Reason-code deprecation/removal governance: after
  [Reason Code Registry](taxonomy/REASON_CODE_REGISTRY.md) and
  [Reason Code Compatibility Policy](taxonomy/REASON_CODE_COMPATIBILITY_POLICY.md),
  what mandatory migration window and evidence burden should be required before
  any major taxonomy removal is allowed?
- Taxonomy-version expansion boundary: should additional legacy reason-like
  fields (`result_reason_code`, `blocked_reason_code`,
  `quarantine_reason_code`) be moved under strict taxonomy governance in this
  major-version line, or deferred to a future major-version migration lane?
- Audit export: what final export manifest format, integrity metadata, package
  retention, and access-control refs are required beyond
  [Audit Export And Customer Exit Policy](governance/AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md)?
- Export-manifest interoperability: should `evidence.export_manifest` remain a
  single contract or be split into request/approval/package records in a future
  major version?
- Delete/export conflict precedence: when export and delete requests conflict,
  what deterministic precedence and proof model governs denied vs failed-closed
  outcomes?
- Customer exit/delete: what exact proof fields, preservation conflict rules,
  and device/memory/cache reset evidence are required before implementation?
- Durable evidence/export posture: what storage, emergency spool, retry/backoff,
  disk-full threshold, reconciliation, and export posture must exist before
  runtime expansion?
- Evidence ledger format: what canonical hash material, parent/previous linkage
  rules, and verification cadence should back `evidence.ledger.entry`?
- First compliance target: what governance or compliance mapping matters first,
  without claiming certification?

## Runtime

- Durable approval-token consumption: `approval.binding` now defines and tests
  the mock/in-memory binding model, but what durable atomic consume mechanism,
  replay store, concurrency rule, evidence export, and incident path should be
  approved before any side-effecting approval path exists?
- Durable Guardian replay posture: Guardian expiry/replay is defined and tested
  for mock/in-memory Phase 1A flows in
  [Guardian Expiry And Replay Policy](GUARDIAN_EXPIRY_REPLAY_POLICY.md), but
  what durable replay store, atomic decision consumption, concurrency rule,
  idempotency behavior, exportable replay evidence, and incident path should be
  approved before any side-effecting path exists?
- Replay-store record posture: what transactional boundaries, conflict retries,
  and durability class should back `replay.store.record` before runtime
  expansion?
- Transaction-boundary posture: what final participant model, isolation level,
  and idempotency guarantees should back `transaction.boundary` before runtime
  expansion?
- Transaction coordinator posture: what final transition matrix, immutability
  enforcement model, and duplicate-request resolution semantics should back
  `transaction.coordinator.event` before runtime expansion?
- Cross-contract linkage posture: which linkage fields become mandatory for
  implementation-time foreign-key guarantees across
  `transaction.coordinator.event`, `transaction.boundary`,
  `replay.store.record`, `evidence.ledger.entry`, `evidence.artifact`, and
  `evidence.export_manifest`?
- Linkage drift taxonomy enforcement: reason-code registries now exist, but how
  should runtime emitters and storage pipelines enforce registry-only values in
  durable mode?
- Reconciliation ownership: which role owns terminal-state selection for partial
  commit ambiguity during coordinator recovery, and what approval separation is
  required?
- Approval/Guardian reconciliation taxonomy rollout: schemas now carry taxonomy
  placeholders, but what final migration path applies to legacy free-form
  reason strings when durable services are introduced?
- Reconciliation evidence minimum set: what exact mandatory evidence references
  are required per drift class (`missing_ref`, `mismatched_binding`,
  `stale_decision`, `replay_mismatch`, `coordinator_mismatch`,
  `cross_tenant_blocked`, `blocked_mvp`)?
- Health reason taxonomy: which reason code set should become normative for
  Supervisor health, Guardian decisions, worker state, queue depth, evidence
  status, connector readiness, LIMA IT handoff, and degraded/offline/quarantine
  transitions beyond the planning defaults in [Worker Deployment Blueprint](deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)
  and the scaffolding in [Health Reason Taxonomy](ux/HEALTH_REASON_TAXONOMY.md)?
- Model-route defaults by tenant: Phase 1A now defines safe route-mode and
  route-status posture in [Model Routing Defaults](architecture/MODEL_ROUTING_DEFAULTS.md)
  and `model.route` contracts, but tenant/customer override governance remains
  open.
- Heartbeat thresholds: what heartbeat interval, missed-heartbeat thresholds,
  stale-age limits, and escalation timing should apply in lab mode?
- Worker attestation: what trust root, attestation method, TPM/secure boot
  requirement, and key lifecycle should replace the placeholder in
  [Worker Attestation Policy](governance/WORKER_ATTESTATION_POLICY.md)?
- Update rollback: what signed/verified source format, signer authority,
  known-good selection, rollback trigger matrix, and approval workflow should
  replace the placeholders in [Signed Update Rollback Policy](governance/SIGNED_UPDATE_ROLLBACK_POLICY.md)?
- Worker hardware baseline: what exceptions, local-model sizing thresholds, and
  exact lab acceptance criteria should be applied to the vendor-neutral classes
  in [Worker Hardware Baseline](deployment/WORKER_HARDWARE_BASELINE.md)?
- Small-business supportability: what offline/ISP outage, power-loss recovery,
  log retention, disk-full behavior, device replacement, support RACI, and
  operator escalation assumptions remain required beyond the field checklist?
- Cross-contract invariant source: the 2026-05-22 reconciliation check found no
  local object and no `origin` branch for
  `phase-1a-cross-contract-invariants` / `e71431007ddbe96c3e141b77591efc2508c53e5d`
  after `git fetch --all --prune`; `phase-1a-invariant-checkpoint-v2`
  supersedes it as the reachable replacement candidate. Remaining question:
  should the old branch name be permanently retired or kept as a historical
  missing checkpoint note?

## Connectors And Deployment

- Connector consent/scope/revocation: what final consent expiry, provider scope
  mapping, live-review threshold, revocation verification, and prompt-injection
  test evidence should replace the placeholders in
  [Connector Consent Scope Revocation Policy](governance/CONNECTOR_CONSENT_SCOPE_REVOCATION_POLICY.md)?
- Model routing defaults: what tasks can use local models, what tasks can use
  subscription/cloud model classes, and what data classifications block cloud
  routing?
- First deployment posture: is the first lab deployment on-prem, hybrid, or
  managed private cloud, and what acceptance threshold moves it from lab-only to
  pilot-review?
- First workflow posture: what target vertical or workflow should be considered
  first while staying draft-only or mock-only?
- Connector prompt-injection evaluation: what test and review evidence is
  required before connector-handled content can influence model/tool decisions?

Resolved in [Deployment Docs](deployment/README.md) and `worker.deployment`:

- Vendor-neutral worker hardware classes are documented for lightweight,
  standard, local-model, and supervisor/helper-capable machines.
- Lab/default network posture is documented as no public inbound worker exposure,
  no direct cross-worker trust, local-supervisor-first communication, and no
  direct production-system remediation.
- Worker deployment records can represent hardware, OS, network, Supervisor
  endpoint, policy/model refs, encryption, attestation placeholder,
  update/rollback posture, and evidence refs.
- Worker deployment, update/rollback, and field IT preflight runbooks exist as
  manual operator docs only.

Resolved as fail-closed governance scaffolding in [Governance Docs](governance/README.md)
and governance contracts:

- Identity/MFA, role, session, device trust, and access review posture can be
  represented by `governance.identity` and `governance.access_review`.
- Approver separation and blocked self-approval cases are documented.
- Breakglass is explicitly blocked for MVP and can be represented by
  `governance.breakglass` denial metadata.
- Retention/redaction record coverage, export/delete review posture, and
  customer exit process are documented as placeholders without final legal
  retention periods.
- Connector consent, scope review, revocation, rotation placeholder, data
  class, and prompt-injection review posture can be represented by
  `governance.connector_consent`.
- Worker attestation and signed update/rollback posture can be represented by
  policy docs, runbooks, and `governance.update_record`.

Resolved as console UX scaffolding in [UX / Control-Room Docs](ux/README.md)
and console contracts:

- Operator console navigation, workflow coverage, approval inbox, evidence
  viewer, worker fleet, LIMA IT panel, permissions, and information
  architecture are documented as specs only.
- Initial health reason taxonomy is documented for worker, evidence, Guardian,
  approval, taint, connector, attestation, update/rollback, LIMA IT, retention,
  export/delete, and IdP/MFA states.
- `console.view`, `console.alert`, and `console.action` can represent
  metadata-only console views, alerts, and review actions without UI code or
  runtime effects.

Resolved in [Schema Hardening Notes](SCHEMA_HARDENING_NOTES.md) and [contracts/v1](../contracts/v1):

- `approval.result` is a separate v1 schema.
- `helper.scope` is a separate v1 schema.
- v1 schemas include conditionals for approval token lifecycle states, blocked-MVP denial, LIMA IT remediation constraints, evidence-required completion, evidence failure, token verification, and taint refs.

Resolved in [Approval Token Runtime Binding](APPROVAL_TOKEN_RUNTIME_BINDING.md)
and `approval.binding` / `approval.chain`:

- Approval request/result/token/verification/Guardian/task/tool/worker/evidence
  binding is represented as a first-class `approval.binding` record.
- Valid one-time binding, consumed binding, replay denial, scope mismatch,
  blocked-MVP, tenant mismatch, expired token, revoked token, LIMA IT
  remediation block, and tainted input denial are covered by schemas, examples,
  and mock tests.
- Approval-required mock task enqueueing requires a valid binding in addition
  to token verification.

Resolved in [Guardian Expiry And Replay Policy](GUARDIAN_EXPIRY_REPLAY_POLICY.md)
and `guardian.decision` / `guardian.replay`:

- Guardian decision expiry, issued/effective time, max age, clock-skew
  allowance, one-time decision nonce, replay policy, scope hash, tenant/task/
  worker/action/tool binding, approval binding, token verification, and
  evidence refs are represented in contracts.
- Valid first use, replay denial, expiry, scope mismatch, blocked-MVP,
  clock-skew denial, and LIMA IT remediation denial are covered by schemas,
  examples, and mock tests.
- Phase 1A mock runtime rejects replayed, stale, expired, future-effective,
  ambiguous, mismatched, tainted, and blocked-MVP Guardian decisions.

Resolved as mock-hardening drills in
[APPROVAL_GUARDIAN_RECONCILIATION_DRILLS](APPROVAL_GUARDIAN_RECONCILIATION_DRILLS.md):

- Approval/Guardian linkage drift classes are explicitly modeled and tested
  against fail-closed outcomes.
- Reconciliation status and canonical-ID fields are represented across
  approval/Guardian/replay/transaction/ledger contracts.
- A mock-only reconciliation helper classifies linkage status deterministically
  and never authorizes real action.

Resolved in [Phase 0 Validation](VALIDATION.md) and [Phase 0 validation workflow](../.github/workflows/phase0-validation.yml):

- CI uses [requirements-dev.txt](../requirements-dev.txt) for JSON Schema draft 2020-12 validation with format checks.

Resolved in [Phase 1A Runtime Scaffolding](PHASE_1A_RUNTIME_SCAFFOLDING.md):

- Runtime contract validation requires `jsonschema` and fails closed if it is unavailable.
- Phase 1A runtime state is in-memory mock scaffolding only, with no live connectors, external sends, remediation execution, external model API calls, browser automation, services, databases, or production-system access.

## Policy Follow-Ups

- What concrete default retention periods should replace placeholders in [Retention And Redaction Matrix](policies/retention-redaction-matrix.md)?
- What redaction profile taxonomy should apply by record type and data classification?
- What redaction strategy should apply to free-text reason fields such as `denial_reason`, `failure_reason`, `summary`, and `result_summary`?
- What audit export manifest format is required?
- What customer exit/delete/reset process and proof fields are required?
- What local emergency evidence spool depth, retry/backoff, disk-full threshold, and reconciliation process should be approved?
- What final signing root, source format, known-good selection, and rollback
  trigger matrix should replace the placeholders in the update rollback policy?
- What final connector consent expiry, provider scope mapping, and revocation
  verification are required before any live connector review?
- What access role/RBAC matrix should be enforced once the operator identity provider is selected?
- What session service semantics (TTL source of truth, revocation propagation,
  and step-up intent binding) should replace the placeholder
  `governance.session_policy` metadata contract?
- What device posture and attestation signals should replace the placeholder
  `governance.device_trust` metadata contract before privileged runtime paths
  are implemented?
- What operator identity provider and MFA level should be assumed for approval and token verification?
- What worker attestation method should be used before re-enrollment can be automated?
- Should any future breakglass implementation be allowed beyond the current
  blocked placeholder, and which actions remain blocked during breakglass?
- If LIMA IT remediation is reviewed after MVP, who is the independent approver
  and what separation evidence is required?
