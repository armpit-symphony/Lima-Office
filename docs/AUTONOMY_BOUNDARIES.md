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
- Blocked MVP actions are denied rather than routed for approval; they must map to `approval.result` denied, `guardian.decision` denied or `block_mvp`, `tool.invocation` denied or `blocked_mvp`, and `task.execution` blocked or denied.
- If evidence is required and evidence cannot be written, the action maps to `evidence.failure` and the task/tool path blocks or degrades according to the evidence failure policy.
- External writes and live connector actions remain unavailable in Phase 0.
- Helper agents and workers share the same autonomy boundaries.

## Contract Mapping

Autonomy decisions must map to the field-level contracts in [contracts/v1](../contracts/v1).

| Boundary | Required contracts | Required outcome |
| --- | --- | --- |
| Allowed automatically | `guardian.decision`, action-specific contract, `evidence.artifact` | Guardian returns `allow` or `allow_with_evidence`; evidence is linked; no approval token is needed. |
| Approval required | `guardian.decision`, `approval.request`, `approval.result`, `approval.token`, `token.verification`, action-specific contract, `tool.invocation` where a tool is involved, `evidence.artifact` | Guardian returns `requires_approval`; request is reviewed; a scoped, expiring, single-use token is issued only after approval and verified before the action can leave draft/mock/read-only mode. |
| Blocked for MVP | `guardian.decision`, `approval.result`, action-specific contract, `tool.invocation` where a tool is involved, `task.execution`, `evidence.artifact`, `incident.ops` where suspicious behavior exists | Guardian returns `deny` or `block_mvp`; approval result is `denied`; task/tool state is `blocked`, `denied`, or `blocked_mvp`; no approval token is issued; evidence records the denial. |
| Evidence unavailable | `evidence.failure`, `task.execution`, `tool.invocation`, `worker.heartbeat`, `incident.ops` where needed, `evidence.artifact` where the fallback writer can record metadata | Required evidence cannot be written before action, so privileged action is blocked; post-action failure degrades, queues reconciliation, and may quarantine the worker. |

Action-specific contract mapping:

- External email/text/chat drafts and sends: `task.execution`, `approval.request`, `approval.token`, `tool.invocation`, `guardian.decision`, `evidence.artifact`.
- Approval outcomes: `approval.result` records `approved`, `denied`, `expired`, `cancelled`, `superseded`, or `partial_approved`; blocked-MVP actions use `denied` with no token.
- File delete or overwrite requests: `tool.invocation`, `guardian.decision`, `approval.request` if future policy allows, `evidence.artifact`; unapproved deletion is denied.
- Customer record mutation: `tool.invocation`, `connector.trust`, `approval.request`, `approval.token`, `guardian.decision`, `evidence.artifact`; live connector writes are blocked in Phase 0.
- Sensitive HR/finance/legal/medical access: `memory.access` or `connector.trust`, `approval.request`, `guardian.decision`, `evidence.artifact`.
- Token verification: `token.verification` records valid or fail-closed results for expired, revoked, used, missing, mismatched, ambiguous, or wrong-scope tokens.
- Software install/update and remediation: `lima_it.handoff`, `approval.request`, `approval.result`, `guardian.decision`, `evidence.artifact`; remediation execution and production touch are blocked in Phase 0.
- Cross-tenant memory access: `memory.access`, `guardian.decision`, `incident.ops`, `evidence.artifact`; `cross_tenant_access` must be `false`.
- Tainted content: `taint.ref`, `guardian.decision`, `tool.invocation`, `memory.access`, `model.route`, `evidence.artifact`; unresolved taint blocks privileged tools, durable memory writes, external sends, approval scope, and remediation.
