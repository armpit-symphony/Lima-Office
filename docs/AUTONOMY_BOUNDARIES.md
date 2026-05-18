# Autonomy Boundaries

Guardian classification and evidence are required for all categories. "Allowed automatically" means no human approval is required; it does not mean Guardian is bypassed.

## Allowed Automatically

- Summarize documents.
- Classify tickets.
- Draft emails/messages.
- Prepare forms.
- Gather read-only diagnostics using metadata/ref-based checks only; no secrets, no raw sensitive payload dumps, no mutation, and no hidden background work.
- Update internal notes.
- Suggest runbook steps.
- Draft file-organization plans and update internal notes. File move, rename, export, delete, or overwrite requires approval or remains blocked by policy.
- Produce customer-service draft replies.

## Approval Required

- Send external email/text/chat.
- Submit forms.
- Delete/overwrite files.
- Modify customer records.
- Install/update software.
- Run remediation.
- Access sensitive HR/finance/legal/medical data.
- Touch production servers.
- Use payment/legal/regulated systems.

## Blocked For MVP

- Autonomous financial decisions.
- Autonomous employee discipline/monitoring decisions.
- Autonomous production server changes.
- Cross-tenant memory sharing.
- Hidden background actions.
- Unrestricted browser/file/network access.

## Enforcement Notes

- Approval-required actions need approver identity, scope, expiration, replay protection, Guardian decision, and evidence.
- Blocked MVP actions are denied rather than routed for approval.
- External writes and live connector actions remain unavailable in Phase 0.
- Helper agents and workers share the same autonomy boundaries.

## Contract Mapping

Autonomy decisions must map to the field-level contracts in [contracts/v1](../contracts/v1).

| Boundary | Required contracts | Required outcome |
| --- | --- | --- |
| Allowed automatically | `guardian.decision`, action-specific contract, `evidence.artifact` | Guardian returns `allow` or `allow_with_evidence`; evidence is linked; no approval token is needed. |
| Approval required | `guardian.decision`, `approval.request`, `approval.token`, action-specific contract, `tool.invocation` where a tool is involved, `evidence.artifact` | Guardian returns `requires_approval`; request is reviewed; a scoped, expiring, single-use token is issued before the action can leave draft/mock/read-only mode. |
| Blocked for MVP | `guardian.decision`, action-specific contract, `evidence.artifact`, `incident.ops` where suspicious behavior exists | Guardian returns `deny` or `block_mvp`; no approval token is issued; evidence records the denial. |

Action-specific contract mapping:

- External email/text/chat drafts and sends: `task.execution`, `approval.request`, `approval.token`, `tool.invocation`, `guardian.decision`, `evidence.artifact`.
- File delete or overwrite requests: `tool.invocation`, `guardian.decision`, `approval.request` if future policy allows, `evidence.artifact`; unapproved deletion is denied.
- Customer record mutation: `tool.invocation`, `connector.trust`, `approval.request`, `approval.token`, `guardian.decision`, `evidence.artifact`; live connector writes are blocked in Phase 0.
- Sensitive HR/finance/legal/medical access: `memory.access` or `connector.trust`, `approval.request`, `guardian.decision`, `evidence.artifact`.
- Software install/update and remediation: `lima_it.handoff`, `approval.request`, `approval.token`, `guardian.decision`, `evidence.artifact`; direct production remediation is blocked in MVP.
- Cross-tenant memory access: `memory.access`, `guardian.decision`, `incident.ops`, `evidence.artifact`; `cross_tenant_access` must be `false`.
