# Threat Model

## Method

This threat model uses STRIDE as a practical checklist: spoofing, tampering, repudiation, information disclosure, denial of service, and elevation of privilege.

Phase 0 status values:

- `documented`: covered by current docs.
- `needs_contract`: contract fields or states still needed.
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
| Malicious worker node | Spoofing, tampering, elevation | Worker accepts tasks or reports false results | Device identity, capability lease, Guardian decisions, quarantine | Heartbeat anomaly, capability mismatch, evidence mismatch | Worker lifecycle event, Guardian decision, quarantine record | needs_contract |
| Compromised mini PC | Tampering, disclosure, denial | Local cache or task data exposed; worker misused | Encrypted cache, least privilege, revoke, replacement flow | Missed heartbeat, endpoint alert, suspicious tool request | Incident record, worker status, containment action | needs_contract |
| Stolen API key | Spoofing, disclosure, elevation | Connector/model access abused | No plaintext keys, secret refs, rotation, revocation | Secret access anomaly, failed scope check | Secret reference event, Guardian denial, incident record | needs_contract |
| Prompt injection through email/doc/chat/browser/ticket | Tampering, elevation | Model follows hostile instructions and requests unsafe action | Treat content as untrusted, tool mediation, Guardian decision, approval | Suspicious instruction patterns, high-risk tool request | Input classification, denial/approval evidence | needs_contract |
| Bad connector scopes | Elevation, disclosure | Connector grants write/admin access too early | Connector trust contract, mock first, scope review | Scope mismatch, connector readiness block | Connector readiness evidence, Guardian denial | needs_contract |
| Cross-tenant memory leak | Disclosure | Data from one customer appears in another context | Tenant namespaces, no cross-tenant memory, exit/delete posture | Tenant ID mismatch, retrieval audit | Memory access denial, audit event | blocked_mvp |
| Unauthorized outbound message | Repudiation, tampering | External email/text/chat sent without approval | Approval required, Guardian outbound gate, no live sends in Phase 0 | Outbound request without approval token | Guardian denial, approval audit | blocked_mvp |
| Unauthorized file mutation | Tampering | Business file deleted or overwritten | Approval required, file mutation gate, version/rollback plan | File write request risk tier | Guardian decision, approval result, evidence | needs_contract |
| Rogue supervisor/helper agent | Elevation, repudiation | Helper agent bypasses operator or tool limits | Helper scope contract, RBAC, Guardian gate, evidence | Tool request outside scope, missing operator context | Helper action evidence, denial/quarantine | needs_contract |
| Model/tool hallucination causing business action | Tampering, repudiation | Model invents action, recipient, or record update | Draft-first workflow, approval for writes, evidence checks | High-risk action request, confidence mismatch | Task result, approval record, Guardian decision | needs_contract |
| Update supply-chain compromise | Tampering, elevation | Bad update changes worker/supervisor behavior | Verified update source, known-good rollback, approval | Version mismatch, failed verification | Update evidence, incident record, rollback record | future_review |
| Customer network compromise | Spoofing, denial, disclosure | Local attacker targets supervisor/worker channel | Authenticated channel, firewall assumptions, quarantine | Connection anomaly, repeated failures | Network incident record, worker containment | needs_contract |

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

## Open Threat Questions

- What identity provider should operators use?
- Is hardware attestation required for worker mini PCs?
- What is the first data retention period?
- Which connector is first eligible for live review?
- What local network assumptions are acceptable for the first lab?
