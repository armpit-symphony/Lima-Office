# LIMA Office OS Status

Project name: LIMA Office OS

Canonical integration branch: `integration/phase-0-1a-baseline`

Superseding invariant checkpoint branch: `phase-1a-invariant-checkpoint-v2`

Current working branch: `durable-attestation-lineage-authority-design`

Integration source branch: `operator-console-ux-spec` at
`bac6f80cc63dd15ec7cd3d669193160c3766a8e1`

Current reachable baseline: Phase 0 architecture/contracts/policies, Phase 1A
mock runtime scaffolding, closeout archive, worker deployment blueprint,
governance policy details, and operator console UX specification.

Current phase: Phase 1A durable attestation lineage and verifier-owner authority
hardening. Phase 1A mock runtime scaffolding is present, the v2 invariant
checkpoint and durable replay/evidence, transaction/storage, coordinator,
linkage, approval/Guardian reconciliation, governance export/delete taxonomy,
reason-code registry/compatibility, model-routing defaults, and health taxonomy
checkpoints are reachable. This branch adds fail-closed attestation
reference-value, endorsement, appraisal-policy, attestation-result lineage, and
verifier-owner authority metadata contracts/examples/tests, trust-aware
model-route linkage, and mock-only attestation-verifier governance/runbook
hardening.
Runtime expansion remains blocked until the remaining gates in this file,
[Baseline](docs/BASELINE.md), and [Next Phase Plan](docs/NEXT_PHASE_PLAN.md)
are resolved.

Superseded missing checkpoint: the previously reported
`phase-1a-cross-contract-invariants` commit
`e71431007ddbe96c3e141b77591efc2508c53e5d` remains absent from this checkout and
from `origin` after fetch. This branch replaces it with a reachable v2
checkpoint. Do not treat `e714310...` itself as integrated or validated.

## What Exists

- Phase 0 architecture, MVP scope, autonomy, security, threat model, supervisor,
  worker, decision, roadmap, validation, policy, and runbook docs.
- Worker deployment blueprint docs for mini PC hardware, network, install
  layout, lifecycle, update/rollback, and field IT preflight.
- Governance policy details for identity/MFA placeholders, approver separation,
  breakglass blocked status, retention/redaction, audit export/customer exit,
  connector consent, worker attestation, and signed update/rollback posture.
- Operator console UX specification docs for Supervisor health, worker fleet,
  approvals, Guardian decisions, evidence, incidents, LIMA IT handoffs,
  deployment/update/attestation, governance, connector readiness, and
  audit/export/delete views.
- Canonical integration inventory in [Baseline](docs/BASELINE.md).
- Phase 1A v2 invariant checkpoint in
  [Cross-Contract Invariants](docs/CROSS_CONTRACT_INVARIANTS.md).
- Versioned v1 contract schemas and sanitized examples in [contracts](contracts).
- `worker.deployment` contract schema and examples for deployment planning
  metadata.
- Governance metadata contract schemas and examples for identity, access
  review, breakglass, audit export, connector consent, and update records.
- Governance metadata contract schemas and examples for RBAC matrix, session
  policy, and device trust posture.
- Console metadata contract schemas and examples for view, alert, and
  action-review records.
- `supervisor.health` contract schema and examples for metadata-only mock
  Supervisor health summaries.
- `approval.binding` contract schema and examples for normalized
  approval-request/result/token/verification/Guardian/task/tool/worker/evidence
  binding.
- `approval.chain` validation-bundle schema and examples for valid one-time,
  replay-denied, scope-mismatch, tenant-mismatch, expired, revoked, tainted,
  denied blocked-MVP, and LIMA IT remediation-blocked chains.
- `guardian.decision` expiry/replay fields for issued/effective/expires,
  max-age, clock-skew allowance, decision nonce, replay policy, scope hash,
  bound tenant/task/worker/action/tool scope, approval binding, token
  verification, and evidence refs.
- `guardian.replay` schema and examples for valid first use, replay denial,
  expiry, scope mismatch, and blocked-MVP outcomes.
- `replay.store.record` schema and examples for consumed, replay-denied, and
  failed-closed nonce/atomicity metadata.
- `transaction.boundary` schema and examples for committed, failed-closed, and
  export-manifest-prepare transaction metadata.
- `transaction.coordinator.event` schema and examples for transaction start,
  replay-nonce-reserved, commit, failed-closed, duplicate-request, and
  reconciliation-completed metadata.
- `evidence.export_manifest` schema and examples for prepared-redacted and
  denied-delete-conflict export metadata.
- `evidence.ledger.entry` schema and examples for pre-action, replay-denial,
  export-manifest, and rollback append-only metadata.
- Durable replay/evidence posture design in
  [docs/DURABLE_REPLAY_EVIDENCE_POSTURE.md](docs/DURABLE_REPLAY_EVIDENCE_POSTURE.md).
- Durable transaction/storage design in
  [docs/rfcs/RFC_DURABLE_TRANSACTION_STORAGE.md](docs/rfcs/RFC_DURABLE_TRANSACTION_STORAGE.md)
  and [docs/architecture/DURABLE_STORAGE_ARCHITECTURE.md](docs/architecture/DURABLE_STORAGE_ARCHITECTURE.md).
- Durable transaction coordinator design in
  [docs/architecture/DURABLE_TRANSACTION_COORDINATOR.md](docs/architecture/DURABLE_TRANSACTION_COORDINATOR.md)
  with reconciliation and failure-drill runbooks in
  [docs/runbooks/transaction-recovery-reconciliation.md](docs/runbooks/transaction-recovery-reconciliation.md)
  and [docs/runbooks/transaction-failure-drills.md](docs/runbooks/transaction-failure-drills.md).
- Cross-contract linkage hardening design in
  [docs/CROSS_CONTRACT_LINKAGE_HARDENING.md](docs/CROSS_CONTRACT_LINKAGE_HARDENING.md)
  with schema-level linkage status fields and fail-closed mismatch modeling.
- Approval/Guardian reconciliation drill design in
  [docs/APPROVAL_GUARDIAN_RECONCILIATION_DRILLS.md](docs/APPROVAL_GUARDIAN_RECONCILIATION_DRILLS.md)
  with deterministic reconciliation statuses and fail-closed drift classes.
- Reconciliation and evidence reason taxonomies in
  [docs/taxonomy/RECONCILIATION_REASON_TAXONOMY.md](docs/taxonomy/RECONCILIATION_REASON_TAXONOMY.md)
  and [docs/taxonomy/EVIDENCE_REASON_TAXONOMY.md](docs/taxonomy/EVIDENCE_REASON_TAXONOMY.md).
- Canonical reason-code registry and compatibility policy in
  [docs/taxonomy/REASON_CODE_REGISTRY.md](docs/taxonomy/REASON_CODE_REGISTRY.md)
  and
  [docs/taxonomy/REASON_CODE_COMPATIBILITY_POLICY.md](docs/taxonomy/REASON_CODE_COMPATIBILITY_POLICY.md).
- `reason.code.registry` and `reason.code.compatibility` schemas/examples for
  versioned reason-code lifecycle and migration metadata.
- Export/delete conflict policy and runbook in
  [docs/governance/EXPORT_DELETE_CONFLICT_POLICY.md](docs/governance/EXPORT_DELETE_CONFLICT_POLICY.md)
  and [docs/runbooks/export-delete-conflict-review.md](docs/runbooks/export-delete-conflict-review.md).
- `governance.export_delete_review` schema and examples for metadata-only
  export/delete review posture.
- Strict contract validation through [scripts/validate-contracts.py](scripts/validate-contracts.py).
- Strict reason-code conformance validation through
  [scripts/check-reason-codes.py](scripts/check-reason-codes.py), including
  mandatory `taxonomy_version` checks for reason-bearing schema/example
  payloads and model-route/health reason arrays.
- Model-route defaults and health taxonomy docs in
  [docs/architecture/MODEL_ROUTING_DEFAULTS.md](docs/architecture/MODEL_ROUTING_DEFAULTS.md),
  [docs/taxonomy/HEALTH_STATUS_TAXONOMY.md](docs/taxonomy/HEALTH_STATUS_TAXONOMY.md),
  [docs/runbooks/model-routing-review.md](docs/runbooks/model-routing-review.md),
  and [docs/runbooks/health-taxonomy-review.md](docs/runbooks/health-taxonomy-review.md).
- Worker-attestation and signed-update trust docs in
  [docs/architecture/WORKER_ATTESTATION_TRUST_ROOT.md](docs/architecture/WORKER_ATTESTATION_TRUST_ROOT.md)
  and
  [docs/architecture/SIGNED_UPDATE_ROLLBACK_TRUST.md](docs/architecture/SIGNED_UPDATE_ROLLBACK_TRUST.md).
- Attestation verifier/reference-value governance docs in
  [docs/architecture/ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md](docs/architecture/ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md)
  and
  [docs/governance/ATTESTATION_REFERENCE_VALUE_GOVERNANCE.md](docs/governance/ATTESTATION_REFERENCE_VALUE_GOVERNANCE.md).
- Worker-attestation and signed-update review runbooks in
  [docs/runbooks/worker-attestation-review.md](docs/runbooks/worker-attestation-review.md)
  and
  [docs/runbooks/signed-update-rollback-review.md](docs/runbooks/signed-update-rollback-review.md).
- Attestation verifier review runbook in
  [docs/runbooks/attestation-verifier-review.md](docs/runbooks/attestation-verifier-review.md).
- `worker.attestation` and `update.rollback` schemas/examples for metadata-only
  trust posture and fail-closed verification/rollback linkage.
- `attestation.reference_value`, `attestation.endorsement`,
  `attestation.appraisal_policy`, and `attestation.result` schemas/examples for
  metadata-only appraisal governance and fail-closed attestation result posture.
- `attestation.result.lineage` and `attestation.authority` schemas/examples for
  durable attestation-result lineage posture, verifier-owner authority posture,
  and revocation propagation metadata.
- Durable lineage/authority docs in
  [docs/architecture/DURABLE_ATTESTATION_RESULT_LINEAGE.md](docs/architecture/DURABLE_ATTESTATION_RESULT_LINEAGE.md),
  [docs/governance/VERIFIER_OWNER_AUTHORITY_POLICY.md](docs/governance/VERIFIER_OWNER_AUTHORITY_POLICY.md),
  and [docs/runbooks/attestation-revocation-propagation.md](docs/runbooks/attestation-revocation-propagation.md).
- Local Markdown link validation through [scripts/check-doc-links.py](scripts/check-doc-links.py).
- Phase 1A mock Python runtime scaffolding in [lima_office](lima_office).
- In-memory worker registry, heartbeat validation, task queue, Guardian policy
  stub, contract loader/validator, and metadata-only evidence writer.
- Cross-contract invariant checks for Guardian decision binding, token
  verification binding, evidence-required completion, worker capability
  routing, taint propagation, LIMA IT remediation blocking, and helper scope
  boundaries.
- Mock-only approval binding verifier that validates binding-shaped payloads,
  compares them to requested action metadata, and tracks one-time nonce
  consumption in memory for tests.
- Mock-only Guardian decision replay verifier that validates decision-shaped
  payloads, compares them to requested action metadata, and tracks one-time
  decision nonce consumption in memory for tests, with nonce consumption
  occurring only after full validation succeeds.
- Mock-only in-memory replay-store helper for reserve/consume/replay-deny/
  fail-closed metadata simulation with no disk persistence.
- Mock-only evidence export-manifest helper for refs-only export metadata
  validation with no export service.
- Mock-only in-memory transaction coordinator helper for transition ordering,
  tenant-scoped idempotency uniqueness checks, and duplicate detection.
- Mock-only in-memory cross-contract linkage validator for metadata-only
  coordinator/boundary/replay/ledger/artifact/manifest chain checks.
- Mock-only in-memory approval/Guardian reconciler for metadata-only linkage
  classification across approval chain, Guardian replay, replay records,
  coordinator events, transaction boundaries, and evidence ledger refs.
- Mock-only in-memory access-matrix evaluator for role/action/session/device
  trust classification with fail-closed outcomes and `can_authorize: false`
  posture.
- Mock-only trust-posture classifier for attestation/update metadata with
  fail-closed blocked states and `can_authorize: false` posture.
- Fail-closed Guardian replay invariants for required requested-action tenant,
  customer context, decision ID, action type (when bound), decision scope hash
  (when bound), approval binding (when bound), token verification (when bound),
  required evidence refs, contradictory timestamp ordering, and bound-scope
  matching.
- Fail-closed replay-store and evidence-export invariants for denial evidence,
  tenant/action/scope consistency, refs-only export posture, tenant-consistent
  evidence chaining, and raw/secret exclusion in MVP.
- Fail-closed cross-contract linkage tests for transaction/replay/evidence drift,
  nonce mismatch, tenant mismatch, export/delete conflict posture, and duplicate
  idempotency-key collision handling.
- Fail-closed approval/Guardian reconciliation-drill tests for missing/stale
  Guardian decisions, approval/token/replay mismatches, coordinator/
  transaction/ledger drift, cross-tenant linkage, blocked-MVP classes, and
  denial-path evidence requirements.
- Approval-binding freshness checks enforced at task enqueue and tool invocation
  invariant paths using reference-time checks for expiry.
- Metadata-only Supervisor health reporter for mock/lab status records.
- Unit tests for contract loading, validation, fail-closed policy, worker state,
  heartbeat, task queue, evidence behavior, cross-contract invariants, and
  Supervisor health reporting.

## What Does Not Exist

- No live connectors, OAuth/provider wiring, webhooks, connector tokens, or
  live customer-system reads/writes.
- No external email, text, chat, form submission, or other external send path.
- No real IT remediation, production server touch, software install/update, or
  endpoint/network control.
- No external model provider API calls.
- No browser automation.
- No durable database, queue, web server, background service, scheduler, or UI.
- No frontend code or operator console implementation.
- No production operations or production-readiness claim.
- No marketing, pricing, sales, TAM, or financial projection content.

## Validation Commands

Run the baseline validation set before merge:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
python scripts/check-doc-links.py
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B -m compileall lima_office scripts tests
git diff --check
git diff --cached --check
git status
```

See [Validation Evidence](docs/VALIDATION_EVIDENCE.md) for the captured result.

## Remaining Blockers

- Approval-token binding now exists as contracts, docs, and mock/in-memory
  tests. Future runtime still needs durable atomic consumption, replay storage,
  and evidence export posture before any side-effecting approval path can
  expand.
- Guardian expiry/replay is now defined and tested for Phase 1A mock/in-memory
  paths. Future runtime still needs a durable Guardian replay store, durable
  atomic decision consumption, idempotency/concurrency handling, and exportable
  replay evidence before any side-effecting path can expand.
- Durable replay/evidence posture design now exists as docs/contracts/tests,
  but actual durable storage, transaction implementation, and export/delete
  services are not implemented.
- RBAC/IdP/MFA/session/device trust matrix now exists as docs/contracts/tests
  and mock-only metadata classification; real IdP/OAuth/OIDC/SAML integration,
  real MFA/session/device posture enforcement, and runtime authorization remain
  blocked.
- Durable transaction/storage RFC and architecture docs now exist as
  docs/contracts/tests, and coordinator design docs/runbooks now exist as
  docs/contracts/tests/mock-hardening. Cross-contract linkage hardening now
  exists as docs/contracts/tests/mock-hardening. Approval/Guardian
  reconciliation drills now exist as docs/contracts/tests/mock-hardening, but
  actual durable coordinator runtime, durable storage implementation, migration
  strategy, and transaction runtime execution are not implemented.
- Promote the initial health reason taxonomy in
  [Health Reason Taxonomy](docs/ux/HEALTH_REASON_TAXONOMY.md) to final runtime
  thresholds and owner/escalation rules.
- Define final storage engine choice, migration posture, retention periods,
  redaction taxonomy, export package format, and customer delete proof posture.
- Finalize reason-code registry migration window and removal governance for
  post-Phase-0 taxonomy major-version transitions.
- Define final legal retention periods and external legal review for
  taxonomy/retention semantics before any live export/delete implementation.
- Select operator IdP/MFA, breakglass, access review cadence, and LIMA IT
  approver separation implementation. Governance scaffolding now defines
  fail-closed metadata, role separation, and blocked breakglass posture, but no
  provider, runtime enforcement, or final cadence is selected.
- Define final worker attestation method, trust root, signed update format,
  and rollback trigger defaults plus final verifier owner/endorsement authority.
  Governance scaffolding now blocks automatic update behavior and automated
  re-enrollment.
- Define final connector consent expiry, live-review criteria, provider scope
  mapping, and prompt-injection test evidence before any live connector review.

## Next Recommended Lane

After attestation-verifier/reference-value hardening is reviewed, the next safe
lane is implementation-gate planning for durable attestation result storage,
endorsement source validation, and update trust-root ownership without adding
live services. Phase 1B lab runtime expansion remains blocked until remaining
gates are approved. Mainline update should wait for explicit approval.
