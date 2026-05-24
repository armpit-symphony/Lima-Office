# Reconciliation Reason Taxonomy

Status: Phase 1A metadata-only taxonomy. Not an authorization surface.

## Purpose

Define one canonical reason vocabulary for fail-closed reconciliation, linkage
drift detection, and export/delete conflict posture.

## Reason-Code Naming Rules

- Use lowercase snake_case.
- Prefix families for clarity:
  - `recon_` for reconciliation flow reasons
  - `linkage_` for cross-contract linkage reasons
  - `evidence_` for evidence completeness/integrity failures
  - `export_delete_` for governance conflict outcomes
  - `blocked_mvp_` for MVP hard blocks
- Codes are stable identifiers. Wording can evolve, code IDs cannot.

## Severity And Status Mapping

- `info`: review-required metadata, no direct authorization semantics.
- `warn`: degraded metadata, requires operator review.
- `deny`: fail-closed deny path.
- `blocked_mvp`: policy hard block in MVP.

Mapping:

- `reconciled` -> `info`
- `missing_ref`, `mismatched_binding`, `replay_mismatch`,
  `evidence_missing`, `coordinator_mismatch`, `stale_decision` -> `deny`
- `cross_tenant_blocked`, `blocked_mvp` -> `blocked_mvp`

## Actor-Visible Vs Internal Categories

- Actor-visible:
  - `recon_missing_guardian_decision`
  - `recon_stale_guardian_decision`
  - `recon_mismatched_approval_binding`
  - `recon_mismatched_token_verification`
  - `recon_replay_record_missing`
  - `recon_replay_record_mismatch`
  - `recon_evidence_ref_missing`
  - `recon_coordinator_event_mismatch`
  - `recon_cross_tenant_linkage`
  - `blocked_mvp_authorization_attempt`
- Internal (diagnostic):
  - `linkage_missing_ref`
  - `linkage_mismatched_tenant`
  - `linkage_mismatched_scope`
  - `linkage_mismatched_nonce`
  - `linkage_drift_detected`
  - `linkage_blocked_mvp`

## Canonical Reconciliation Status Values

- `reconciled`
- `missing_ref`
- `mismatched_binding`
- `stale_decision`
- `replay_mismatch`
- `evidence_missing`
- `coordinator_mismatch`
- `cross_tenant_blocked`
- `blocked_mvp`

## Canonical Linkage Failure Reasons

- `linkage_missing_ref`
- `linkage_mismatched_tenant`
- `linkage_mismatched_scope`
- `linkage_mismatched_nonce`
- `linkage_drift_detected`
- `linkage_blocked_mvp`

## Canonical Evidence Failure Reasons

- `evidence_ref_missing`
- `evidence_chain_parent_missing`
- `evidence_chain_tenant_mismatch`
- `evidence_raw_content_blocked`
- `evidence_secret_material_blocked`
- `evidence_failed_closed_required`

## Canonical Export/Delete Conflict Reasons

- `export_delete_conflict_active`
- `export_delete_preservation_hold_active`
- `export_delete_retention_window_active`
- `export_delete_review_required`
- `export_delete_blocked_mvp`

## Canonical Denial Evidence Reasons

- `denial_replay_denied`
- `denial_stale_decision`
- `denial_expired_decision`
- `denial_scope_mismatch`
- `denial_tenant_mismatch`
- `denial_token_binding_mismatch`
- `denial_blocked_mvp`

## Blocked-MVP Reason Codes

- `blocked_mvp_external_send`
- `blocked_mvp_live_connector_access`
- `blocked_mvp_lima_it_remediation`
- `blocked_mvp_export_delete_execution`

## Tenant-Isolation Reason Codes

- `tenant_mismatch`
- `customer_context_mismatch`
- `cross_tenant_linkage_blocked`
- `cross_tenant_evidence_ref_blocked`

## Replay/Nonce Reason Codes

- `nonce_replayed`
- `nonce_missing`
- `nonce_scope_mismatch`
- `replay_record_missing`
- `replay_record_mismatch`

## Token/Binding Reason Codes

- `approval_binding_mismatch`
- `token_verification_mismatch`
- `approval_chain_mismatch`
- `binding_scope_mismatch`

## Guardian Decision Reason Codes

- `guardian_decision_missing`
- `guardian_decision_stale`
- `guardian_decision_expired`
- `guardian_decision_scope_mismatch`
- `guardian_decision_blocked_mvp`

## Evidence Ledger Reason Codes

- `ledger_parent_missing`
- `ledger_chain_position_mismatch`
- `ledger_artifact_ref_missing`
- `ledger_cross_tenant_mismatch`
- `ledger_failed_closed`

## Export Manifest Reason Codes

- `export_manifest_refs_only_required`
- `export_manifest_redaction_required`
- `export_manifest_conflict_evidence_required`
- `export_manifest_raw_content_blocked`
- `export_manifest_secret_material_blocked`

## Deprecation And Versioning Rules

- Additive code additions require taxonomy minor version bump.
- Semantic code meaning changes require taxonomy major version bump.
- Deprecated codes stay accepted for one major cycle and map to canonical
  replacements in compatibility notes.
- Unknown codes fail validation in strict mock tests.

## MVP Non-Goals

- No live export service.
- No live delete service.
- No legal retention determination.
- No production reconciliation engine.

