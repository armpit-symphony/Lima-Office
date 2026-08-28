# Decisions

This is an ADR-style decision log. Status values are `accepted`, `proposed`, or `revisit`.

## ADR-0001: Start With 1 Supervisor And 1-8 Workers

- Status: accepted
- Decision: LIMA Office OS starts with 1 Supervisor Server and a design range of 1-8 Arc worker mini PCs for one small business tenant.
- Rationale: This keeps the first deployment understandable, observable, and supportable.
- Consequence: Multi-tenant SaaS and enterprise-scale management are out of Phase 0.

## ADR-0002: Contracts First

- Status: accepted
- Decision: Architecture, security, threat model, contracts, and runbooks come before runtime implementation.
- Rationale: The system coordinates privileged office work and needs governance before execution.
- Consequence: Code paths for live actions remain blocked until contracts are approved.

## ADR-0003: Guardian As Mandatory Syscall Gate

- Status: accepted
- Decision: Guardian gates every model call, tool call, network action, file mutation, outbound message, connector action, scheduled action, and privileged operation.
- Rationale: A governed control plane needs one required policy and evidence boundary.
- Consequence: No worker, helper agent, model provider, or connector can bypass Guardian.

## ADR-0004: Lab Mode Before Production

- Status: accepted
- Decision: The first target is lab mode with 1 Supervisor Server and 1-3 workers before any pilot posture.
- Rationale: Lab mode lets the team validate contracts and failure modes without customer-system risk.
- Consequence: Production-readiness claims remain out of scope.

## ADR-0005: Mock Connectors Before Live Connectors

- Status: accepted
- Decision: Connector work starts as mock/readiness state only.
- Rationale: Live connectors require consent, scope review, secret handling, prompt-injection controls, audit, and revocation.
- Consequence: No OAuth, tokens, webhooks, live reads, or writes in Phase 0.

## ADR-0006: Approval Required For Privileged Actions

- Status: accepted
- Decision: Privileged or high-risk actions require human approval.
- Rationale: External sends, file mutation, customer record changes, software updates, remediation, and regulated systems carry business risk.
- Consequence: Approval records must include approver identity, scope, expiration, replay protection, Guardian decision, and evidence.

## ADR-0007: Tenant Isolation From Day One

- Status: accepted
- Decision: Tenant/customer isolation is designed even while the first target is one tenant at a time.
- Rationale: Evidence, memory, connectors, approvals, and worker assignments must not leak between customers.
- Consequence: Contracts must include tenant IDs and customer exit/delete posture.

## ADR-0008: Marketing And Financial Claims Out Of Phase 0

- Status: accepted
- Decision: Marketing, pricing, financial projections, TAM, investor content, sales copy, and production claims are out of Phase 0 unless explicitly requested.
- Rationale: The repo is an engineering baseline.
- Consequence: README and docs use architecture/status language.

## ADR-0009: Arc Owns Operator Queue Selection

- Status: accepted
- Decision: The physical test IDE consumes an Arc-owned adapter over Arc's
  existing task queue, approval store, and task selector. LIMA Office supplies
  governed outcome, SOP-resolution, escalation, and evidence state through a
  narrow consumer port.
- Rationale: Queue ordering and resume safety are shell behavior. Keeping them
  in Arc prevents a browser or Office convenience layer from becoming a second
  scheduler.
- Consequence: Human approvals and instructed SOP gaps may mark a blocked task
  ready for Arc selection, but neither signal is execution authority. Every
  governed read still requires a fresh Supervisor decision and Arc grant.

## ADR-0010: Exclude Sparkbot From The Arc + LIMA Office Lab Preview

- Status: accepted
- Date: 2026-08-27
- Decision: The first Arc + LIMA Office Lab Preview will not depend on, embed,
  package, or release-gate on Sparkbot. LIMA Office owns the Supervisor
  experience and Arc owns bounded worker execution for this lane.
- Rationale: The current LIMA Office and Arc stack already owns the task UI,
  queue lifecycle, grants, evidence, and Windows worker lifecycle needed for a
  bounded lab preview. Coupling Sparkbot into the preview would add another
  application lifecycle without resolving a required preview capability.
- Consequence: Sparkbot remains historical or research reference only. No
  Sparkbot code, UI, CI job, package, or runtime service is required to complete
  the preview. Reintroducing Sparkbot requires a future contract and explicit
  architecture decision.

## ADR-0011: Freeze The First Preview To Governed Document Listing And Reading

- Status: accepted
- Date: 2026-08-27
- Decision: The first preview is limited to the current localhost
  Training/Working experience and Guardian-governed document-list and
  document-read operations using explicit grants and separate execution
  opt-ins.
- Rationale: This is the smallest end-to-end slice that proves Supervisor
  admission, Arc dispatch, Guardian enforcement, evidence capture, restart
  behavior, and Windows operation without introducing customer-impacting side
  effects.
- Consequence: Live models, connectors, outbound sends, file mutation, LAN
  exposure, remediation, and customer data remain outside the preview. Adding
  an excluded capability requires its own contract, threat review, tests, and
  explicit approval. The preview must fail closed when grants or execution
  opt-ins are absent, expired, malformed, or replayed.

## ADR-0012: Use One LIMA Runtime Commit Across Office And Arc

- Status: accepted
- Date: 2026-08-27
- Decision: The Lab Preview selects LIMA Runtime commit
  4a599405961e786808ea7a7da71ecc65f7358e4f for both LIMA Office and Arc.
  Guardian remains pinned to 69e843218c521b913edcec404dea6b7be8c64f06.
- Rationale: A downloadable governed stack must have one runtime identity.
  Separate Office and Arc LIMA pins made installation evidence ambiguous and
  allowed each repository to pass against a different runtime.
- Consequence: Arc's frozen-pin compatibility proof moves deliberately to the
  coordinated preview commit. Every consumer keeps its own isolated
  environment and must prove the installed package provenance before tests.
