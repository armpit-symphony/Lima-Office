# Threat Model

## Method

This threat model uses STRIDE as a practical checklist: spoofing, tampering, repudiation, information disclosure, denial of service, and elevation of privilege.

Phase 0 status values:

- `documented`: covered by current docs.
- `needs_contract`: contract fields or states still needed.
- `schema_defined`: field-level schema/control exists, but runtime remains blocked.
- `blocked_mvp`: denied for MVP.
- `future_review`: deferred until implementation planning.

## Assets

- Customer data.
- Worker identities.
- Operator approvals.
- Connector readiness and future tokens.
- Model prompts and outputs.
- Tenant memory.
- Evidence artifacts.
- Supervisor policy.
- LIMA IT handoff records.

## Trust Boundaries

- Operator to Supervisor.
- Supervisor to Arc worker.
- Supervisor to helper agent.
- Guardian to model/tool/connector.
- Worker to local cache.
- LIMA Office to LIMA IT.
- Tenant to tenant.
- Local network to internet.

## Threat Scenarios

| Scenario | STRIDE | Risk | Control | Detection | Evidence | MVP Status |
| --- | --- | --- | --- | --- | --- | --- |
| Malicious worker node | Spoofing, tampering, elevation | Worker accepts tasks or reports false results | Device identity, capability lease, Guardian decisions, quarantine | Heartbeat anomaly, capability mismatch, evidence mismatch | Worker lifecycle event, Guardian decision, quarantine record | schema_defined |
| Compromised mini PC | Tampering, disclosure, denial | Local cache or task data exposed; worker misused | Encrypted cache, least privilege, revoke, replacement flow | Missed heartbeat, endpoint alert, suspicious tool request | Incident record, worker status, containment action | schema_defined |
| Stolen API key | Spoofing, disclosure, elevation | Connector/model access abused | No plaintext keys, secret refs, rotation, revocation | Secret access anomaly, failed scope check | Secret reference event, Guardian denial, incident record | schema_defined |
| Prompt injection through email/doc/chat/browser/ticket | Tampering, elevation | Model follows hostile instructions and requests unsafe action | Treat content as untrusted, tool mediation, Guardian decision, approval | Suspicious instruction patterns, high-risk tool request | Input classification, denial/approval evidence | schema_defined |
| Bad connector scopes | Elevation, disclosure | Connector grants write/admin access too early | Connector trust contract, mock first, scope review | Scope mismatch, connector readiness block | Connector readiness evidence, Guardian denial | schema_defined |
| Cross-tenant memory leak | Disclosure | Data from one customer appears in another context | Tenant namespaces, no cross-tenant memory, exit/delete posture | Tenant ID mismatch, retrieval audit | Memory access denial, audit event | blocked_mvp |
| Unauthorized outbound message | Repudiation, tampering | External email/text/chat sent without approval | Approval required, Guardian outbound gate, no live sends in Phase 0 | Outbound request without approval token | Guardian denial, approval audit | blocked_mvp |
| Unauthorized file mutation | Tampering | Business file deleted or overwritten | Approval required, file mutation gate, version/rollback plan | File write request risk tier | Guardian decision, approval result, evidence | schema_defined |
| Rogue supervisor/helper agent | Elevation, repudiation | Helper agent bypasses operator or tool limits | Helper scope contract, RBAC, Guardian gate, evidence | Tool request outside scope, missing operator context | Helper action evidence, denial/quarantine | schema_defined |
| Invalid approval token use | Elevation, repudiation | Expired, revoked, used, missing, mismatched, or wrong-scope token is accepted | Token verification contract, one-time token lifecycle, fail-closed policy | Token verification failure, scope mismatch, replay attempt | Token verification record, Guardian denial, evidence | schema_defined |
| Evidence writer failure | Repudiation, tampering, denial | Privileged action proceeds without evidence or post-action proof is missing | Evidence failure contract, pre-action block, degraded spool, reconciliation, quarantine | Evidence writer failure state, queue exhaustion, integrity error | Evidence failure record, incident, worker heartbeat/lifecycle evidence | schema_defined |
| Blocked-MVP action attempted by operator or worker | Elevation, tampering | Phase 0 blocked action is treated as approvable | Approval result denial, Guardian block, task/tool blocked state | Blocked action request, production touch or remediation attempt | Approval denial, Guardian decision, tool/task denial evidence | schema_defined |
| Model/tool hallucination causing business action | Tampering, repudiation | Model invents action, recipient, or record update | Draft-first workflow, approval for writes, evidence checks | High-risk action request, confidence mismatch | Task result, approval record, Guardian decision | schema_defined |
| Update supply-chain compromise | Tampering, elevation | Bad update changes worker/supervisor behavior | Verified update source, known-good rollback, approval | Version mismatch, failed verification | Update evidence, incident record, rollback record | future_review |
| Customer network compromise | Spoofing, denial, disclosure | Local attacker targets supervisor/worker channel | Authenticated channel, firewall assumptions, quarantine | Connection anomaly, repeated failures | Network incident record, worker containment | schema_defined |

## Required Controls Before Runtime

- Guardian decision envelope.
- Worker identity and revocation.
- Approval request/result.
- Evidence artifact redaction and retention.
- Connector trust/readiness.
- Prompt injection handling.
- Tenant memory boundary.
- Secure update/rollback.
- Incident runbooks.
- Policy refs and policy snapshot/hash linkage for Guardian decisions.
- Operator runbooks for approval token lifecycle, evidence writer failure, prompt injection response, worker re-enrollment, and LIMA IT handoff.

## Schema Control Map

The Phase 0 schemas do not implement controls, but they define the required records that future controls must produce.

| Threat | Primary schema controls | Required control behavior |
| --- | --- | --- |
| Prompt injection | `taint.ref`, `guardian.decision`, `model.route`, `tool.invocation`, `memory.access`, `connector.trust`, `evidence.artifact` | Treat external content as untrusted data; propagate taint refs; block direct privileged tools, durable memory writes, external sends, approval scope, and remediation until policy clears them. |
| Unauthorized outbound message | `guardian.decision`, `approval.request`, `approval.result`, `approval.token`, `token.verification`, `task.execution`, `tool.invocation`, `evidence.artifact` | Require Guardian `requires_approval`, approved result, scoped single-use token, and valid token verification; Phase 0 examples remain dry-run/draft-only. |
| Unauthorized file mutation | `guardian.decision`, `tool.invocation`, `approval.request`, `approval.result`, `approval.token`, `token.verification`, `evidence.artifact`, `incident.ops` | File delete/overwrite is denied without approval; unapproved mutation attempts create evidence and may create an incident. |
| Cross-tenant memory leak | `memory.access`, `guardian.decision`, `evidence.artifact`, `incident.ops` | Require tenant namespace, `tenant_match_required: true`, `cross_tenant_access: false`, cross-tenant check result, denial evidence, and incident escalation. |
| Stolen API key | `connector.trust`, `guardian.decision`, `incident.ops`, `evidence.artifact` | Phase 0 connector records use refs only, `secret_material_present: false`, revocation status, scope review, and incident evidence on suspected exposure. |
| Rogue worker | `worker.lifecycle`, `worker.heartbeat`, `guardian.decision`, `tool.invocation`, `incident.ops`, `evidence.artifact` | Capability mismatch, suspicious tools, evidence failure, or heartbeat anomalies trigger quarantine/revoke metadata and evidence. |
| Rogue helper agent | `helper.scope`, `task.execution`, `tool.invocation`, `memory.access`, `guardian.decision`, `incident.ops`, `evidence.artifact` | Helper agents remain supervisor-side actors with scoped tasks; out-of-scope tool/memory requests are denied and evidenced. |
| Invalid/expired/revoked token use | `token.verification`, `approval.token`, `approval.result`, `guardian.decision`, `tool.invocation`, `evidence.artifact` | Missing, expired, revoked, used, mismatched, ambiguous, or wrong-scope tokens fail closed and cannot authorize action. |
| Evidence writer failure | `evidence.failure`, `task.execution`, `tool.invocation`, `worker.heartbeat`, `worker.lifecycle`, `incident.ops`, `evidence.artifact` | Pre-action evidence failure blocks privileged actions; post-action failure degrades, spools, reconciles, and may quarantine. |
| LIMA IT remediation misuse | `lima_it.handoff`, `approval.request`, `approval.result`, `guardian.decision`, `incident.ops`, `evidence.artifact` | Diagnostic handoff is read-only; remediation request metadata is denied or approval-required; remediation execution and production touch remain blocked in MVP. |
| Blocked-MVP action attempted | `approval.result`, `guardian.decision`, `task.execution`, `tool.invocation`, `evidence.artifact`, `incident.ops` | Blocked-MVP requests produce denial/block states and no approval token. |

## Open Threat Questions

- What identity provider should operators use?
- Is hardware attestation required for worker mini PCs?
- What is the first data retention period?
- Which connector is first eligible for live review?
- What local network assumptions are acceptable for the first lab?
