# Autonomy Boundaries

Guardian classification and evidence are required for all categories. "Allowed automatically" means no human approval is required; it does not mean Guardian is bypassed.

## Allowed Automatically

- Summarize documents.
- Classify tickets.
- Draft emails/messages.
- Prepare forms.
- Gather diagnostics.
- Update internal notes.
- Suggest runbook steps.
- Organize files.
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
