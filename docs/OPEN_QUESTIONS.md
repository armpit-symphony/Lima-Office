# Open Questions

Date: May 26, 2026

These blockers remain open after the current Phase 0/1A hardening baseline. None of these items approve runtime expansion.

## Runtime authorization

- What final runtime authorization architecture enforces Guardian + approval + evidence for side-effecting paths?
- What durable atomic consumption model is required for approval tokens and Guardian one-time decisions?
- Which runtime invariants must be enforced synchronously vs asynchronously?

## Durable storage/transactions

- What storage engine and transaction model will back replay/evidence/transaction contracts?
- What idempotency, ordering, and recovery guarantees are mandatory before runtime implementation?
- What backup/restore and corruption recovery runbooks are required before runtime broadening?

## Real connector implementation

- What provider-by-provider readiness evidence and kill-switch criteria are mandatory before any live connector pilot?
- What object/property authorization and prompt-injection controls are mandatory for connector data paths?
- What revocation/disable propagation SLO values replace placeholders?

## Identity/IdP/MFA/session runtime

- Which IdP and MFA/session posture is selected for runtime implementation?
- How will device trust and RBAC/session policies be enforced at runtime boundaries?
- What lifecycle events must force session revocation in implementation?

## Attestation/verifier implementation

- What TPM/secure-boot/verifier stack is selected for real attestation?
- Who is the authority owner for reference values, endorsements, and appraisal policy activation/revocation?
- What runtime revocation propagation guarantees are required before privileged routing?

## Model runtime/provider integration

- Which model roles can ever route to local vs subscription providers after implementation gates?
- What tenant override model is acceptable for model-route policy after implementation?
- What provider safety, audit, and evidence criteria are required before any live model route?

## Export/delete implementation

- What export package format, integrity proof, and access-control model is required for real export implementation?
- What deterministic precedence governs export/delete conflicts in runtime?
- What tenant deletion/reset evidence is mandatory across caches, queues, and durable records?

## Legal/compliance retention/redaction

- What final legal retention durations replace placeholders?
- What redaction profiles become mandatory per contract family and data class?
- What evidence crosswalk is required for NIST CSF/AI RMF governance mapping without certification claims?

## Production deployment

- What production deployment controls are required for Supervisor/worker runtime, secrets, monitoring, and incident handling?
- What SRE minimum runbook set is required (including supervisor outage/failover)?
- What cutover gate criteria must be satisfied before any production claim language is allowed?

## Safety patch cleanup

- `model-routing-health-taxonomy.partial.patch` was archived outside repo with
  documented disposition in `docs/audits/SAFETY_PATCH_DISPOSITION.md`.
- Open follow-up: who owns forensic retention window and eventual archive
  deletion policy for out-of-repo artifacts?

## Phase 1B planning gate

- What is the exact first mock lab runner scope: supervisor+worker+task+replay
  bundle, or a narrower subset?
- Should tag `lima-office-phase-0-1b-planning-baseline` be treated as the
  required independent gate-audit anchor before any tiny implementation slice?
- Should `lima-office-phase-1b-simulator-baseline` be treated as the required
  independent gate-audit anchor before any additional tiny implementation
  slice?
- Should the refreshed integration baseline be tagged/refrozen before any tiny
  Phase 1B implementation proposal?
- Should `main` remain untouched through Phase 1B planning and first tiny slice
  evaluation?
- Worker lifecycle simulator-only slice and task lifecycle simulator-only slice
  are now implemented; what exact acceptance criteria are required before any
  further tiny slice is considered?
- Should the next lane be an independent audit specific to task lifecycle
  simulator scope before any additional runtime planning/implementation?
- Which single additional tiny slice, if any, is eligible next after
  independent gate-audit sign-off on the simulator baseline tag?
- Must durable storage/transaction planning be completed before any Phase 1B
  implementation slice?

## Phase 1C supervised lab orchestration gate

- Evidence lifecycle simulator-only slice is now implemented in-memory; what
  independent audit acceptance threshold is required before any additional
  Phase 1C slice?
- Guardian replay drill simulator-only slice is now implemented in-memory;
  what independent audit acceptance threshold is required before any additional
  Phase 1C slice?
- Which single next simulator slice should be approved next, if any:
  supervisor orchestration simulator or pause/audit-only?
- What is the exact orchestrator metadata boundary so "decision envelope"
  behavior cannot drift into dispatch semantics?
- Are worker/task simulator APIs stable enough for read-only orchestration
  compatibility checks?
- Should monotonic timestamp and idempotency hardening be completed before
  any orchestration simulator slice?
- Evidence lifecycle simulator hardening audit is now `PASS` in
  `docs/audits/EVIDENCE_LIFECYCLE_SIMULATOR_HARDENING_AUDIT.md`; are any
  additional fail-closed constraints required before orchestration-coupling
  planning?
- What mandatory post-implementation audit checklist should apply to every
  future tiny Phase 1C slice?
