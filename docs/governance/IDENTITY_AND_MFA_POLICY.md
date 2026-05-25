# Identity And MFA Policy

## Purpose

Define the identity and MFA posture required before LIMA Office OS can expand
beyond docs, contracts, and mock runtime scaffolding.

Policy ref: `policy.governance_identity.phase0`

Status: draft scaffold. No identity provider, MFA provider, OAuth wiring, or
runtime enforcement is implemented by this policy.

Companion matrix: [RBAC IdP MFA Session Device Trust Matrix](RBAC_IDP_MFA_SESSION_DEVICE_TRUST_MATRIX.md).

## Operator Identity Assumptions

- Operators are named human users represented by opaque identity refs.
- Shared operator accounts are not acceptable for approval or audit trails.
- Operator identity records must not store credentials, secrets, session
  cookies, or MFA factors.
- Operator role assignment requires evidence and an access review record.

## Approver Identity Assumptions

- Approvers are named human users with explicit approver role assignment.
- Approvers must be distinct from the requester for high-risk actions.
- Approver identity must be present on approval results and audit evidence.
- Approvers cannot use worker identity, service identity, or helper-agent
  identity to approve actions.

## Service Identity Assumptions

- Supervisor, Guardian, worker, helper, connector readiness, and evidence
  writer identities are service identities represented by refs.
- Service identities cannot approve human approval requests.
- Service identity credentials are out of scope for this docs lane and must be
  represented only through `secrets_ref` or identity refs in future contracts.

## Worker Identity Assumptions

- Arc workers use stable `worker_id`, device identity ref, channel identity
  ref, tenant binding, capability manifest hash, and policy bundle refs.
- Worker identity does not imply operator identity.
- Failed or ambiguous worker identity causes quarantine or revoke posture.
- See [Worker Attestation Policy](WORKER_ATTESTATION_POLICY.md).

## MFA Expectations

- MFA is required for operators, approvers, supervisor admins, security
  reviewers, and field IT reviewers before any future approval-required runtime
  behavior is enabled.
- MFA method selection is a policy decision still open.
- Lab mock records may use `mfa_status: required_not_configured` only as a
  blocker, not as trust.
- Breakglass cannot bypass MFA until a future explicit policy defines emergency
  identity proof and post-use review.

## Session Duration Placeholder

- Session TTL is unresolved.
- Future runtime must bind privileged approval actions to fresh operator intent,
  active identity assurance, and evidence.
- Missing, expired, ambiguous, or stale session posture fails closed.

## Device Trust Placeholder

- Operator device trust is unresolved.
- Device trust must not be inferred from network location alone.
- Future policy may require managed device posture, disk encryption, screen
  lock, patch posture, or device certificate refs.

## Least Privilege Roles

Initial roles:

- `operator`: views status, requests allowed low-risk work, starts manual
  reviews.
- `approver`: reviews approval requests within assigned scope.
- `supervisor_admin`: manages Supervisor metadata and status posture.
- `field_it_reviewer`: reviews hardware, OS, network, enrollment, update, and
  rollback readiness.
- `security_reviewer`: reviews security incidents, identity failures,
  quarantine release, taint, connector scope, and breakglass records.
- `compliance_reviewer`: reviews retention, redaction, export, delete, and
  customer exit posture.
- `lima_it_reviewer`: reviews read-only LIMA IT diagnostic handoff metadata.

Workers, helper agents, and service identities are not human roles.

## Access Review Cadence Placeholder

- Cadence is unresolved and remains an open question.
- Quarterly placeholder records may be represented by
  `governance.access_review`.
- Any role with approval, security, export, delete, connector, update, or
  breakglass authority must be reviewed before future runtime expansion.

## Joiner/Mover/Leaver Process

- Joiner: create identity ref, assign least-privilege role, capture evidence,
  require MFA decision, and schedule access review.
- Mover: review old role removal before new role assignment; prevent privilege
  accumulation.
- Leaver: revoke role assignments, close active sessions where applicable,
  revoke approval authority, and capture evidence.
- Orphaned roles or unknown owners fail closed.

## MVP Blocked Areas

- No IdP or MFA integration is implemented.
- No OAuth/provider wiring is added.
- No live connector access is authorized.
- No remediation, production server touch, external sends, or privileged
  runtime action is enabled.
- No compliance certification claim is made.

## Acceptance Gates

- Identity and MFA requirements are represented as policy and contract metadata.
- Role/action matrix is documented in
  [RBAC IdP MFA Session Device Trust Matrix](RBAC_IDP_MFA_SESSION_DEVICE_TRUST_MATRIX.md)
  before runtime expansion.
- Access review records exist for privileged roles.
- Human approval requires a human identity ref and evidence.
- Missing MFA, stale session, ambiguous identity, orphaned role, or unreviewed
  privileged role fails closed.
