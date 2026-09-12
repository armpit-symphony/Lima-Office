# Runtime Boundaries

This document defines what the current Phase 1A runtime scaffolding is allowed
to represent and what remains blocked.
## Approved physical-PC test exception (2026-08-20)

The operator explicitly approved one later bounded lab exception to the Phase
1A no-service/no-UI baseline: `scripts/arc-runtime-harness.py` may run one real
Arc worker and one real Supervisor behind a loopback-only Training/Working UI.

The exception is limited to the already-proven `document_read` grant path,
server-side SOP-gap persistence, task-outcome routing, training counters, and
sanitized harness evidence. Training is the default. Working mode requires the
Supervisor opt-in, Arc opt-in, and a document root at startup.

This exception does not approve production hosting, LAN access, connectors,
external sends, file mutation, model calls except the separately bounded
read-only Supervisor turn below, remediation, unrestricted network access,
device/robotics control, hidden jobs, or any other runtime expansion.
The detailed boundary and runbook are in
[`ARC_RUNTIME_HARNESS.md`](ARC_RUNTIME_HARNESS.md).

## Approved attended Supervisor model exception (2026-09-07)

The business-owner console at `/office` may perform one explicit foreground
Supervisor reasoning turn through the saved local ChatGPT/Codex sign-in. The
owner must confirm each turn and classify it as public or non-sensitive
internal text. The route is low risk, read-only, ephemeral, and has shell,
files, web search, MCP/tools, memory, helper agents, fallback, Arc dispatch,
external sends, and customer-record mutation disabled.

Guardian and pre-action evidence must pass before invocation. Post-action
evidence must pass before the response is released. Durable evidence stores
hashes, lengths, IDs, classifications, and policy posture only; raw prompt and
response text remain transient in the browser/process. Any tool event or missing
restriction fails closed. This exception is not approval for persistent chat,
sensitive data, autonomous work, production hosting, or general provider use.

## Approved synthetic Office Operations Helper exception (2026-09-07)

The `/office` console may run one explicit deterministic review over an existing
fixed synthetic registration scenario. The helper remains Supervisor-side and
must use `helper.scope`, `helper.assignment`, `helper.result`, Guardian, and
pre/post evidence. It may identify missing/invalid fields, recommend human
follow-up, and propose non-executing task steps.

The helper cannot accept free-form/customer data, invoke a model, use tools,
read files or memory, request approval tokens, contact connectors, dispatch Arc,
submit forms, or cause any external side effect. Missing confirmation, unknown
scenario, Guardian denial, evidence failure, or contract failure withholds the
result. Only fixed scenario IDs and derived synthetic review metadata enter the
evidence store.

## Approved tokenless Supervisor task-proposal exception (2026-09-07)

After a successful in-process synthetic helper review, the `/office` console may
create one durable structured task proposal. The owner may edit only `low` or
`normal` priority and a non-empty subset of three fixed task-step identifiers,
then propose, accept for future approval, deny, or cancel it. Every mutation is
explicit, Guardian-gated, revision-checked, and evidenced. Proposal state and
its completion evidence are committed atomically in the local harness SQLite
store.

`accepted_for_future_approval` is not approval. Every proposal records that no
approval token was issued, no worker was assigned, Arc dispatch is disallowed
and did not occur, and no model, tool, connector, submission, or external side
effect ran. Free-form and customer data are not accepted.

## Approved tokenless approval-preview exception (2026-09-07)

An `accepted_for_future_approval` synthetic proposal may create one durable
`supervisor.approval.preview`. The preview binds the exact proposal revision and
content hash, lists one plan-review operation and explicit prohibited execution
operations, records future approver-identity and fresh-intent requirements, and
has a 15-minute attended review window. The operator may mark it
`reviewed_no_authority`, deny it, or withdraw it. Each change is confirmed,
Guardian-gated, revision-checked, evidenced, and atomically committed with its
completion event.

This exception does not instantiate `approval.request` or `approval.result`.
Identity binding, nonce/replay record, approval binding, token issuance or
verification, worker assignment, Arc dispatch, model/tool/connector use,
submission, and external effects remain false. Review expiry is calculated only
on explicit load/action; no background poller or hidden transition is added.

## Approved pending approval-request exception (2026-09-08)

After a preview reaches `reviewed_no_authority`, the attended owner may bind the
current localhost process to a pseudonymous digest of the current OS subject.
This 30-minute `personal_pc_attended_lab` session collects no password or PIN,
does not persist the raw OS username, is lost on restart, and is not production
identity, MFA, an approval, or an execution credential.

With a current source proposal, unexpired preview, active same-process binding,
exact revisions/hashes, and a second fixed confirmation, Guardian may return
`requires_approval` and the Supervisor may atomically persist one
`approval.request` in `pending_review`. This request allows only
`review_prepared_form_plan`, has external effect `none` and `max_uses: 0`, and
cannot produce a positive approval, token, approval binding, token verification,
replay record, worker assignment, Arc dispatch, model/tool/connector use,
submission, or external effect.

## Approved non-authorizing approval-decision exception (2026-09-09)

A synthetic request in `pending_review` may now transition exactly once to
`denied`, `cancelled`, or `expired`. Deny requires any active attended lab
session; cancel additionally requires the original requester's same
process-bound binding. Expiry is never automatic: after the request TTL, an
explicit foreground action records the terminal expiry without restoring the
lost session.

The service revalidates the exact request hash and current status. Deny and
cancel also revalidate the source proposal and preview. Guardian must return
`allow_with_evidence`, then the updated request, separate `approval.result`,
and completion event commit in one SQLite transaction. Every result fixes
approved scope, token, binding, nonce, worker, replay, verification, dispatch,
and external-effect fields to null or false. Positive approval is not a legal
transition in this lane.


## Phase 1A Runtime State

The `approval.readiness` record added on 2026-09-09 is contract/documentation
only. It aggregates design prerequisites and fixes all authority flags false.
It does not add a positive-result endpoint, identity provider, MFA ceremony,
token issuer, binding service, replay consumption, worker assignment, or Arc
dispatch.

The core Phase 1A runtime remains mock/in-memory only apart from the explicit
attended harness exceptions above.
Approved Phase 1B narrow addition is also mock/in-memory only:
worker lifecycle simulator metadata transitions.
Task lifecycle simulator metadata transitions.
Approved Phase 1C narrow addition is also mock/in-memory only:
evidence lifecycle simulator metadata transitions.
Guardian replay drill simulator metadata transitions.

It contains contract loading, contract validation, a default-deny Guardian
policy stub, in-memory worker registry, heartbeat validation, in-memory task
queue, cross-contract invariant checks, metadata-only Supervisor health
reporting, and metadata-only in-memory evidence writer.
This branch also includes a mock-only Guardian decision replay verifier that
validates expiry, replay nonce, scope, clock-skew, approval binding, token
verification, and evidence refs in memory for tests.

It does not contain live dispatch, live tool execution, durable business-data
persistence beyond the bounded synthetic harness proposal store, external
services, production operations, or customer-system mutation.

## Explicit Blocks

- No live connectors.
- No OAuth/provider wiring.
- No connector tokens, webhooks, live reads, or live writes.
- No external email, text, chat, form submission, or customer-system send.
- No real IT remediation.
- No production server touch.
- No software install/update execution.
- No durable database, queue, web server, scheduler, daemon, or UI except the
  explicitly bounded loopback Arc physical-PC test harness and its synthetic
  task-proposal records above.
- No browser automation.
- No external model provider calls except the exact attended read-only
  Supervisor exception above.
- No unrestricted browser, file, network, shell, connector, or tool access.
- No cross-tenant memory sharing.
- No hidden background actions.
- No helper execution except the exact foreground synthetic review above.

The worker lifecycle simulator does not add any exception to these blocks.
The task lifecycle simulator does not add any exception to these blocks.
The evidence lifecycle simulator does not add any exception to these blocks.
The Guardian replay drill simulator does not add any exception to these blocks.

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
- Persisting and reviewing fixed synthetic task proposals in the attended
  harness without issuing approval or dispatch authority.
- Previewing a future approval-request scope without creating an approval
  request, result, identity binding, replay record, token, or dispatch authority.
- Binding a short-lived attended personal-PC lab session and creating one
  durable pending-only synthetic form-review request with no execution authority.

## Future Approval Required

Future approval is required before:

- Any live connector review, OAuth/provider wiring, token storage, webhook, live
  read, live write, or connector-side effect.
- Any external model provider call or model account integration beyond the
  attended read-only Supervisor exception above.
- Any external message, form submission, or customer-system mutation.
- Any file delete/overwrite beyond mock records.
- Any remediation, software install/update, endpoint control, network change, or
  production server touch.
- Any production or customer-data database, queue, service, scheduler, UI, or
  operator-console implementation beyond the attended lab exceptions above.
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
