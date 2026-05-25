# Model Routing Defaults

## Purpose

Define Phase 1A model-routing defaults for LIMA Office OS as contractable policy
metadata, with fail-closed behavior and no execution authority.

Status: design-only, not implemented.

## Model Route Decision Lifecycle

1. Intake route request metadata (`tenant_id`, task, risk, data class, taint,
   role/session/device posture, approval requirement).
2. Evaluate policy defaults and blocked-MVP classes.
3. Classify route mode and route status.
4. Emit evidence-backed route metadata.
5. Stop. No provider call, no local inference, no side effect.

## Route Modes (MVP)

- `mock_only`
- `local_planned`
- `subscription_planned`
- `blocked_mvp`

`local_planned` and `subscription_planned` are planning postures only; they do
not authorize execution.

## Model Role Categories

- `supervisor_reasoning`
- `worker_draft`
- `worker_classification`
- `it_diagnostic_summary`
- `file_memory_helper`
- `governance_review`

## Routing Inputs

- `tenant_id`
- `task_id`
- `risk_tier`
- `data_class`
- `taint_status`
- `approval_required`
- `rbac_context_ref`
- `session_policy_ref`
- `device_trust_ref`
- `worker_attestation_ref`
- `attestation_result_ref`
- `appraisal_policy_ref`
- `update_rollback_ref`
- `worker_capability_refs`
- provider/local bundle availability placeholders
- cost/capacity placeholders

## Local vs Subscription/Cloud Posture

- `mock_only`: default-safe posture for MVP.
- `local_planned`: future local bundle selection placeholder only.
- `subscription_planned`: future provider class selection placeholder only.
- `blocked_mvp`: explicit deny/block metadata when policy, taint, risk, trust,
  or MVP boundaries are violated.

No external provider calls or local inference runs are permitted in this lane.

## Fail-Closed Rules

- Unknown route mode, role, risk, taint, or trust posture => blocked.
- Missing policy/evidence refs for selected/degraded route => blocked.
- High-risk route without approval requirement => blocked or denied.
- Untrusted device/session/RBAC posture for privileged route => blocked.
- Failed/expired attestation or untrusted update metadata => blocked.
- Blocked-MVP classes cannot be selected.

## Tainted Input Rules

- Tainted privileged route must be `denied` or `blocked_mvp`.
- Suspected taint in privileged paths is treated the same as tainted input.
- Taint may only proceed as metadata review for non-privileged mock work.
- Taint never implies approval to execute route/provider/inference.

## Privileged Task Rules

- Privileged/high-risk route metadata requires `approval_required: true` or
  fail-closed blocked status.
- `subscription_planned` and `local_planned` cannot imply live execution in
  privileged paths.

## Evidence and Audit Requirements

Route records must include:

- route decision metadata and reason codes
- policy refs
- evidence refs
- tenant/correlation IDs
- trust posture references (RBAC/session/device) when relevant
- attestation appraisal/result references for privileged routes

## Acceptance Gates Before Implementation

1. Contract and taxonomy conformance pass with zero warnings/failures.
2. Explicit fail-closed tests for taint, risk, trust, fallback, and blocked-MVP
   paths.
3. Runbook coverage for degraded/blocked route review.
4. No runtime provider wiring, local inference runtime, or authorization
   expansion.
