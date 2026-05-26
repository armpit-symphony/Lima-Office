# Next Phase Plan

This plan is a gate decision document. It does not approve runtime implementation, live connectors, OAuth/provider wiring, durable production services, production authorization, or compliance certification.

Current checkpoint basis:

- Latest hardening checkpoint: `connector-source-of-truth-values-slo-target-finalization` / `a92606a`
- Review branch: `major-baseline-stabilization-next-phase-gate-review`
- Integration refresh status: `integration/phase-0-1b-planning-baseline` frozen at `9fd479c`

## Phase 1B Planning-Only Update (May 26, 2026)

Current recommendation is Phase 1B planning-only, tracked in:

- [PHASE_1B_LAB_RUNTIME_PLAN.md](PHASE_1B_LAB_RUNTIME_PLAN.md)
- [PHASE_1B_IMPLEMENTATION_GATE_CHECKLIST.md](PHASE_1B_IMPLEMENTATION_GATE_CHECKLIST.md)
- [runbooks/phase-1b-lab-runtime-drill.md](runbooks/phase-1b-lab-runtime-drill.md)

This branch does not approve Phase 1B runtime implementation.

Current baseline-freeze step adds annotated tag:
`lima-office-phase-0-1b-planning-baseline`.
Next lane is an independent gate audit on that tag.

Any future tiny implementation slice requires separate explicit approval after:

1. implementation-gate checklist pass,
2. safety patch disposition completion,
3. fresh validation and audit confirmation.

Blocked surfaces remain blocked:

- live connectors
- OAuth/OIDC/SAML/provider wiring and token runtime
- durable storage/service implementation
- real model provider calls and local inference runtime
- real IdP/MFA/session runtime authorization
- real attestation/verifier/signing runtime
- real export/delete runtime
- remediation execution

## Decision Matrix

### Option A: Refresh integration baseline branch

- Purpose: align canonical integration branch with latest docs/contracts/tests/mock-hardening checkpoint.
- Prerequisites: full validation rerun recorded; branch lineage verified; unresolved patch disposition documented.
- Allowed work: branch hygiene, baseline docs/evidence updates, integration refresh planning/merge.
- Blocked work: runtime features, live connectors, OAuth/token runtime, durable runtime services.
- Acceptance gates: branch/commit inventory consistent across `STATUS`, `BASELINE`, `VALIDATION_EVIDENCE`, and stabilization review docs.
- Risk level: low.
- Recommendation: recommended first.

### Option B: Phase 1B lab runtime planning only

- Purpose: define implementation plan boundaries without code execution expansion.
- Prerequisites: Option A complete; independent audit completed or explicitly waived by leadership.
- Allowed work: planning docs, contracts gap analysis, runbook prerequisites, risk reviews.
- Blocked work: implementation code that enables side effects or live integration.
- Acceptance gates: explicit implementation blockers remain listed and unchanged.
- Risk level: low to medium.
- Recommendation: recommended second (planning-only).

### Option C: Phase 1B narrow runtime implementation

- Purpose: start minimal runtime implementation only after formal gate approval.
- Prerequisites: Option A and B complete, plus explicit gate approval, clear scope, and acceptance tests.
- Allowed work: tightly scoped, approved runtime increments.
- Blocked work: broad authorization expansion, live connectors, provider integrations without dedicated approvals.
- Acceptance gates: durable replay/transaction/evidence and runtime auth boundaries approved first.
- Risk level: high.
- Recommendation: not recommended at this stage.

### Option D: Storage/transaction implementation planning

- Purpose: select implementation-time storage/transaction architecture without enabling runtime services.
- Prerequisites: Option A complete; durability and recovery requirements documented.
- Allowed work: architecture RFC refinement, migration strategy planning, failure-mode drills (docs).
- Blocked work: database/service deployment, migrations, production durability claims.
- Acceptance gates: unresolved atomicity/idempotency/recovery questions reduced with concrete design choices.
- Risk level: medium.
- Recommendation: optional after Option A; keep planning-only.

### Option E: Live connector implementation planning

- Purpose: map prerequisites for future connector execution, not implementation.
- Prerequisites: Option A complete; legal/compliance and connector risk/ownership gates reviewed.
- Allowed work: provider-by-provider gate checklist, evidence requirements, threat updates.
- Blocked work: OAuth/OIDC/SAML wiring, token runtime, API calls, browser automation, external sends.
- Acceptance gates: explicit no-live-connector stance preserved; blocked categories remain blocked.
- Risk level: high.
- Recommendation: defer until after audit and runtime planning gates.

### Option F: Independent audit / pause

- Purpose: obtain external or separate-team validation of baseline integrity and gate posture.
- Prerequisites: Option A complete or included in audit scope.
- Allowed work: audit checklist execution, evidence review, corrective docs-only updates.
- Blocked work: runtime expansion during audit window.
- Acceptance gates: audit findings triaged with documented disposition.
- Risk level: low.
- Recommendation: recommended in sequence before any implementation lane.

## Conservative Recommendation

Recommended sequence:

1. Option F (independent audit / pause).
2. Option B (Phase 1B lab runtime planning only).
3. Option D (storage/transaction implementation planning only), if audit findings permit.
4. Consider a tiny implementation slice only after explicit gate approval.

Explicit non-recommendations for this gate:

- Do not begin live connectors.
- Do not begin production storage/runtime services.
- Do not begin real IdP/OAuth/MFA/runtime authorization implementation.
- Do not begin real TPM/verifier/signing/update runtime implementation.
