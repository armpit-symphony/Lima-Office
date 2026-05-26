# Runtime Boundaries

This document defines what the current Phase 1A runtime scaffolding is allowed
to represent and what remains blocked.

## Phase 1A Runtime State

Phase 1A runtime is mock/in-memory only.
Approved Phase 1B narrow addition is also mock/in-memory only:
worker lifecycle simulator metadata transitions.

It contains contract loading, contract validation, a default-deny Guardian
policy stub, in-memory worker registry, heartbeat validation, in-memory task
queue, cross-contract invariant checks, metadata-only Supervisor health
reporting, and metadata-only in-memory evidence writer.
This branch also includes a mock-only Guardian decision replay verifier that
validates expiry, replay nonce, scope, clock-skew, approval binding, token
verification, and evidence refs in memory for tests.

It does not contain live dispatch, live tool execution, durable persistence,
external services, production operations, or customer-system mutation.

## Explicit Blocks

- No live connectors.
- No OAuth/provider wiring.
- No connector tokens, webhooks, live reads, or live writes.
- No external email, text, chat, form submission, or customer-system send.
- No real IT remediation.
- No production server touch.
- No software install/update execution.
- No durable database, queue, web server, scheduler, daemon, or UI.
- No browser automation.
- No external model provider calls.
- No unrestricted browser, file, network, shell, connector, or tool access.
- No cross-tenant memory sharing.
- No hidden background actions.

The worker lifecycle simulator does not add any exception to these blocks.

## Safe Runtime Uses

The current runtime can safely be used for:

- Loading local contract schemas.
- Validating sanitized local contract examples and mock payloads.
- Exercising fail-closed behavior in tests.
- Representing one tenant and up to eight mock Arc workers in memory.
- Recording mock worker registration and state transitions.
- Validating heartbeat shape, tenant match, staleness, Guardian reachability,
  and evidence-writer posture.
- Representing task assignment only after a validated mock Guardian decision.
- Blocking task assignment for quarantined, revoked, offline, wrong-tenant, or
  unregistered workers.
- Creating metadata-only, in-memory evidence refs for tests.
- Simulating evidence writer failure so privileged paths can fail closed.
- Checking cross-contract invariants in memory so valid schemas cannot be
  combined into unsafe task, token, tool, memory, helper, worker, evidence, or
  LIMA IT flows.
- Building `supervisor.health` mock reports for tests and operator-facing
  planning.
- Checking Guardian decision expiry/replay invariants in memory so one-time
  decisions can pass once in tests and stale, replayed, mismatched, or
  blocked-MVP decisions fail closed.

## Future Approval Required

Future approval is required before:

- Any live connector review, OAuth/provider wiring, token storage, webhook, live
  read, live write, or connector-side effect.
- Any external model provider call or model account integration.
- Any external message, form submission, or customer-system mutation.
- Any file delete/overwrite beyond mock records.
- Any remediation, software install/update, endpoint control, network change, or
  production server touch.
- Any durable database, queue, service, scheduler, UI, or operator console
  implementation.
- Any worker daemon or background loop.
- Any customer data persistence, audit export, customer exit/delete, or evidence
  retention implementation.

Before those approvals, the relevant contract, Guardian policy, approval state,
evidence path, failure behavior, runbook, and tests must exist and pass.

## Expansion Gates

Do not expand runtime behavior until these gates are closed:

- Durable approval-token consumption, replay evidence/export posture, and
  concurrency behavior beyond the mock/in-memory verifier.
- Durable Guardian replay store, durable atomic decision consumption,
  idempotency/concurrency behavior, and final non-test clock-skew thresholds.
- Final Supervisor health reason thresholds, owner/escalation rules, and
  operations posture.
- Durable evidence/export posture.
- Durable memory retention, delete/export, raw-content handling, and customer
  exit posture.
- Model-routing defaults for local versus subscription/cloud provider classes,
  including data classifications that force local-only handling or denial.
- Operator IdP/MFA and access-review posture.
- Worker attestation and update rollback posture.
- Connector consent, scope review, and revocation posture.
