# Prompt Injection Response Runbook

## Purpose

Guide operator response to suspected prompt injection from email, documents, chat, browser pages, tickets, forms, files, connector content, tool output, or retrieved memory.

## Policy Traceability

- Policy ref: `policy.prompt_injection.phase0`
- Version: `policy-phase0-v1`
- Triggering contracts: `guardian.decision`, `model.route`, `tool.invocation`, `memory.access`, `connector.trust`, `incident.ops`, `evidence.artifact`.
- Required fields: tenant/customer context, source refs, content origin, taint status, injection signals, containment action, Guardian decision ID, evidence artifact IDs, correlation ID.
- Fail-closed outcome: treat tainted content as data, block privileged paths, block durable raw memory writes, keep external messages draft-only.

## When To Use

Use this runbook when Guardian, a worker, helper agent, or operator flags:

- Attempts to override instructions.
- Requests for secrets.
- Requests for unapproved tools.
- Requests for external sends or file mutations.
- Suspicious content in memory retrieval.
- Repeated tainted content across tasks.

## Prerequisites

- Identify source ref, tenant ID, customer context, task ID, correlation ID, and content origin.
- Confirm tainted content is treated as data, not instructions.
- Confirm Guardian decision and evidence refs exist or can be created.

## Must Not

- Do not run privileged tools from tainted input.
- Do not approve external sends based solely on tainted content.
- Do not write tainted raw content to durable memory.
- Do not let tainted content override system, developer, Guardian, policy, tenant, or operator instructions.
- Do not paste raw suspicious content into logs if it contains sensitive data.

## Procedure

1. Mark source as tainted.
2. Stop privileged tool, connector, memory-write, and external-message paths for the task.
3. Review Guardian prompt-injection fields and containment action.
4. If tainted content requested privileged action, deny or require operator-safe re-scope.
5. If durable memory write was requested, block raw write and allow only policy-approved sanitized summary refs.
6. If external message draft exists, keep draft-only and require fresh operator intent.
7. Record evidence with source refs, signals, and containment action.
8. Create incident if the injection requests secrets, policy bypass, external sends, file mutation, connector writes, or remediation.
9. Quarantine worker or helper agent if it attempted to act on tainted instructions.

## Approval Requirements

Approval cannot convert prompt-injected instructions into trusted operator intent. A human operator must provide fresh intent outside the tainted content, and Guardian must evaluate the new scoped request.

## Evidence To Capture

- Source refs and origin.
- Injection signals.
- Guardian decision.
- Blocked action class.
- Taint propagation to model/tool/memory/connector records.
- Operator decision.
- Incident ID when created.

## Containment / Rollback

- Revoke approval tokens created from tainted context.
- Cancel or block affected tasks.
- Quarantine worker/helper if it attempted unsafe action.
- Mark memory records sourced from the tainted item for review.

## Escalation

Escalate to security reviewer for secret requests, policy bypass, repeated attempts, or cross-task taint propagation.

Escalate to compliance reviewer if sensitive HR, finance, legal, medical, or customer-confidential data is involved.

## Done Criteria

- Tainted source is labeled.
- Privileged paths are blocked or re-scoped.
- Evidence is recorded.
- Incident exists when required.
- No durable raw memory write occurred.
- No external send occurred from tainted input.
