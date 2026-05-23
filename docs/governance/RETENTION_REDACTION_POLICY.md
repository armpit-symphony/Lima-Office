# Retention Redaction Policy

## Purpose

Expand the retention, redaction, export, delete, and access placeholders for
LIMA Office OS record types. This is not legal advice and does not claim legal
or compliance certification.

Policy ref: `policy.retention_redaction.phase0`

Default retention periods remain policy decisions. Future runtime must fail
closed for sensitive durable writes, export, or delete when retention or
redaction posture is missing or ambiguous.

## Record Matrix

| Record type | Data class | Default retention placeholder | Redaction requirement | Export requirement | Delete requirement | Access role | Evidence implications | MVP status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task metadata | `internal` to `customer_confidential` | Policy decision needed | Redact free-text summaries and resource refs by data class | Export task IDs, status, Guardian refs, approval refs, and redacted summaries | Delete/reset posture tied to customer exit policy | Operator, security reviewer, compliance reviewer | Evidence links must remain even when summaries are redacted | Required before runtime expansion |
| Guardian decisions | `internal` to source data class | Evidence-retained placeholder | Redact reason text and resource summaries | Export decision metadata, policy refs, and redacted reasons | Delete eligibility unresolved when tied to security evidence | Security reviewer, compliance reviewer | Required for audit chain | Required before runtime expansion |
| Approval requests/results/tokens/verifications | `internal` to `customer_confidential` | Evidence-retained placeholder | Redact reasons; never store token material | Export request/result/token metadata only | Expired/revoked metadata retention unresolved | Operator, approver, security reviewer | Required to prove human decision and token posture | Required before runtime expansion |
| Evidence artifacts | Mixed | Policy decision needed | Redact payload refs and summaries by profile | Export redacted package with integrity refs | Delete may conflict with evidence preservation | Security reviewer, compliance reviewer | Evidence chain may require preservation exceptions | Required before runtime expansion |
| Worker heartbeat | `internal` | Short operational placeholder needed | Redact host details where needed | Export health metadata and anomaly summaries | Delete/reset posture tied to worker retirement | Operator, supervisor admin, field IT reviewer | Heartbeat anomaly evidence must survive incident review | Draft scaffold |
| Model route records | Matches task/source data class | Policy decision needed | Raw prompts/responses prohibited in records; export refs only | Export route metadata, provider class, local/cloud posture, redacted summary | Delete follows source task/evidence policy | Security reviewer, compliance reviewer | Model route evidence must show no external call when blocked | Required before model runtime |
| Tool invocation records | Matches task/source data class | Policy decision needed | Raw args/output prohibited; artifact refs only | Export tool metadata, decision, scope, and redacted result | Delete follows task/evidence policy | Operator, security reviewer | Evidence required for allow, deny, block, fail | Required before tool runtime |
| Memory access records | Matches memory namespace data class | Policy decision needed | Raw memory prohibited in contract records | Export refs, purpose, delete/export posture, and redacted summary | Delete request process unresolved | Security reviewer, compliance reviewer | Tenant isolation and delete/export evidence required | Required before durable memory |
| Connector trust records | `internal` to connector data class | Policy decision needed | No secrets; redact connector resource names where needed | Export readiness, consent, scope, revocation metadata only | Delete/revoke evidence policy unresolved | Connector owner, security reviewer | Consent and revocation evidence required | Mock/readiness only |
| Worker deployment records | `internal` | Device lifecycle placeholder needed | Redact physical location and asset refs for broad export | Export hardware class, lifecycle, policy/model refs, and evidence refs | Device retirement and cache purge proof unresolved | Operator, field IT reviewer, security reviewer | Enrollment, quarantine, revoke, and retirement evidence required | Draft scaffold |
| LIMA IT handoff records | `internal` to `customer_confidential` | Policy decision needed | Redact diagnostic summaries and target refs | Export read-only diagnostic metadata and denied remediation posture | Delete follows incident/customer exit policy | Field IT reviewer, security reviewer | Must show remediation execution blocked in MVP | Draft scaffold |
| Incident records | Mixed, often sensitive | Policy decision needed | Redact affected subject summaries and sensitive refs | Export incident metadata, containment, evidence, and post-review refs | Delete may conflict with evidence preservation | Security reviewer, compliance reviewer | Incident evidence may require hold placeholder | Required before runtime expansion |

## Redaction Profiles

Initial profile placeholders:

- `metadata_only`: IDs, timestamps, states, and policy refs only.
- `operational_summary`: redacted status and reason summaries.
- `customer_safe_summary`: customer-facing summary with sensitive refs removed.
- `security_review`: security reviewer view with protected refs, not raw secrets.
- `export_redacted`: export package view after redaction review.

## Export Requirements

- Export requires operator approval and compliance/security review when records
  include sensitive classes.
- Export packages must identify included record classes, date range, tenant,
  redaction profile, integrity refs, and exclusions.
- Export packages must not include secret material, raw connector payloads, raw
  prompts, raw model responses, or bearer token material.

## Delete Requirements

- Delete requests require customer context, scope, approver refs, evidence refs,
  and conflict review.
- Evidence preservation conflict is unresolved and must be documented per
  request.
- Device cache purge, worker retirement, connector revocation, and memory delete
  proofs are required before customer exit can be considered complete.

## Access Roles

- Operators may view operational metadata.
- Approvers may view records needed for assigned approval decisions.
- Security reviewers may view security and incident metadata.
- Compliance reviewers may review retention, export, delete, and customer exit
  posture.
- Field IT reviewers may view deployment and health metadata.
- LIMA IT reviewers may view read-only diagnostic handoff metadata only.

## MVP Status

This policy resolves record coverage and default fail-closed posture, but does
not set final legal retention periods. Open retention durations remain visible
in [Open Questions](../OPEN_QUESTIONS.md).
