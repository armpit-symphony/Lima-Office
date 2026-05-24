# Evidence Reason Taxonomy

Status: Phase 1A metadata-only taxonomy. No payload export/delete execution.

## Purpose

Normalize evidence reason vocabulary across evidence artifact, ledger,
reconciliation, and governance export/delete review records.

## Evidence Types

- `evidence.artifact`
- `evidence.ledger.entry`
- `evidence.failure`
- `evidence.export_manifest`
- `governance.audit_export`
- `governance.export_delete_review` (metadata-only review contract)

## Evidence Intent

- `pre_action`
- `post_action`
- `denial`
- `replay_denial`
- `reconciliation`
- `rollback`
- `export_manifest`
- `delete_review`
- `failed_closed`

## Evidence Status Values

- `recorded`
- `review_required`
- `denied`
- `blocked_mvp`
- `failed_closed`

## Evidence Failure Reasons

- `evidence_ref_missing`
- `evidence_chain_parent_missing`
- `evidence_chain_tenant_mismatch`
- `evidence_hash_missing`
- `evidence_hash_algorithm_missing`
- `evidence_writer_unavailable`
- `evidence_failed_closed_required`

## Evidence Chain Reason Codes

- `chain_parent_missing`
- `chain_previous_hash_missing`
- `chain_position_mismatch`
- `chain_cross_tenant_blocked`
- `chain_drift_detected`

## Redaction Reason Codes

- `redaction_not_required`
- `redaction_required`
- `redaction_pending`
- `redaction_applied`
- `redaction_failed`
- `redaction_blocked_mvp`

## Export Eligibility Reason Codes

- `export_refs_only_required`
- `export_raw_content_blocked`
- `export_secret_material_blocked`
- `export_retention_placeholder_required`
- `export_review_required`

## Delete Conflict Reason Codes

- `delete_conflict_preservation_hold`
- `delete_conflict_retention_window`
- `delete_conflict_open_incident`
- `delete_conflict_unresolved_review`
- `delete_conflict_blocked_mvp`

## No Raw Content / No Secret Material Rules

- `raw_content_included` must remain `false` in MVP evidence/governance
  examples.
- `secret_material_included` must remain `false` in MVP evidence/governance
  examples.
- Ref-only metadata is required for export and reconciliation artifacts.

## Registry Compatibility

Canonical lifecycle and compatibility posture are governed by:

- [Reason Code Registry](REASON_CODE_REGISTRY.md)
- [Reason Code Compatibility Policy](REASON_CODE_COMPATIBILITY_POLICY.md)

Reason-bearing evidence/governance contracts/examples must include
`taxonomy_version`. Missing or unsupported taxonomy versions fail closed in CI.
