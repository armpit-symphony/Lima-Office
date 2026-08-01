# RBAC / IdP / MFA Access Review

## Purpose

Run a repeatable governance review of role assignments, MFA/session posture,
device trust posture, and separation-of-duties evidence before any privileged
metadata action is accepted.

## When To Use

- Scheduled access review cycles.
- Role changes for approver/security/field IT roles.
- Device trust downgrade or attestation failure.
- Session revocation events.
- Breakglass or LIMA IT remediation review requests.

## Preconditions

- Current policy refs are available.
- Relevant identity/session/device/approval records exist.
- Reviewer and requester are distinct for privileged review.

## Access Review Steps

1. Confirm tenant and customer-context scoping.
2. Validate role assignments against `governance.rbac_matrix`.
3. Validate MFA requirement for privileged actions.
4. Validate session posture and revocation triggers.
5. Validate device trust posture for actor/device pair.
6. Validate worker attestation posture for worker-scoped privileged metadata.
7. Validate separation-of-duties constraints for approval, export/delete, and
   LIMA IT remediation requests.
8. Record denied/blocked reasons and evidence refs for every fail-closed
   decision.

## Role Assignment Review

- Verify least privilege.
- Verify `auditor_readonly` is view-only.
- Verify no implicit elevation from worker/service/helper identities.

## MFA / Session / Device Trust Review

- Privileged approve/administer paths require step-up MFA posture.
- Session role change or untrusted-device events must force revoke posture.
- Untrusted devices are view-only or blocked.

## Separation-Of-Duties Review

- Requester must not approve own high-risk request.
- LIMA IT remediation requester/preparer cannot be sole approver.
- Export/delete reviewer must be independent from requester.

## Evidence To Capture

- role assignment refs
- MFA/session/device trust records
- Guardian decision refs
- policy refs and policy version
- reason codes
- evidence refs for denied/blocked paths

## Escalation

- Escalate to security reviewer for identity ambiguity, role collisions,
  attestation failures, breakglass attempts, and cross-tenant indicators.
- Escalate to compliance reviewer for export/delete/preservation-hold conflicts.

## Done Criteria

- Review outcome is `completed` or `blocked` with explicit reason codes.
- SoD checks are evidenced.
- Privileged paths without MFA/session/device trust are blocked.
- No runtime authorization, IdP wiring, session issuance, or device enforcement
  is introduced.
