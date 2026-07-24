# Export Delete Conflict Review

## Purpose

Provide operator/reviewer steps for metadata-only export/delete conflict review
in Phase 1A.

## When To Use

- Export request includes delete scope.
- Delete request conflicts with preservation hold or retention posture.
- Export/delete review enters denied, blocked, or failed-closed status.

## Preconditions

- Tenant and customer context confirmed.
- Request and correlation IDs present.
- Required reviewer roles assigned.
- Conflict evidence refs available.

## Triggers

- `export_review_status: review_required|denied|failed_closed|blocked_mvp`
- `delete_review_status: review_required|denied|conflict_detected|blocked_mvp`
- `preservation_hold_status: active|conflict_with_delete`
- `linkage_status != linked` for export/delete records

## Review Steps

1. Validate tenant/correlation/linkage consistency across request, manifest,
   and audit records.
2. Validate reason codes against canonical taxonomy.
3. Validate conflict evidence refs and denial evidence refs are present.
4. Validate redaction/retention placeholders are present before export-ready
   status.
5. Validate delete-proof placeholders for any approved delete posture.
6. Set terminal metadata state: review_required, denied, blocked_mvp, or
   failed_closed.

## Approval Requirements

- Export/delete conflict closure requires reviewer separation.
- If separation is unavailable, keep state blocked and escalate.

## Evidence To Capture

- Request and review IDs
- Correlation ID
- Reason code(s)
- Conflict evidence refs
- Reviewer refs
- Denial or failed-closed evidence refs

## Redaction/Export Checks

- Export remains refs-only.
- `raw_content_included` and `secret_material_included` remain `false`.
- Exported states require `redaction_status` of `applied` or `not_required`.

## Delete Conflict Handling

- Active preservation hold blocks delete completion.
- Unresolved conflict remains denied/blocked with next-step evidence.

## Escalation

- Escalate to security/compliance reviewer for unresolved conflict or
  cross-tenant drift.
- Escalate to incident workflow when evidence is missing for denied paths.

## Done Criteria

- Final review status is explicit and fail-closed.
- Reason codes and evidence refs are complete.
- No live export/delete action was attempted.

