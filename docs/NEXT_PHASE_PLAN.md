# Next Phase Plan

This plan defines safe next lanes after the Phase 0 / Phase 1A closeout. It is
docs and contracts guidance only. It does not approve runtime features, live
connectors, OAuth/provider wiring, external model calls, external sends,
browser automation, real remediation, durable services, production operations,
or customer-system mutation.

## Recommendation

Recommended order:

1. Worker deployment blueprint.
2. Governance policy details.
3. Operator console UX spec.
4. Phase 1B lab runtime expansion only after approval-token runtime record
   binding, Guardian expiry policy, health reason taxonomy, and durable
   evidence/export posture are addressed.
5. Merge strategy / mainline stabilization can run in parallel with the docs
   lanes when it does not hide unresolved gates.

## Option A: Worker Deployment Blueprint

Purpose: define the lab deployment shape for one Supervisor Server and 1-8 Arc
worker mini PCs without installing or running production services.

Status: documented in [Deployment Docs](deployment/README.md). Remaining work
is review, merge, and follow-up policy closure; the blueprint still does not
authorize runtime services or production deployment.

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
enforcement.

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

- Approval-token runtime record binding is defined and tested.
- Non-test Guardian expiry and replay policy is defined.
- Health reason taxonomy is defined.
- Durable evidence/export posture is defined.
- Durable memory retention, delete/export, raw-content, and customer exit
  posture is defined.
- Model-routing defaults are defined for local versus subscription/cloud model
  classes, including data classifications that force local-only handling or
  denial.
- Missing cross-contract invariant checkpoint source is restored, recreated, or
  formally superseded.

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
