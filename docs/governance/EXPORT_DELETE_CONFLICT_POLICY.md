# Export Delete Conflict Policy

Policy ref: `policy.export_delete_conflict.phase1a`

Status: Phase 1A docs/contracts/tests hardening only. Not implemented.

## Purpose

Define one fail-closed policy posture for export/delete conflict handling,
retention/redaction placeholders, and customer-exit proof metadata.

## Export/Delete Conflict Model

- Export/delete is modeled as metadata review state, not live execution.
- Conflicts are represented by explicit reason codes and evidence refs.
- Unresolved conflict posture blocks completion states.

## When Export Is Blocked

- Preservation hold is active.
- Retention window is active.
- Redaction status is `pending`, `failed`, or `blocked_mvp`.
- Conflict evidence is missing.
- Tenant/correlation/linkage drift is detected.

## When Delete Is Blocked

- Preservation hold status is `active` or `conflict_with_delete`.
- Export review remains unresolved for `export_and_delete` requests.
- Required delete proof refs are missing.
- Conflict reason codes are present and unresolved.

## When Delete Requires Review

- Any request type `delete` or `export_and_delete`.
- Any request with `sensitive_*` classes.
- Any request with unresolved retention/redaction placeholders.

## Evidence Preservation Conflict Handling

- If preservation and delete conflict, default is deny/block.
- Conflict records must include:
  - conflict reason code(s)
  - conflict evidence refs
  - reviewer refs
  - next review posture

## Redaction Before Export

- Exported metadata requires `redaction_status` of `applied` or
  `not_required`.
- Export manifests remain refs-only and cannot include raw payload fields.

## Delete Proof Placeholder

- Delete-proof fields are placeholders only in this phase.
- A request marked delete-approved must carry `delete_proof_refs` or remain
  blocked/review-required.

## Export Package Placeholder

- `export_package_refs` are metadata placeholders only.
- No package generation, transport, or delivery is implemented.

## Tenant Isolation

- Cross-tenant refs force fail-closed (`cross_tenant_blocked`,
  `mismatched_tenant`, or equivalent blocked status).
- Cross-tenant records cannot be represented as linked/reconciled.

## Approver And Reviewer Requirements

- Requester and reviewer separation is required where policy defines it.
- Single-actor self-approval is blocked for conflict closure.
- Missing reviewer capacity keeps request blocked.

## Evidence Requirements

- Denied/blocked states require evidence refs and reason codes.
- `conflict_detected` states require conflict evidence refs.
- `failed_closed` states require failure reason codes and evidence refs.

## Audit Requirements

- Every state change requires correlation and immutable review metadata.
- Reasons must use canonical taxonomy codes from:
  - [Reconciliation Reason Taxonomy](../taxonomy/RECONCILIATION_REASON_TAXONOMY.md)
  - [Evidence Reason Taxonomy](../taxonomy/EVIDENCE_REASON_TAXONOMY.md)

## Fail-Closed Behavior

- Missing or ambiguous conflict metadata blocks completion.
- `blocked_mvp` cannot represent completed export or completed delete.
- Unknown reason codes fail validation in strict mock tests.

## MVP Acceptance Gates

- Conflicts are representable with canonical reason/evidence fields.
- Redaction and retention placeholders are explicit.
- Refs-only export posture is enforced.
- Denial-path evidence is required for blocked/denied/fail-closed states.

## Non-Goals

- No live export implementation.
- No live delete implementation.
- No legal retention determination.
- No production storage or workflow service implementation.

