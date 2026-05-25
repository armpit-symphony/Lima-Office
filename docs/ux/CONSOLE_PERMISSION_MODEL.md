# Console Permission Model

This model is a UX permission specification only. It does not implement an
identity provider, role engine, access-control service, or UI.

Canonical contract posture: [RBAC IdP MFA Session Device Trust Matrix](../governance/RBAC_IDP_MFA_SESSION_DEVICE_TRUST_MATRIX.md).

## Role Matrix

| Role | View permissions | Approve permissions | Deny permissions | Export/delete request permissions | Connector consent permissions | Worker quarantine/re-enrollment permissions | Update/rollback permissions | LIMA IT diagnostic/remediation permissions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| owner/operator | View all tenant-scoped operational metadata | Approve low/medium items only when not requester and policy allows | Deny assigned or visible requests | Request export/delete review; cannot bypass compliance review | Request consent/revocation review; cannot approve scope expansion alone | Request quarantine/re-enrollment; release requires reviewer where applicable | Request review; cannot execute update | View/request read-only diagnostics; remediation execution blocked |
| approver | View assigned approval context and evidence | Approve assigned approval requests within role and scope | Deny assigned requests | No direct export/delete approval unless separately assigned | No connector approval unless assigned | No direct worker release unless assigned | Approve assigned update/rollback metadata only | May deny remediation request metadata; execution blocked |
| field_it | View deployment, worker, health, update, LIMA IT diagnostic metadata | Approve field-readiness metadata when not requester | Deny field-readiness or update metadata | View exit records affecting devices; cannot approve delete alone | View connector impact during exit; cannot approve live connector | Request quarantine; approve field re-enrollment checks; security release separate | Review update/rollback metadata; no automatic update | View diagnostics; cannot approve own remediation recommendation |
| auditor_readonly | View redacted evidence, decisions, incidents, governance, and export metadata allowed by policy | None | None | View export/delete status only | View connector status only | View worker state only | View update status only | View handoff status only |
| worker_owner | View owned worker deployment/health metadata | None for high-risk actions | May request denial/cancel of owned worker action | None | None | Request quarantine/re-enrollment; cannot self-release security quarantine | Request review for owned worker; cannot approve | View related diagnostics only |
| security_reviewer | View security, Guardian, evidence, incident, governance, connector, worker, and taint metadata | Approve security-scoped reviews when not requester and policy allows | Deny or block high-risk/security requests | Review sensitive export/delete and preservation conflicts | Review connector consent/scope/revocation; live access still blocked | Approve release from security quarantine when separation holds | Review failed attestation/update verification; require rollback | Review remediation request metadata; execution blocked |

## Global Rules

- No self-approval for high-risk actions.
- LIMA IT remediation requires separation of duties and remains blocked or
  request metadata only in MVP.
- Read-only auditor cannot approve, deny, request mutation, export/delete,
  quarantine, re-enroll, or change connector/update posture.
- Breakglass is blocked placeholder-only in MVP.
- Console role display is not authorization; Guardian, policy, approval,
  evidence, and audit refs remain required.
- Missing IdP/MFA, stale access review, missing policy, or ambiguous role
  posture blocks approval-capable UX.
- Untrusted device posture blocks privileged approve/administer controls.

## Fail-Closed Permission States

Show blocked state when:

- Actor role is missing.
- Actor is requester and high-risk approval would be self-approval.
- Approver separation cannot be proven.
- Evidence is missing.
- Guardian decision is missing, expired, denied, or block-MVP.
- Requested action is outside role scope.
- Connector consent is revoked or live access would be required.
- Export/delete posture is missing.
- Worker is quarantined/revoked and release gates are incomplete.
