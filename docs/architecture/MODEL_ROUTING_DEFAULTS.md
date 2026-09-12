# Model Routing Defaults

## Purpose

Define model-routing defaults for LIMA Office OS as contractable policy with
fail-closed behavior. One narrow attended lab route now has execution authority;
all other modes remain metadata-only.

Status: contract-backed; `subscription_lab_readonly` is implemented for the
localhost Supervisor conversation only.

## Model Route Decision Lifecycle

1. Intake route request metadata (`tenant_id`, task, risk, data class, taint,
   role/session/device posture, approval requirement).
2. Evaluate policy defaults and blocked-MVP classes.
3. Classify route mode and route status.
4. Write pre-action evidence and evaluate Guardian.
5. Stop for every mode except an allowed `subscription_lab_readonly` route.
6. For that route only, run one ephemeral read-only text turn and write
   post-action evidence before returning the response.

## Route Modes (MVP)

- `mock_only`
- `local_planned`
- `subscription_planned`
- `subscription_lab_readonly`
- `blocked_mvp`

`local_planned` and `subscription_planned` are planning postures only; they do
not authorize execution. `subscription_lab_readonly` is limited to attended,
low-risk Supervisor reasoning over public or non-sensitive internal text.

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
- `subscription_lab_readonly`: one explicit, ephemeral text turn through the
  operator's saved ChatGPT/Codex session, with read-only sandbox, user config,
  rules, web search, tools, memory, helpers, fallback, and Arc dispatch disabled.
- `blocked_mvp`: explicit deny/block metadata when policy, taint, risk, trust,
  or MVP boundaries are violated.

No local inference runs are permitted in this lane. External provider use is
permitted only by the narrow lab route above and never authorizes a side effect.

## Fail-Closed Rules

- Unknown route mode, role, risk, taint, or trust posture => blocked.
- Missing policy/evidence refs for selected/degraded route => blocked.
- High-risk route without approval requirement => blocked or denied.
- Untrusted device/session/RBAC posture for privileged route => blocked.
- Failed/expired attestation or untrusted update metadata => blocked.
- Blocked-MVP classes cannot be selected.
- Any missing lab restriction, sensitive/tainted input, fallback request,
  non-Supervisor role, or non-attended request => denied before invocation.
- Pre-action or Guardian evidence failure => no invocation. Post-action evidence
  failure => response withheld.

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
- `subscription_lab_readonly` cannot accept privileged/high-risk work or act as
  an approval, helper, worker, connector, or tool authority.

## Evidence and Audit Requirements

Route records must include:

- route decision metadata and reason codes
- policy refs
- evidence refs
- tenant/correlation IDs
- trust posture references (RBAC/session/device) when relevant
- attestation appraisal/result references for privileged routes
- attestation lineage/authority/revocation propagation refs when present

Lineage or authority conflict reason codes (for example
`attestation_lineage_revoked`, `attestation_revocation_pending`,
`attestation_revocation_not_propagated`, `verifier_authority_conflict`,
`model_route_selected_with_untrusted_lineage`) must map to `denied`,
`blocked_mvp`, or `unavailable`, never `selected`.

Drift-class posture for these cases is defined in
[ATTESTATION_REVOCATION_RECONCILIATION_DRILLS](../ATTESTATION_REVOCATION_RECONCILIATION_DRILLS.md).

## Implemented Lab Acceptance Gates

1. Contract and taxonomy conformance pass with zero warnings/failures.
2. Explicit fail-closed tests for taint, risk, trust, fallback, and blocked-MVP
   paths.
3. Runbook coverage for degraded/blocked route review.
4. Live-provider coverage proves read-only/ephemeral configuration, zero tool
   events, explicit confirmation, no raw-content evidence persistence, and
   fail-closed evidence behavior.
5. Local inference, helpers, worker dispatch, connectors, and side effects
   remain outside this route.
