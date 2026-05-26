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

- Untracked file `model-routing-health-taxonomy.partial.patch` is intentionally preserved.
- Decide whether to:
  1. Promote it through a reviewed branch and commit, or
  2. Archive/discard with documented traceability.
- Do not silently merge or delete it without explicit instruction.
- Recommended immediate lane: independent audit decision on this artifact before any Phase 1B implementation discussion.

## Phase 1B planning gate

- What is the exact first mock lab runner scope: supervisor+worker+task+replay
  bundle, or a narrower subset?
- What is the final disposition for
  `model-routing-health-taxonomy.partial.patch` before any implementation lane?
- Should the refreshed integration baseline be tagged/refrozen before any tiny
  Phase 1B implementation proposal?
- Should `main` remain untouched through Phase 1B planning and first tiny slice
  evaluation?
- If implementation is later approved, should the first tiny slice be worker
  lifecycle simulator only, or task lifecycle transitions only?
- Must durable storage/transaction planning be completed before any Phase 1B
  implementation slice?
