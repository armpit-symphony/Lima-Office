# Next Phase Plan

This plan defines safe next lanes after the Phase 0 / Phase 1A closeout. It is
docs and contracts guidance only. It does not approve runtime features, live
connectors, OAuth/provider wiring, external model calls, external sends,
browser automation, real remediation, durable services, production operations,
or customer-system mutation.

Current canonical integration branch: `integration/phase-0-1a-baseline`. See
[Baseline](BASELINE.md) for the included reachable branches and the missing
cross-contract invariant checkpoint. The reachable replacement is
`phase-1a-invariant-checkpoint-v2`; see
[Cross-Contract Invariants](CROSS_CONTRACT_INVARIANTS.md).

## Recommendation

Recommended order:

1. Governance/export/delete conflict policy finalization and reconciliation
   evidence taxonomy hardening (checkpoint completed as docs/contracts/tests
   hardening on `governance-export-delete-taxonomy-finalization`).
2. Reason-code registry compatibility policy and canonical lifecycle hardening
   (checkpoint completed as docs/contracts/tests hardening on
   `reason-code-registry-compatibility-policy`).
3. Reason-code conformance CI gate and fail-closed taxonomy drift checks
   (checkpoint completed as validation/tooling/tests hardening on
   `reason-code-conformance-ci-gate`).
4. Taxonomy-version enforcement hardening for all reason-bearing contracts and
   examples (checkpoint completed as validation/schema/docs/tests hardening on
   `taxonomy-version-enforcement-hardening`).
5. Final RBAC/IdP/MFA/session/device trust matrix (checkpoint completed as
   docs/contracts/tests/mock-hardening on
   `rbac-idp-mfa-session-device-trust-matrix`).
6. Model-routing defaults and health taxonomy refinement (checkpoint completed
   as docs/contracts/tests/mock metadata hardening on
   `model-routing-defaults-health-taxonomy-refinement`).
7. Worker attestation trust-root and signed update/rollback hardening
   (checkpoint completed as docs/contracts/tests/mock metadata hardening on
   `worker-attestation-trust-root-signed-update-rollback-hardening`).
8. Attestation verifier policy/reference-value governance design (checkpoint
   completed as docs/contracts/tests/mock metadata hardening on
   `attestation-verifier-policy-reference-values-design`).
9. Durable attestation lineage/authority design (checkpoint completed as
   docs/contracts/tests/mock metadata hardening on
   `durable-attestation-lineage-authority-design`).
10. Attestation revocation reconciliation drills (checkpoint completed as
    docs/contracts/tests/mock metadata hardening on
    `attestation-revocation-reconciliation-drills`).
11. Live connector criteria design (checkpoint completed as
    docs/contracts/tests/mock metadata hardening on
    `live-connector-criteria-design`).
12. Connector provider risk-profile and revocation/disable drill hardening
    (checkpoint completed as docs/contracts/tests/mock metadata hardening on
    `connector-provider-risk-profile-revocation-disable-drills`).
13. Connector trust-boundary linkage invariants and reconciliation posture
    (checkpoint completed as docs/contracts/tests/mock metadata hardening on
    `connector-trust-boundary-linkage-invariants`).
14. Phase 1B lab runtime expansion only after the gates above are approved.

Next recommended lane after this checkpoint: connector provider acceptance
scoring and revocation-propagation cadence formalization (docs/contracts/tests
only), while keeping live connector wiring/execution, OAuth/token runtime,
browser automation, and runtime authorization expansion blocked.

After the connector trust-boundary checkpoint, the next lane is connector
provider acceptance scoring and revocation-propagation cadence formalization
(docs/contracts/tests only), with no live connector runtime behavior.

Alternative non-runtime lanes can proceed when they do not obscure the blockers:
model-routing defaults, final IdP/MFA/RBAC matrix, health taxonomy refinement,
and worker attestation/update trust-root details.

Approval-token runtime binding design is now represented in
[Approval Token Runtime Binding](APPROVAL_TOKEN_RUNTIME_BINDING.md) with
`approval.binding` and `approval.chain` contracts plus mock/in-memory tests.
Future side-effecting runtime still needs durable atomic token consumption and
replay evidence before expansion.

Guardian expiry/replay policy is now represented in
[Guardian Expiry And Replay Policy](GUARDIAN_EXPIRY_REPLAY_POLICY.md) with
`guardian.decision` expiry/replay fields, `guardian.replay` metadata, and
mock/in-memory tests. Future side-effecting runtime still needs durable atomic
decision consumption, replay storage, idempotency/concurrency rules, and
exportable replay evidence before expansion.

Durable replay/evidence posture design is now represented in
[Durable Replay And Evidence Posture](DURABLE_REPLAY_EVIDENCE_POSTURE.md) with
`replay.store.record` and `evidence.export_manifest` contracts plus mock-only
tests. Actual durable storage, transactionality, and export/delete services
remain blocked.

Durable transaction/storage RFC posture is now represented in
[RFC_DURABLE_TRANSACTION_STORAGE](rfcs/RFC_DURABLE_TRANSACTION_STORAGE.md) and
[DURABLE_STORAGE_ARCHITECTURE](architecture/DURABLE_STORAGE_ARCHITECTURE.md)
with `transaction.boundary` and `evidence.ledger.entry` contracts plus
mock-only tests. Storage engine choice, migrations, and transaction runtime
implementation remain blocked.

Durable transaction coordinator posture is now represented in
[DURABLE_TRANSACTION_COORDINATOR](architecture/DURABLE_TRANSACTION_COORDINATOR.md)
with `transaction.coordinator.event` contracts/examples, a mock in-memory
transition validator, and reconciliation/failure-drill runbooks. Durable
coordinator runtime, storage integration, and production transaction execution
remain blocked.

Cross-contract linkage hardening posture is now represented in
[CROSS_CONTRACT_LINKAGE_HARDENING](CROSS_CONTRACT_LINKAGE_HARDENING.md) with
explicit linkage status/reason fields across coordinator/boundary/replay/
ledger/artifact/manifest contracts, a mock in-memory linkage validator, and
negative-path drift/tenant/nonce/export-conflict tests. Durable storage and
runtime transaction execution remain blocked.

Approval/Guardian reconciliation drills are now represented in
[APPROVAL_GUARDIAN_RECONCILIATION_DRILLS](APPROVAL_GUARDIAN_RECONCILIATION_DRILLS.md)
with stricter reconciliation conditionals across approval/Guardian/replay/
transaction/ledger contracts, a mock in-memory reconciler, and fail-closed
negative-path drill tests. Durable transaction/runtime implementation remains
blocked.

Attestation revocation reconciliation drills are now represented in
[ATTESTATION_REVOCATION_RECONCILIATION_DRILLS](ATTESTATION_REVOCATION_RECONCILIATION_DRILLS.md)
with `attestation.reconciliation` metadata contracts/examples, fail-closed
drift classes spanning lineage/authority/reference/endorsement/appraisal/
result/route/transaction/ledger records, and a mock-only reconciliation helper.
Durable storage and runtime trust-authorization remain blocked.

## Option A: Worker Deployment Blueprint

Purpose: define the lab deployment shape for one Supervisor Server and 1-8 Arc
worker mini PCs without installing or running production services.

Status: documented in [Deployment Docs](deployment/README.md). Remaining work
is review and follow-up policy closure inside the canonical baseline; the
blueprint still does not authorize runtime services or production deployment.

Prerequisites:

- Current Phase 0 docs, contracts, policies, and runbooks remain authoritative.
- Worker identity, heartbeat, quarantine, revoke, evidence, update, and rollback
  requirements are linked to existing contracts.
- No assumption of live connectors or real remediation.

Allowed work:

- Deployment topology diagrams.
- Hardware and OS assumptions.
- Network trust-boundary notes.
- Worker enrollment and re-enrollment flow.
- Heartbeat thresholds and health reason codes.
- Emergency evidence spool, disk-full, and evidence-location posture.
- Health-check and rollback requirements.
- Evidence to capture during lab setup.
- Runbook additions or checklists.

Blocked work:

- Installing or updating software on real endpoints.
- Running worker daemons or background services.
- Touching production servers.
- Adding endpoint control, remediation, or live connector behavior.
- Adding databases, queues, web servers, or UI frameworks.

Acceptance gates:

- Blueprint stays inside one Supervisor Server and 1-8 Arc workers.
- Every worker action path routes through Guardian and evidence.
- Quarantine, revoke, rollback, and re-enrollment are visible and documented.
- No production-readiness claim appears.

Recommended order: first.

## Option B: Governance Policy Details

Purpose: close the policy blockers that currently prevent runtime expansion.

Status: documented in [Governance Docs](governance/README.md). The lane adds
fail-closed policy scaffolding and metadata contracts for identity/MFA
placeholders, access review, approver separation, breakglass denial, retention
and redaction, audit export/customer exit, connector consent/revocation, worker
attestation, and signed update/rollback. It does not select providers, final
legal retention periods, signing roots, attestation mechanisms, or runtime
enforcement. It is included in the canonical integration baseline.

Prerequisites:

- Approval-token lifecycle, evidence writer failure, prompt-injection handling,
  worker quarantine, retention/redaction, and LIMA IT handoff policies remain
  the starting point.
- Policy changes must preserve Guardian as the syscall gate.

Allowed work:

- Operator IdP/MFA assumptions.
- Breakglass policy and blocked actions during breakglass.
- Access review cadence.
- LIMA IT approver separation.
- Retention defaults.
- Redaction taxonomy.
- Audit export manifest.
- Customer exit/delete/reset process.
- Durable evidence/export posture.

Blocked work:

- Implementing identity providers.
- Wiring secrets, OAuth, live connector scopes, or model provider accounts.
- Granting remediation, production server, or regulated-system execution.
- Claiming certification or production compliance.

Acceptance gates:

- Policies define concrete approvals, evidence, failure behavior, and done
  criteria.
- Sensitive HR, finance, legal, medical, and secret data remain approval-gated
  or blocked.
- LIMA IT remediation approval separation is explicit.
- Customer exit/delete and audit export posture are documented.

Recommended order: second.

## Option C: Operator Console UX Spec

Purpose: define what an operator must see and approve before any UI is built.

Status: documented in [UX / Control-Room Docs](ux/README.md). This lane defines
operator console information architecture, workflows, permission model, approval
inbox, evidence viewer, worker fleet, LIMA IT panel, and health reason taxonomy
as specs only. It does not add UI code, a web server, frontend framework, or
runtime control plane. It is included in the canonical integration baseline.

Prerequisites:

- Supervisor health fields and reason taxonomy have a draft.
- Approval, evidence, quarantine, worker state, and LIMA IT handoff states are
  mapped to contracts.
- Governance identity, access review, breakglass denial, audit export/delete,
  connector revocation, attestation failure, and update/rollback states are
  mapped to contracts and runbooks.
- The spec is framed as UX requirements only.

Allowed work:

- Information architecture.
- Wire-level status inventory.
- Approval review screen requirements.
- Evidence view requirements.
- Worker health and quarantine view requirements.
- Runbook handoff requirements.
- Error and fail-closed state copy.

Blocked work:

- Adding a UI framework or web server.
- Adding live controls that mutate customer systems.
- Hiding background work.
- Displaying a mock state as if a real customer action occurred.

Acceptance gates:

- Every command view names the Guardian decision and evidence record required.
- High-risk actions show approval and denial states.
- Worker quarantine/revoke controls are visible as spec-only flows.
- The UX does not imply production operation or live connector readiness.

Recommended order: third.

## Option D: Phase 1B Lab Runtime Expansion

Purpose: expand the mock lab runtime only after the remaining safety gates are
resolved and approved.

Prerequisites:

- Approval-token runtime record binding is defined and tested for mock/in-memory
  Phase 1A flows; durable atomic consumption and replay evidence posture are
  explicitly deferred.
- Guardian expiry/replay policy is defined and tested for mock/in-memory
  Phase 1A flows; durable replay storage and atomic decision consumption are
  explicitly deferred.
- Durable replay/evidence posture schemas and tests exist, but durable storage,
  atomic transaction implementation, and export/delete implementation are
  explicitly deferred.
- Durable transaction-boundary and evidence-ledger contracts exist, but
  implementation-time coordinator logic, migration strategy, and storage-engine
  selection are explicitly deferred.
- Durable coordinator event contracts and runbooks exist, but runtime service
  implementation, durable persistence, and operational automation are
  explicitly deferred.
- Cross-contract linkage hardening contracts/tests exist, but durable
  referential integrity enforcement, storage-layer transactions, and recovery
  tooling implementation are explicitly deferred.
- Approval/Guardian reconciliation drill contracts/tests exist, but durable
  reconciliation services, durable replay/transaction storage, and operator
  automation remain explicitly deferred.
- Attestation result lineage and verifier-owner authority contracts/runbook
  exist, but durable attestation storage, authority service integration,
  revocation automation, and quarantine-clearance automation are explicitly
  deferred.
- Health reason taxonomy is defined.
- Durable evidence/export posture is defined.
- Durable memory retention, delete/export, raw-content, and customer exit
  posture is defined.
- Model-routing defaults are defined for local versus subscription/cloud model
  classes, including data classifications that force local-only handling or
  denial.
- Cross-contract invariant checkpoint source is restored, rebuilt, replaced, or
  formally superseded. The reachable v2 branch provides the current replacement
  candidate.

Allowed work after prerequisites:

- Small, synchronous lab-only runtime additions.
- Contract-backed state transitions.
- Additional tests for fail-closed behavior.
- Mock-only health summaries.
- Mock-only evidence/export records when durable posture has been approved.

Blocked work:

- Live connectors.
- OAuth/provider wiring.
- External model API calls.
- External sends.
- Browser automation.
- Real remediation.
- Production system access.
- Durable database, queue, web server, scheduler, or production service unless a
  separate approved runtime plan explicitly authorizes it.

Acceptance gates:

- All new behavior has a contract, policy ref, Guardian decision, evidence path,
  failure behavior, and tests.
- Approval-required paths cannot proceed on missing, expired, reused, revoked,
  mismatched, ambiguous, or wrong-scope approval tokens.
- Evidence failure blocks pre-action privileged work.
- Runtime remains lab-only and mock-only.

Recommended order: fourth, only after the named gates are closed.

## Option E: Merge Strategy / Mainline Stabilization

Purpose: choose the safest way to bring completed Phase 0 and Phase 1A branches
back to mainline without losing evidence or hiding blockers.

Status: active in [Baseline](BASELINE.md) on
`integration/phase-0-1a-baseline`. Do not update `main` without explicit
approval.

Prerequisites:

- Branch order and expected commits are listed.
- Missing `phase-1a-cross-contract-invariants` source is resolved or explicitly
  marked as superseded.
- Validation commands pass on the stabilization branch.

Allowed work:

- Merge order notes.
- Mainline stabilization checklist.
- Branch/commit inventory.
- CI validation and whitespace checks.
- Documentation index updates.

Blocked work:

- Squashing away required validation history without an archive note.
- Merging runtime expansion under a docs-only closeout.
- Treating unavailable branch evidence as validated.
- Adding production claims during merge cleanup.

Acceptance gates:

- `STATUS.md`, closeout docs, and validation evidence identify the baseline.
- All links and validation commands pass.
- Remaining blockers are still visible after merge.
- Mainline does not imply live connector or production readiness.

Recommended order: parallel with A/B when needed for repository hygiene.
