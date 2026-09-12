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

## ADR-0013: Project Supervisor Inventory And Evidence Into Arc Explicitly

- Status: accepted
- Date: 2026-09-06
- Decision: The first LIMA Office integration panel in Arc reuses the signed
  Supervisor operator channel for explicit worker-inventory refresh and
  redacted evidence lookup. It does not create a second registry, poll in the
  background, or expose execution controls.
- Rationale: The Supervisor remains authoritative for worker classification and
  evidence while Arc remains the bounded worker/operator surface. Explicit
  foreground requests keep network activity visible and auditable.
- Consequence: Results may be cached only in process memory for display. Every
  refresh and evidence read traverses authentication, Guardian, LIMA, and
  evidence gates and fails closed if any layer is unavailable.

## ADR-0014: Serve The Business-Owner Console From The Attended Lab Process

- Status: accepted
- Date: 2026-09-06
- Decision: Serve the first LIMA Office business-owner console at `/office`
  from the existing loopback-only attended lab process. The console consumes a
  redacted projection of existing Supervisor and Arc state and does not create
  a second daemon, scheduler, registry, authority path, or background poller.
- Rationale: A business owner needs a clear LIMA Office surface before live
  model reasoning or business workflows are introduced. Reusing the attended
  process preserves visible lifecycle, same-origin boundaries, and the current
  one-Supervisor architecture.
- Consequence: Codex integration in this slice is readiness detection only.
  Credential contents, live model calls, helper execution, approvals, dispatch,
  and external effects remain disabled until their contracts, Guardian gates,
  evidence path, and failure tests are approved.

## ADR-0015: Permit One Governed Read-Only Supervisor Turn

- Status: accepted
- Date: 2026-09-07
- Decision: Permit the attended `/office` console to send one explicitly
  confirmed public or non-sensitive internal text message through the local
  saved ChatGPT/Codex session. The route must be low risk, read-only, ephemeral,
  and disable user config, rules, web, tools, memory, helpers, fallback, Arc
  dispatch, and every external business side effect.
- Rationale: The business owner needs a usable Supervisor reasoning surface,
  while LIMA—not the model—must remain the control plane and Guardian must remain
  the syscall gate. A one-turn boundary is testable without creating persistent
  memory or execution authority.
- Consequence: Pre-action and Guardian evidence are required before invocation;
  post-action evidence is required before response release. Durable evidence
  stores hashes and posture only, not raw conversation text. Any sensitive
  classification, missing confirmation/restriction/evidence, tool event, auth
  failure, or concurrent turn fails closed. Helpers, approvals, Arc work, live
  connectors, persistent chat, and customer-system changes remain blocked.

## ADR-0016: Start The Office Helper As A Deterministic Synthetic Reviewer

- Status: accepted
- Date: 2026-09-07
- Decision: Implement one foreground `office_operations_helper` that reviews
  only the fixed synthetic registration scenarios already defined by the Arc
  training module. Require a helper scope, assignment, result, explicit operator
  confirmation, Guardian decision, and pre/post evidence for every review.
- Rationale: LIMA Office needs visible helper behavior before granting another
  model or tool boundary. Reusing deterministic fixtures proves delegation,
  evidence, UI, and failure behavior without creating customer-data, memory,
  connector, or worker authority.
- Consequence: The helper can identify synthetic form issues, recommend human
  follow-up, and propose review steps. It cannot accept free-form data, call a
  model, use tools/files/memory, request approval tokens, dispatch Arc, contact a
  connector, submit a form, or create an external side effect. A model-backed or
  customer-data helper requires a separate decision and approval.

## ADR-0017: Make Task Proposals Durable But Tokenless

- Status: accepted
- Date: 2026-09-07
- Decision: Allow the attended Supervisor console to convert only the current
  in-process synthetic helper result into a revisioned local task proposal. The
  owner may edit fixed priority/steps and record propose,
  accept-for-future-approval, deny, or cancel decisions. Each mutation is
  Guardian-gated and the proposal plus completion evidence commits atomically.
- Rationale: The business owner needs a durable reviewable work object before
  any approval-token or Arc-dispatch path exists. Separating proposal acceptance
  from approval makes that authority boundary visible and testable.
- Consequence: `accepted_for_future_approval` never grants authority. The
  contract fixes approval-token, assignment, dispatch, model, tool, connector,
  submission, and external-side-effect flags to safe values. Customer data,
  free-form proposals, approval issuance, and Arc dispatch require later
  contracts, threat review, tests, and explicit approval.

## ADR-0018: Preview Approval Scope Without Creating Approval Authority

- Status: accepted
- Date: 2026-09-07
- Decision: Create a separate durable `supervisor.approval.preview` only from an
  exact `accepted_for_future_approval` proposal revision. The preview may be
  marked reviewed-with-no-authority, denied, or withdrawn, but it must never
  instantiate the existing `approval.request`/`approval.result` contracts or
  create identity, binding, replay, token, worker, dispatch, or external-action
  artifacts.
- Rationale: Sparkbot's durable approval inbox is useful evidence for eventual
  LIMA extraction, but the Office lab does not yet have verified approver
  identity, fresh-intent binding, or a durable single-use token path. A separate
  preview lets the owner inspect scope and safety requirements without allowing
  UI wording or state to become authority.
- Consequence: The preview binds the source proposal revision/hash, has a
  15-minute attended review window, lists prohibited operations, and requires
  explicit Guardian/evidence-backed transitions. The next lane must establish
  verified local operator identity/session binding before it can create even a
  pending real approval request. Approval results, tokens, and Arc dispatch stay
  out of scope.

## ADR-0019: Bind An Attended Lab Session And Stop At Pending Review

- Status: accepted
- Date: 2026-09-08
- Decision: Derive a pseudonymous operator ref from the current OS session plus
  per-binding randomness, keep the 30-minute binding in this localhost process
  only, and allow it to create exactly one durable `approval.request` from an
  unexpired reviewed preview. Guardian must recheck the exact proposal and
  preview hashes and return `requires_approval`; the request remains
  `pending_review` and permits only review of the synthetic preparation plan.
- Rationale: The owner declined a PIN for this personal-PC lab, but creation of
  a real request still needs explicit presence, fresh intent, source binding,
  expiry, policy, and evidence. Lab assurance must not be mislabeled as
  production authentication.
- Consequence: Raw OS usernames, passwords, and PINs are not stored. The session
  does not survive restart and cannot approve. The request has zero uses and no
  external effect. Approval results, tokens, execution bindings, replay
  consumption, worker assignment, Arc dispatch, and live business action remain
  unimplemented and unavailable.

## ADR-0020: Close Synthetic Requests With Non-Authorizing Results

- Status: accepted
- Date: 2026-09-09
- Decision: Permit a durable synthetic `approval.request` in `pending_review`
  to transition only to `denied`, `cancelled`, or `expired`. Deny and cancel
  require explicit attended intent; cancel is limited to the original
  process-bound requester. Expiry is recorded only by an explicit foreground
  action after TTL and never by a hidden timer. Guardian gates every outcome,
  and the request, separate `approval.result`, and completion evidence commit
  atomically after exact request-hash validation.
- Rationale: A real review inbox needs a reliable way to close unwanted or
  stale requests before the riskier positive-approval/token path exists.
  Negative terminal decisions improve operability without granting authority.
- Consequence: These results can never contain approved scope, an approval
  token, execution binding, nonce, replay consumption, token verification,
  worker assignment, Arc dispatch, or external effects. Positive approval is
  deliberately absent until stronger identity, role-separation, and single-use
  authority contracts are approved.

## ADR-0021: Require A Non-Authorizing Readiness Assessment Before Positive Approval

- Status: accepted
- Date: 2026-09-09
- Decision: Add `approval.readiness` as a design-only aggregate over the existing
  identity, RBAC, session, device, approval, token, binding, verification,
  replay, Guardian, and evidence contracts. It records one of three owner
  profiles and the outstanding controls, while fixing every runtime-authority
  flag false.
- Rationale: Sparkbot proves the value of short-lived privileged sessions,
  lockout, one-time consumption, redacted evidence, and execution-time policy
  rechecks. LIMA Office must select how those controls identify a business owner
  and handle a single-owner business before code can safely issue approvals.
- Consequence: On 2026-09-09 the owner selected profile A,
  `attended_os_session_lab_only`, temporarily for whole-system synthetic
  testing. The assessment moves to `blocked_controls_missing`, not ready or
  authorized. No UI approve button, positive result issuer, token service,
  execution binding, replay consumption, worker assignment, or Arc dispatch is
  authorized. Profile B or C still requires its own threat review and explicit
  implementation approval before customer or production use.
