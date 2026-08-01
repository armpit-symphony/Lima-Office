# Evidence Viewer Spec

The evidence viewer shows redacted metadata and integrity refs for important
actions and decisions. It does not expose raw secrets, raw customer payloads,
raw connector content, raw prompts, raw model responses, or raw tool output.

## Evidence Artifact Cards

Cards must show:

- Artifact ID.
- Artifact type.
- Actor and subject refs.
- Action class.
- Guardian decision ID.
- Approval request/token refs where applicable.
- Policy snapshot hash.
- Redaction status and profile.
- Retention class and policy ref.
- Storage ref.
- Payload hash and integrity ref.
- Previous artifact ID.
- Export eligibility.
- Access-control ref.
- Summary.

## Hashes And Refs

Hashes and refs are shown as opaque metadata. The viewer does not dereference
protected payloads unless a future policy explicitly defines that behavior.

## Pre-Action Vs Post-Action

- Pre-action evidence proves required review existed before privileged work.
- Post-action evidence records outcome, denial, failure, or degraded state.
- Missing required pre-action evidence blocks the related action.
- Missing post-action evidence creates degraded state and reconciliation review.

## Evidence Failure States

The viewer must show:

- Failure stage.
- Failure code.
- Affected contract/action.
- Emergency spool ref.
- Retry/reconciliation posture.
- Incident/quarantine refs.
- Runbook link.

## Redacted View

Default view is metadata/redacted. Sensitive fields show only refs and redacted
summaries. Role-limited views must show access denied rather than an empty
healthy state.

## Export Eligibility

Export eligibility shows:

- Eligible/not eligible.
- Export redaction profile.
- Non-exportable classes.
- Preservation conflict state.
- Audit/export request refs.

## Retention Class

Retention class and policy ref must be visible. Final legal retention periods
remain unresolved; missing retention policy shows blocked state for export or
delete.

## Access Roles

View access follows [Console Permission Model](CONSOLE_PERMISSION_MODEL.md).
Auditors see redacted metadata only. Approvers see only records needed for
assigned decisions. Security and compliance reviewers see review metadata
needed for their role.
