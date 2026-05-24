# Audit Export And Customer Exit Policy

## Purpose

Define the docs-only policy for audit export, customer exit, delete requests,
and evidence preservation conflicts.

Policy ref: `policy.audit_export_customer_exit.phase0`

Status: draft scaffold. No export service, delete service, durable store, or
customer portal is implemented.

## Audit Export Purpose

Audit export exists to produce a redacted, scoped package of governance,
Guardian, approval, task, worker, evidence, connector, model route, tool,
memory, LIMA IT handoff, and incident metadata for review.

Export does not authorize live connectors, external sends, remediation, or
production operation.

## Exportable Records

Export candidates:

- Task metadata.
- Guardian decisions.
- Approval requests, results, token metadata, and token verification metadata.
- Evidence artifact metadata and integrity refs.
- Worker lifecycle, heartbeat, and deployment metadata.
- Model route metadata.
- Tool invocation metadata.
- Memory access metadata.
- Connector trust and consent metadata.
- LIMA IT diagnostic handoff metadata.
- Incident metadata.
- Governance identity, access review, breakglass, audit export, connector
  consent, and update records.

## Non-Exportable Or Secret Records

Do not export:

- Credentials, API tokens, OAuth codes, session material, or secret values.
- Raw prompts, raw model responses, raw connector payloads, raw tool output, or
  raw customer files.
- Private signing keys or device key material.
- Unredacted sensitive HR, finance, legal, medical, payment, or regulated data.
- Data outside the requested tenant/customer context.

## Redaction Before Export

Before export:

- Confirm export scope and requester.
- Select redaction profile.
- Remove secret material and raw payloads.
- Replace sensitive resources with refs.
- Record exclusions and preservation conflicts.
- Capture evidence of review and approval.

Phase 1A posture now models export metadata with
`evidence.export_manifest`. The manifest remains refs-only metadata and must
carry `raw_content_included: false` and `secret_material_included: false`.
Prepared/exported status requires a redaction profile and retention refs.

## Customer Exit Process

Customer exit requires:

- Exit request record.
- Tenant/customer context confirmation.
- Export scope decision.
- Connector revocation plan.
- Worker cache purge plan.
- Memory delete/export posture.
- Evidence preservation conflict review.
- Device retirement or reset plan.
- Handoff notes and final evidence record.

## Delete Request Process

Delete request steps:

1. Record requester identity ref and customer context.
2. Classify requested delete scope.
3. Identify evidence, incident, retention, and legal/policy conflict
   placeholders.
4. Require approval and evidence.
5. Execute only after a future approved implementation exists.
6. Record proof refs, exclusions, and unresolved conflicts.

## Evidence Preservation Conflict Placeholder

Delete requests can conflict with evidence preservation, security incidents,
audit trail needs, or future legal obligations. This repo does not decide final
retention law or legal hold posture. Ambiguous conflict fails closed and blocks
automatic delete.

Denied or blocked export/delete outcomes must explicitly include
`delete_conflict_refs` in export-manifest metadata.

## Operator Approval Requirements

- Export requires operator approval.
- Sensitive export requires security or compliance review.
- Delete requires operator approval and compliance review.
- Customer exit requires operator, field IT, and compliance/security review
  where worker devices, connectors, memory, or incidents are in scope.

## Audit Log Of Export/Delete Actions

Every export/delete request must create:

- Request ID.
- Actor/requester ref.
- Approver refs.
- Tenant/customer context.
- Scope and redaction profile.
- Included/excluded record classes.
- Evidence refs.
- Status and reason.
- Created/updated timestamps.

When export-manifest records are produced, include:

- manifest ID and request ID;
- included/excluded evidence refs;
- redaction profile ref;
- retention policy refs;
- delete conflict refs when denied/blocked;
- hash manifest ref when prepared/exported.

## MVP Blocked Areas

- No live export service.
- No automatic delete service.
- No durable evidence store is added.
- No customer portal or UI is added.
- No compliance certification claim is made.

## Acceptance Gates

- `governance.audit_export` can represent export/delete request posture.
- `evidence.export_manifest` can represent refs-only prepared/denied outcomes.
- Customer exit/delete runbook exists.
- Export/delete records use refs, not raw payloads.
- Evidence preservation conflicts remain explicit.
- Missing policy, approval, evidence, or redaction posture fails closed.
