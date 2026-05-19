# Schema Hardening Notes

These notes explain the Phase 0 schema conditionals added before any Phase 1A runtime scaffolding. They are docs/schema scaffolding only.

## Why Conditionals Exist

Enums describe allowed values, but they do not stop contradictory records. The v1 schemas now use draft 2020-12 `allOf`, `if`, `then`, `not`, and enum narrowing to make unsafe combinations invalid at the contract boundary.

Conditionals are used where a single field changes the safety meaning of other fields:

- Approval request/result/token lifecycle.
- Token verification result.
- Guardian allow, deny, approval-required, blocked-MVP, and quarantine decisions.
- Task/tool terminal states.
- Evidence-required paths and evidence writer failure.
- Taint propagation.
- Worker quarantine, revoke, and re-enrollment.
- LIMA IT diagnostic versus remediation request boundaries.
- Model route cloud/egress denial.

## Unsafe States Blocked By Schema

- Approved approval outcome without approver, decision time, scoped token linkage, and evidence.
- Denied or blocked-MVP approval outcome with an approval token.
- Used, expired, or revoked approval token with contradictory lifecycle fields.
- Valid token verification when scope does not match or observed status is not active.
- Guardian denial or blocked-MVP decision with an approval token.
- Privileged tool completion with denied policy, missing token verification, or unresolved taint.
- Evidence-required task completion when pre-action evidence failed.
- Healthy worker state when evidence writer failed or identity verification failed.
- LIMA IT remediation represented as executable authorization in Phase 0.
- Cloud model route when egress/cloud routing is blocked.
- Secret evidence exported without secret redaction.

## Schema Policy Versus Runtime Policy

Schemas can require metadata shape, cross-field consistency, and fail-closed records. They cannot prove real identity, time, token cryptography, approval authority, evidence storage, redaction quality, or tenant isolation by themselves.

Runtime policy must still verify:

- Operator identity, role, and MFA.
- Approval freshness and separation of duties.
- Token expiry, revocation, replay, binding, and atomic consumption.
- Evidence ledger write durability and integrity.
- Prompt-injection detection and taint clearance.
- Worker identity, channel identity, capability lease, and attestation.
- Connector consent, scope, revocation, and secret storage.
- Retention, redaction, export, and customer exit/delete behavior.

If runtime policy is missing or ambiguous, the future runtime must fail closed.

## Phase 1A Test Expectations

Before Phase 1A runtime scaffolding accepts these contracts, add contract tests for:

- Valid and invalid approval request/result/token state transitions.
- Valid, expired, revoked, missing, mismatched, ambiguous, and wrong-scope token verification.
- Guardian denied, blocked-MVP, approval-required, quarantine, and allow-with-evidence decisions.
- Tainted input denial for tool invocation, memory write, external send, approval scope, and LIMA IT remediation.
- Evidence failure pre-action block and post-action degraded reconciliation.
- Worker quarantine, revoke, release request, and re-enrollment records.
- LIMA IT read-only diagnostic handoff and remediation-denied-MVP handoff.
- Model route cloud/egress denial and secret-material denial.

Phase 1A should use a JSON Schema draft 2020-12 validator in CI before runtime consumers rely on these contracts.
