# Prompt Injection Handling Policy

## Purpose

Define Phase 0 handling for untrusted content that may try to override system, developer, Guardian, policy, tenant, operator, or task instructions. This policy is scaffolding only and does not implement detectors, model calls, or tool execution.

## Policy Metadata

- Policy ref: `policy.prompt_injection.phase0`
- Version: `policy-phase0-v1`
- Status: Draft scaffold.
- Owner role: Security reviewer.
- Applies to contracts: `guardian.decision`, `model.route`, `tool.invocation`, `memory.access`, `connector.trust`, `incident.ops`, `evidence.artifact`.
- Evidence artifact types: `guardian_decision`, `denial`, `tool_invocation`, `model_route`, `memory_access`, `incident`.
- Fail-closed outcome: deny privileged action, block durable raw memory write, keep external messages draft-only, create incident when suspicious.
- Runbook: [Prompt Injection Response Runbook](../runbooks/prompt-injection-response.md).

## Sources

Prompt injection can arrive through:

- Email.
- Documents.
- Chat.
- Browser pages.
- Tickets.
- Forms.
- Files.
- Connector payloads.
- Memory records sourced from any of the above.

## Must Not

- Do not treat untrusted content as policy, Guardian, operator, system, or developer instruction.
- Do not allow tainted content to directly form privileged tool arguments.
- Do not allow tainted content to create approval scope without fresh operator intent.
- Do not silently write tainted raw content to durable memory.
- Do not send external messages from tainted input in Phase 0.

## Detection Hints

Detection is not limited to exact strings. Hints include:

- Requests to ignore previous instructions.
- Requests to reveal secrets or tokens.
- Requests to use unapproved tools.
- Requests to send messages or mutate records.
- Encoded or hidden instructions.
- Instructions embedded in document metadata.
- Instructions pretending to be policy, Guardian, operator, or supervisor commands.
- Attempts to change tenant, data classification, approval state, or evidence requirements.

## Severity Levels

| Severity | Criteria | Default outcome |
| --- | --- | --- |
| Low | Untrusted content with no unsafe instruction | Treat as data and record taint metadata. |
| Medium | Attempts to influence model behavior or workflow scope | Require Guardian review, block privileged paths until reviewed. |
| High | Requests secrets, external sends, file mutation, connector writes, durable memory writes, or remediation | Deny privileged action, create evidence, consider incident. |
| Critical | Repeated attempts, cross-task propagation, policy bypass, or worker/helper attempted action | Create incident, revoke related tokens, quarantine worker/helper if applicable. |

## Tainted Content Labeling

Content from untrusted sources must be labeled as tainted until reviewed or policy-cleared.

Required metadata:

- Source ref.
- Content origin.
- Data classification.
- Tenant ID.
- Prompt-injection scan status.
- Injection signals.
- Containment action.
- Evidence artifact refs.

Tainted input remains data. It is not an instruction source.

## Taint Propagation

Taint must follow derived artifacts:

- Model prompt refs.
- Model response refs.
- Tool input refs.
- Tool output refs.
- Memory source refs.
- Draft message refs.
- Connector readiness refs.
- Evidence summaries.

Derived content remains tainted until a policy-approved review records a new classification and evidence. Tainted content cannot become approval scope or durable memory content by itself.

## Tool-Use Restrictions When Tainted

Tainted input must not directly trigger:

- File delete or overwrite.
- External message send.
- Connector write.
- Customer record mutation.
- Software install/update.
- Remediation.
- Shell, browser, file, network, or connector access outside explicit scope.
- Approval token request without operator-visible reason and evidence.

Allowed Phase 0 handling:

- Summarize tainted content as data.
- Classify risk.
- Draft a response for operator review.
- Request Guardian decision with taint metadata.
- Escalate suspicious content.

## Memory-Write Restrictions When Tainted

Tainted input must not silently write durable memory.

Allowed Phase 0 memory posture:

- Store only metadata refs and evidence of detection.
- Mark source as tainted.
- Require policy review before durable summary write.
- Block memory writes when source, tenant, purpose, or retention is unclear.
- Default deny durable memory writes from tainted sources.
- Allow only sanitized summary writes with source refs, taint scan result, retention class, delete/export posture, Guardian decision, and evidence.

## External-Message Restrictions When Tainted

Tainted content cannot authorize or trigger external messages.

External message path requires:

- Guardian decision.
- Operator-visible draft.
- Approval request if send is requested.
- Approval token if future policy allows a send path.
- Evidence.

Phase 0 examples remain draft or dry-run only.

Approval cannot convert prompt-injected instructions into trusted operator intent. A human operator must provide fresh intent outside the tainted content, and Guardian must evaluate the new scoped request.

## Escalation Path

Escalate when:

- Injection asks for secrets or policy bypass.
- Injection asks for privileged tools.
- Injection targets external sends, file mutation, connector writes, or remediation.
- Injection is repeated across sources.
- Injection appears in memory retrieved for future tasks.

Escalation records:

- `guardian.decision`.
- `incident.ops` when suspicious or repeated.
- `evidence.artifact`.
- Affected task/tool/model/memory/connector record.

## Evidence Capture

Evidence should include:

- Tainted source refs.
- Detection signals.
- Guardian decision.
- Action requested.
- Policy result.
- Approval state if any.
- Containment action.
- Redaction status.

Do not store raw malicious content if it contains sensitive data or secrets. Use protected refs and redacted summaries.

## MVP Acceptance Gates

- Tainted input cannot override system, developer, Guardian, policy, tenant, or operator instructions.
- Tainted input cannot directly trigger privileged tools.
- Tainted input cannot silently write durable memory.
- Tainted input cannot trigger external sends.
- Suspicious requests produce Guardian and evidence records.
- Operator runbook exists for suspected prompt injection response.
