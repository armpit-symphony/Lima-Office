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
| Invalid approval token use | Elevation, repudiation | Expired, revoked, used, replayed, missing, mismatched, wrong-scope, wrong-worker, or widened token binding is accepted | Token verification contract, approval binding contract, one-time token lifecycle, fail-closed policy | Token verification failure, binding mismatch, scope mismatch, replay attempt | Token verification record, approval binding record, Guardian denial, evidence | schema_defined |
| Evidence writer failure | Repudiation, tampering, denial | Privileged action proceeds without evidence or post-action proof is missing | Evidence failure contract, pre-action block, degraded spool, reconciliation, quarantine | Evidence writer failure state, queue exhaustion, integrity error | Evidence failure record, incident, worker heartbeat/lifecycle evidence | schema_defined |
| Blocked-MVP action attempted by operator or worker | Elevation, tampering | Phase 0 blocked action is treated as approvable | Approval result denial, Guardian block, task/tool blocked state | Blocked action request, production touch or remediation attempt | Approval denial, Guardian decision, tool/task denial evidence | schema_defined |
| Model/tool hallucination causing business action | Tampering, repudiation | Model invents action, recipient, or record update | Draft-first workflow, approval for writes, evidence checks | High-risk action request, confidence mismatch | Task result, approval record, Guardian decision | schema_defined |
| Update supply-chain compromise | Tampering, elevation | Bad update changes worker/supervisor behavior | Verified update source, known-good rollback, approval | Version mismatch, failed verification | Update evidence, incident record, rollback record | future_review |
| Customer network compromise | Spoofing, denial, disclosure | Local attacker targets supervisor/worker channel | Authenticated channel, firewall assumptions, quarantine | Connection anomaly, repeated failures | Network incident record, worker containment | schema_defined |
| Worker deployment spoofing | Spoofing, elevation | Unapproved mini PC is enrolled as a trusted worker | Deployment record, device/channel identity refs, operator approval, Guardian decision | Deployment preflight mismatch, duplicate worker ID, missing evidence | `worker.deployment`, worker lifecycle, Guardian decision, enrollment evidence | schema_defined |
| Operator identity or MFA ambiguity | Spoofing, elevation, repudiation | Ambiguous operator or stale role approves privileged work | Identity/MFA policy, access review, approver separation, Guardian decision | Missing MFA posture, stale access review, self-approval, conflicted approver | Governance identity/access review records, approval evidence | schema_defined |
| Breakglass misuse | Elevation, repudiation | Emergency path bypasses Guardian, evidence, or blocked-MVP boundaries | Breakglass policy blocks MVP runtime use and preserves evidence | Breakglass request, blocked action class, missing approver, expired scope | Breakglass denial, incident ref, evidence artifact | schema_defined |
| Unsafe audit export or customer exit delete | Disclosure, repudiation | Export leaks sensitive records or delete loses required evidence | Redaction profile, non-exportable classes, preservation conflict review | Export scope mismatch, unredacted class, delete conflict | Audit export record, evidence refs, customer exit review | schema_defined |
| Connector consent or scope drift | Elevation, disclosure | Connector scope expands without consent or revocation evidence | Connector consent policy, scope review, live access false, revocation evidence | Scope mismatch, revoked consent, prompt-injection unresolved | Connector consent record, connector trust record, taint evidence | schema_defined |
| Update or attestation failure | Tampering, elevation, denial | Bad update or weak worker identity changes behavior | Signed update placeholder, automatic update false, attestation review, rollback | Hash mismatch, failed verification, attestation failure, health degradation | Update record, worker quarantine, rollback evidence | schema_defined |
| Unsafe approval UX | Elevation, repudiation | Console makes blocked or ambiguous request appear approvable | Approval inbox spec, permission model, no self-approval, fail-closed controls | Missing evidence, taint, self-approval, stale decision, token mismatch | `console.action`, approval result, Guardian decision, evidence artifact | schema_defined |
| Mock state presented as live | Tampering, repudiation | Operator believes draft/mock/readiness state executed live action | UX labels, blocked-MVP state, runtime boundary docs | Blocked action attempt, live connector confusion, missing runtime ref | Console view/action evidence, Guardian denial | schema_defined |
| Evidence omission in command view | Repudiation | Operator decision lacks visible evidence/policy/Guardian context | Evidence viewer spec, required evidence refs, fail-closed UX | Missing evidence ref, evidence writer degraded, export conflict | `console.alert`, `evidence.failure`, incident record | schema_defined |
| Public worker exposure | Disclosure, elevation, denial | Worker exposes inbound service or remote support path | Network blueprint blocks public inbound exposure and direct cross-worker trust | Firewall/preflight mismatch, unexpected reachability | Worker deployment evidence, incident record, field IT checklist | schema_defined |
| Device reuse without purge | Disclosure, repudiation | Retired or replacement worker carries tenant cache or stale evidence | Revoke, cache purge evidence, customer exit/delete posture | Replacement review, cache purge missing, old device heartbeat | Worker lifecycle, worker deployment, evidence artifact, incident record | needs_contract |

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
| Worker deployment spoofing or unsafe deployment | `worker.deployment`, `worker.lifecycle`, `guardian.decision`, `evidence.artifact`, `incident.ops` | Deployment records require worker ID, deployment ID, hardware/OS/network profiles, Supervisor endpoint ref, policy/model refs, encryption and attestation posture, no public inbound exposure, no cross-worker trust, Guardian decision, and evidence refs. |
| Operator identity or MFA ambiguity | `governance.identity`, `governance.access_review`, `approval.request`, `approval.result`, `evidence.artifact` | Identity records require subject refs, role refs, MFA placeholder status, access review refs, and evidence. Missing or ambiguous identity posture fails closed for privileged runtime expansion. |
| Breakglass misuse | `governance.breakglass`, `guardian.decision`, `incident.ops`, `evidence.artifact` | Breakglass is denied or blocked metadata in MVP. It cannot bypass Guardian, evidence, incident review, or blocked-MVP actions. |
| Unsafe audit export or customer exit delete | `governance.audit_export`, `evidence.artifact`, `memory.access`, `incident.ops` | Export/delete records require tenant scope, redaction profile, non-exportable classes, evidence preservation conflict posture, Guardian decision, and evidence refs. |
| Connector consent or scope drift | `governance.connector_consent`, `connector.trust`, `taint.ref`, `evidence.artifact` | Consent and scope records keep live access false, secret material absent, blocked scopes explicit, revocation evidenced, and prompt-injection review required before live review. |
| Update supply-chain or rollback failure | `governance.update_record`, `worker.deployment`, `worker.lifecycle`, `worker.heartbeat`, `incident.ops` | Update records require source/version/hash refs, signature verification placeholder, staged rollout posture, automatic update false, known-good rollback, attestation posture, and evidence refs. |
| Unsafe approval UX | `console.action`, `approval.request`, `approval.result`, `approval.token`, `token.verification`, `guardian.decision`, `evidence.artifact` | Console action records have `runtime_effect: false`; approval UX must show scope hash, risk, data class, expiry, taint, evidence, and deny/block states before metadata decisions. |
| Mock state presented as live | `console.view`, `console.alert`, `guardian.decision`, `connector.trust`, `lima_it.handoff` | Console views label mock, dry-run, and blocked-MVP states and cannot imply live connector readiness, external sends, remediation, or production operation. |
| Evidence omission in command view | `console.alert`, `console.view`, `evidence.artifact`, `evidence.failure`, `incident.ops` | Missing evidence creates blocked alert/review state; evidence viewer shows redaction, retention, integrity refs, and runbook links. |
| Rogue helper agent | `helper.scope`, `task.execution`, `tool.invocation`, `memory.access`, `guardian.decision`, `incident.ops`, `evidence.artifact` | Helper agents remain supervisor-side actors with scoped tasks; out-of-scope tool/memory requests are denied and evidenced. |
| Invalid/expired/revoked/replayed token use | `token.verification`, `approval.binding`, `approval.token`, `approval.result`, `guardian.decision`, `tool.invocation`, `evidence.artifact` | Missing, expired, revoked, used, replayed, mismatched, tainted, ambiguous, wrong-scope, wrong-worker, or widened token bindings fail closed and cannot authorize action. |
| Evidence writer failure | `evidence.failure`, `task.execution`, `tool.invocation`, `worker.heartbeat`, `worker.lifecycle`, `incident.ops`, `evidence.artifact` | Pre-action evidence failure blocks privileged actions; post-action failure degrades, spools, reconciles, and may quarantine. |
| LIMA IT remediation misuse | `lima_it.handoff`, `approval.request`, `approval.result`, `guardian.decision`, `incident.ops`, `evidence.artifact` | Diagnostic handoff is read-only; remediation request metadata is denied or approval-required; remediation execution and production touch remain blocked in MVP. |
| Blocked-MVP action attempted | `approval.result`, `approval.binding`, `guardian.decision`, `task.execution`, `tool.invocation`, `evidence.artifact`, `incident.ops` | Blocked-MVP requests produce denial/block states and no usable approval token or binding. |

## Open Threat Questions

- What identity provider should operators use?
- Is hardware attestation required for worker mini PCs?
- What is the first data retention period?
- Which connector is first eligible for live review?
- What exceptions to the local-supervisor-first network posture are acceptable
  for the first lab?
- What customer exit/delete proof is required before device reuse or retirement?
- Which IdP/MFA mechanism, session TTL, and device trust posture should back
  the governance identity metadata?
- What signing root, attestation method, and rollback trigger matrix should
  replace the current placeholders?
