# Model Routing Review

## Purpose

Review model-route metadata for fail-closed routing posture in Phase 1A.

## When To Use

- Route status is `degraded`, `denied`, `blocked_mvp`, or `unavailable`.
- Taint, RBAC/session/device posture, or fallback handling is disputed.
- Policy/evidence linkage is missing or ambiguous.

## Review Triggers

- New model-route reason code appears.
- High-risk route lacks approval requirement.
- `fallback_allowed=true` without complete fallback metadata.
- Planned local/subscription mode appears to imply live execution.
- `subscription_lab_readonly` is selected without every mandatory restriction.

## Review Steps

1. Confirm route domain/status/reason codes and taxonomy version.
2. Verify route mode is one of: `mock_only`, `local_planned`,
   `subscription_planned`, `subscription_lab_readonly`, `blocked_mvp`.
3. Verify only `subscription_lab_readonly` implies a provider call and that it
   is an attended, low-risk `supervisor_reasoning` turn over public or internal
   non-sensitive text.
4. Validate taint posture and privileged-path blocking.
5. Validate RBAC/session/device refs for privileged route attempts.
6. Confirm evidence refs and policy refs are present for selected/degraded
   paths.
7. Confirm runbook and operator alert links are present.

## Tainted Input Review

- For tainted privileged requests, confirm route status is denied/blocked.
- Confirm denial/block reason includes taint-oriented reason code(s).

## Privileged Route Review

- Confirm `approval_required=true` for high-risk paths, or blocked result.
- Confirm untrusted session/device/RBAC posture blocks privileged route.

## Local/Subscription Placeholder Review

- `local_planned` and `subscription_planned` must remain metadata-only.
- `provider_ref` and `local_model_bundle_ref` must remain placeholder refs.
- For `subscription_lab_readonly`, verify saved ChatGPT auth, read-only sandbox,
  ephemeral session, no user config/rules, no web/tools/memory/helpers/fallback,
  no Arc dispatch, explicit operator confirmation, and zero tool events.
- Verify pre-action and Guardian evidence exist before invocation and
  post-action evidence exists before response release.
- Evidence may contain hashes, lengths, IDs, classifications, and posture only;
  it must not contain raw owner or model text.

## Evidence To Capture

- route record ID and correlation ID
- policy refs used
- evidence refs linked
- reason codes and status transition notes

## Escalation

- Escalate to security reviewer when taint/risk posture conflicts with status.
- Escalate to architecture reviewer on schema or contract drift.

## Done Criteria

- Route outcome is fail-closed and consistent with policy.
- Evidence/policy/taxonomy fields are complete.
- Any live behavior is confined to the exact read-only subscription lab route;
  all side effects remain denied.
