# Retention And Redaction Matrix

## Purpose

Define Phase 0 retention, redaction, export, delete, and access placeholders for LIMA Office records. This matrix is not a legal or compliance claim. Unknown values remain policy decisions needed before runtime.

## Policy Metadata

- Policy ref: `policy.retention_redaction.phase0`
- Version: `policy-phase0-v1`
- Status: Draft scaffold.
- Owner role: Compliance reviewer.
- Applies to contracts: all v1 contracts with data classification, retention, redaction, export, delete, or evidence fields.
- Evidence artifact types: `evidence_artifact`, `memory_access`, `tool_invocation`, `model_route`, `connector_trust`, `incident`, `lima_it_handoff`.
- Fail-closed outcome: if retention, redaction, export, or delete posture is unclear for sensitive data, block durable writes and external export.
- Runbook: customer exit/delete runbook needed before runtime.

## Must Not

- Do not store plaintext secrets, raw connector payloads, raw prompts, raw tool output, or unredacted sensitive customer content in policy records or evidence summaries.
- Do not export data across tenants.
- Do not mark retention, export, or delete behavior as complete while the row says policy decision needed.
- Do not treat this matrix as a legal compliance or certification claim.

## Matrix

| Record type | Data class | Default retention placeholder | Redaction requirement | Export requirement | Delete requirement | Access role | MVP status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Task metadata | `internal` to `customer_confidential` | Policy decision needed | Redact raw customer payloads and tool inputs | Export metadata and evidence refs only | Delete or customer-exit posture needed | Operator, supervisor admin | Required before runtime |
| Guardian decisions | `internal` to `customer_confidential` | Evidence-retained placeholder | Redact resource details when sensitive | Export decision metadata and policy refs | Retain unless customer-exit policy says otherwise | Operator, security reviewer | Required before runtime |
| Approval requests/tokens | `internal` to `customer_confidential` | Evidence-retained placeholder | Redact reason text if it includes sensitive context; never store token material | Export request/result/token metadata only | Expired/revoked token metadata retention decision needed | Operator, approver, security reviewer | Required before runtime |
| Evidence artifacts | Matches source action | Evidence-retained placeholder | Use `metadata_only`, `payload_redacted`, or `secret_redacted` | Export redacted summaries and artifact refs | Delete eligibility policy needed | Operator, security reviewer, compliance reviewer | Required before runtime |
| Worker heartbeat | `internal` | Short operational placeholder | Redact host/user details if collected later | Export health summary only | Delete after operational window policy needed | Operator, field IT reviewer | Required before runtime |
| Model route records | `internal` to `customer_confidential` | Evidence-retained placeholder | Raw prompts and outputs prohibited; use refs | Export route class, policy, and evidence refs | Delete prompt/response refs by source policy | Operator, security reviewer | Required before runtime |
| Tool invocation records | Matches tool target | Evidence-retained placeholder | Raw args/stdout/stderr prohibited; use refs and summaries | Export scoped tool metadata and outcome | Delete target payload by source policy | Operator, security reviewer | Required before runtime |
| Memory access records | `internal` to sensitive classes | Policy decision needed | Raw memory content prohibited; record refs only | Export access metadata and record refs | Delete/export posture required before durable memory runtime | Operator, compliance reviewer | Required before runtime |
| Connector trust records | `internal` to `customer_confidential` | Evidence-retained placeholder | No OAuth tokens, secrets, cookies, or live payloads | Export consent/scope/revocation metadata | Delete connector readiness metadata per exit policy | Operator, security reviewer | Mock/readiness only |
| LIMA IT diagnostic handoffs | `internal` to `customer_confidential` | Evidence-retained placeholder | Redact hostnames, usernames, and sensitive diagnostics if present later | Export handoff summary, scope, and evidence refs | Delete diagnostic refs by source policy | Operator, field IT reviewer | Read-only diagnostics only |
| Incident records | `internal` to sensitive classes | Evidence-retained placeholder | Redact customer payloads, secrets, and sensitive user details | Export incident summary, containment, and evidence refs | Delete or retain based on incident and exit policy | Operator, security reviewer, field IT reviewer | Required before runtime |
| Logs | `internal` to sensitive classes if payload refs are included | Policy decision needed | No raw secrets, raw prompts, raw tool output, or customer payloads | Export redacted operational metadata only | Log retention/delete policy needed | Operator, supervisor admin, security reviewer | Required before runtime |
| Worker local cache | Matches cached source | Policy decision needed | Cache contents must not appear in evidence summaries | Export not allowed directly; use source records | Purge-on-revoke/customer-exit policy needed | Field IT reviewer, security reviewer | Required before worker runtime |
| Local emergency evidence spool | `internal` to `customer_confidential` | Short emergency placeholder; policy decision needed | Metadata refs only; no raw payloads | Export only after reconciliation | Delete after reconciliation policy needed | Supervisor admin, security reviewer | Required before evidence runtime |
| Model prompt refs | Matches source content | Source-record retention policy | Raw prompt text prohibited in route records | Export refs and redacted summary only | Delete by source policy | Security reviewer, compliance reviewer | Required before model runtime |
| Model response refs | Matches task output | Source-record retention policy | Raw response prohibited in route records | Export redacted summary only | Delete by source policy | Security reviewer, compliance reviewer | Required before model runtime |
| Audit export packages | Mixed | Policy decision needed | Redacted by audience and data class | Export format policy needed | Delete/export package retention needed | Compliance reviewer, security reviewer | Future policy needed |
| Customer exit/delete records | Mixed | Policy decision needed | Redacted administrative summary | Export/delete proof policy needed | Customer exit/delete policy needed | Compliance reviewer, supervisor admin | Future policy needed |
| Legal/security hold | Mixed | Policy decision needed | Redact payloads unless explicitly authorized by future policy | Export blocked unless future policy defines it | Delete may be paused by future policy | Security reviewer, compliance reviewer | Future policy needed |

## Redaction Requirements

Default redaction posture:

- Store metadata and refs, not raw content.
- Redact or reference raw prompts, model outputs, tool outputs, connector payloads, file contents, and memory content.
- Never store plaintext secrets.
- Mark `redaction_status`, `redaction_profile`, `redacted_fields`, and `export_redaction_profile` where evidence is created.

## Export Requirements

Export requirements are placeholders until an audit/export policy exists.

Minimum future export behavior:

- Tenant-scoped export only.
- Redacted by default.
- Includes contract IDs, evidence artifact IDs, timestamps, actor refs, policy refs, and outcome states.
- Excludes raw secrets, raw sensitive payloads, raw prompts, and raw tool output.

## Delete Requirements

Delete requirements are placeholders until customer exit/delete/reset policy exists.

Minimum future delete behavior:

- Tenant-scoped.
- Evidence-retention exceptions explicitly documented.
- Memory delete/export posture defined before durable memory runtime.
- Worker local cache purge behavior defined before worker runtime.

## Access Roles

Initial access roles:

- Operator.
- Approver.
- Supervisor admin.
- Field IT reviewer.
- Security reviewer.
- Compliance reviewer.

Role mapping remains a policy decision until operator identity is selected.

## Access Role Matrix

| Action | Operator | Approver | Supervisor admin | Field IT reviewer | Security reviewer | Compliance reviewer |
| --- | --- | --- | --- | --- | --- | --- |
| View task/evidence metadata | Yes | Limited to assigned approval | Yes | Limited to diagnostics | Yes | Yes |
| Approve privileged action | Policy decision needed | Yes when assigned | Policy decision needed | LIMA IT review only until policy decides | Security cases only until policy decides | No |
| Export evidence summary | No by default | No | Policy decision needed | No by default | Policy decision needed | Policy decision needed |
| Delete/export review | Request only | No | Policy decision needed | No | Security exception review | Yes |
| Connector scope review | No | No | Policy decision needed | No | Yes | Policy decision needed |
| Quarantine release | Request only | No | Policy decision needed | Field IT causes | Security causes | No |
| LIMA IT handoff review | Request only | No | Policy decision needed | Yes | Incident-related only | No |

This matrix is a planning placeholder. Exact RBAC and identity-provider enforcement remain open before runtime.

## MVP Acceptance Gates

- Every record type has data class, retention placeholder, redaction, export, delete, access role, and MVP status.
- Unknowns are marked as policy decisions needed.
- No legal compliance claim is made.
- Raw secrets and raw sensitive payloads remain prohibited.
