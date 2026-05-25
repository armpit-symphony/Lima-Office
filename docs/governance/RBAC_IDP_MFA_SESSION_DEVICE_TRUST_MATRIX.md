# RBAC / IdP / MFA / Session / Device Trust Matrix

## Purpose

Define a Phase 1A governance matrix for operator identity, approver identity,
worker/service identity, session trust, device trust, and role-based
permissions for LIMA Office OS.

Status: design and contract posture only. No IdP, OAuth/OIDC/SAML provider,
MFA provider, session runtime, or device posture runtime is implemented.

## Standards Alignment

- NIST SP 800-63-4 concepts: identity assurance, authenticator assurance,
  federation assurance are represented as contract metadata requirements.
- NIST SP 800-207 Zero Trust: subject and device trust must be evaluated before
  privileged access decisions.
- CISA Zero Trust Maturity Model 2.0: identity, device, application/workload,
  data, visibility, and governance controls are partially represented as
  fail-closed policy metadata scaffolding.
- OWASP ASVS concepts: authentication, session management, access control,
  logging, and evidence linkage are represented as explicit schema fields and
  testable denied/blocked states.

## Identity Actor Types

- `sparkpit_operator`
- `customer_admin`
- `approver`
- `field_it`
- `auditor_readonly`
- `security_reviewer`
- `worker_owner`
- `arc_worker_node`
- `supervisor_service`
- `helper_agent`

Worker/service/helper identities are never treated as human approver identity.

## RBAC Matrix

Permission levels:

- `none`
- `view`
- `request`
- `approve`
- `deny`
- `administer`
- `blocked_mvp`

Action matrix (metadata-only posture):

| Action | Primary allowed roles | Required level | MVP posture notes |
| --- | --- | --- | --- |
| view supervisor health | sparkpit_operator, customer_admin, approver, field_it, auditor_readonly, security_reviewer | view | allowed metadata |
| view worker fleet | sparkpit_operator, field_it, worker_owner, security_reviewer, auditor_readonly | view | allowed metadata |
| onboard worker | sparkpit_operator, field_it | request/administer | manual/runbook metadata |
| quarantine worker | sparkpit_operator, field_it, security_reviewer | request/approve | approval + evidence |
| re-enroll worker | field_it, security_reviewer | request/approve | approval + evidence |
| revoke worker | security_reviewer, sparkpit_operator | approve/administer | approval + evidence |
| view task queue | sparkpit_operator, approver, field_it, auditor_readonly, security_reviewer | view | allowed metadata |
| request approval | sparkpit_operator, customer_admin, worker_owner | request | allowed metadata |
| approve low-risk task | approver, security_reviewer | approve | no self-approval |
| approve privileged task | approver, security_reviewer | approve | MFA step-up + trusted device required |
| deny task | approver, security_reviewer | deny | evidence required on deny path |
| view Guardian decisions | sparkpit_operator, approver, auditor_readonly, security_reviewer | view | allowed metadata |
| view evidence metadata | sparkpit_operator, approver, auditor_readonly, security_reviewer | view | refs-only evidence posture |
| export evidence metadata | security_reviewer, auditor_readonly | request/approve | refs-only export posture |
| request customer export | customer_admin, sparkpit_operator | request | review-required |
| request customer delete | customer_admin, sparkpit_operator | request | review-required |
| approve LIMA IT diagnostic | field_it, security_reviewer | approve | diagnostic metadata only |
| approve LIMA IT remediation | none in MVP | blocked_mvp | blocked or SoD-required metadata only |
| connector consent review | security_reviewer | approve | live connector still blocked |
| connector revocation | security_reviewer | approve/administer | allowed metadata |
| update/rollback approval | field_it, security_reviewer | approve | execution blocked in MVP |
| breakglass request/review | none in MVP | blocked_mvp | breakglass runtime blocked |

`auditor_readonly` must never hold `request`, `approve`, `deny`, or
`administer` permission levels.

## MFA Expectations

- `no_mfa_blocked`: no privileged access.
- `phishing_resistant_preferred`: acceptable for non-privileged review metadata.
- `step_up_required_for_privileged`: required for privileged approve/administer.
- `breakglass_requires_post_review`: metadata-only breakglass placeholder.

## Session Policy

- `session_ttl_placeholder`: runtime value not finalized.
- `idle_timeout_placeholder`: runtime value not finalized.
- `step_up_on_risk`: privileged actions require fresh intent.
- `revoke_on_role_change`: role changes invalidate privileged session posture.
- `revoke_on_device_untrusted`: device trust downgrade invalidates privileged
  session posture.

## Device Trust

- `managed_device_placeholder`: managed posture expected but runtime unresolved.
- `attested_worker_placeholder`: worker attestation metadata required.
- `untrusted_device_readonly_or_blocked`: untrusted devices are view-only or
  blocked.
- `device_posture_required_for_privileged`: privileged approvals require trusted
  posture.

Untrusted device posture cannot approve privileged actions.

## Separation Of Duties

- No self-approval for high-risk actions.
- LIMA IT remediation approver must be separate from requester and executor.
- Export/delete review requires reviewer separation from requester.
- Breakglass remains blocked in MVP and cannot bypass SoD.

## Evidence Requirements

Every privileged or denied/blocked action path must include:

- actor identity refs and role refs
- model-route trust refs (`rbac_context_ref`, `session_policy_ref`,
  `device_trust_ref`, `worker_attestation_ref`, `attestation_result_ref`,
  `appraisal_policy_ref`, `update_rollback_ref`) when route metadata is present
- Guardian decision ref
- policy refs
- evidence refs
- reason codes
- timestamped decision metadata

## Fail-Closed Rules

- Unknown role, action, or permission level blocks action.
- Missing MFA/session/device posture for privileged actions blocks action.
- Untrusted device posture blocks privileged actions.
- Attestation-failed worker posture blocks privileged task metadata.
- Breakglass remains `blocked_mvp`.
- LIMA IT remediation execution remains `blocked_mvp`.
- Missing evidence refs for denied/blocked privileged paths blocks completion.

## MVP Blocked Items

- Real IdP integration.
- OAuth/OIDC/SAML runtime wiring.
- Real MFA provider integration.
- Runtime session issuance/revocation service.
- Runtime device posture attestation engine.
- Runtime RBAC authorization engine.
- Live connector enablement.
- Real remediation execution.

## Acceptance Gates

- Role/action matrix is represented by `governance.rbac_matrix`.
- Session posture is represented by `governance.session_policy`.
- Device trust posture is represented by `governance.device_trust`.
- Attestation trust authority posture is represented by `attestation.authority`.
- Access review runbook captures SoD, MFA, session, and device trust evidence.
- Unknown/ambiguous identity and trust posture fails closed.
