# Positive Approval Readiness Gate

Status: profile A selected for lab testing; controls remain incomplete
Date: 2026-09-09
Scope: one Supervisor Server, one tenant, and 1-8 Arc workers

## Outcome

LIMA Office is not ready to issue a positive approval result, token, execution
binding, or Arc task. The current attended personal-PC session is sufficient to
create, deny, cancel, and expire synthetic review requests, but it is not a
named production identity, MFA, device trust proof, or approval credential.

The new `approval.readiness` contract records this state without granting
authority. The owner selected profile A on 2026-09-09 for whole-system
synthetic LIMA Office and Arc testing. This closes the profile-selection
question only; it does not authorize positive approval or execution.

## Sparkbot-Derived Lessons

The design is grounded in the local Sparkbot source of truth:

- `backend/app/services/guardian/auth.py` uses hashed operator PINs, constant-
  time verification, failed-attempt lockout, short-lived in-memory privileged
  sessions, and explicit revocation.
- `backend/app/services/guardian/pending_approvals.py` persists short-lived
  confirmation requests, consumes them once, and recursively redacts secret-
  named fields before evidence emission.
- `docs/COMMAND_CENTER_SECURITY_AUDIT.md` requires a policy recheck before an
  approved action executes and identifies privileged/break-glass decisions that
  must never be treated as ordinary approval.

LIMA Office keeps these proven concepts but raises the bar:

- Evidence failure must fail closed; it may not be silently ignored.
- Duplicate request IDs may not overwrite existing records.
- Request, result, token/binding metadata, replay reservation, and evidence must
  have a documented atomic transaction boundary before implementation.
- Approval records are never bearer capabilities. Execution requires Guardian
  to validate the complete current chain immediately before the action.

## Owner Decision Profiles

### A. Attended OS Session — Lab Only

- Identity: current pseudonymous Windows-session binding.
- Step-up: fixed confirmation phrase only; no PIN or MFA.
- Separation: single-owner exception for the fixed synthetic plan-review action.
- Permitted future experiment: positive metadata result only, still with no
  token, worker assignment, Arc dispatch, or external effect.
- Limitation: cannot become a customer or production identity profile.

Use this only if the immediate goal is continued personal-PC lab testing.

### B. Windows Hello Or Passkey — Recommended

- Identity: named local business-owner account.
- Step-up: phishing-resistant Windows Hello or passkey ceremony for each
  positive approval or a maximum five-minute approval session.
- Device: approval bound to the enrolled operator endpoint.
- Separation: documented single-owner exception only for low-risk internal or
  synthetic work; higher-risk and external actions still require a distinct
  approver.
- Fit: practical for a one-owner small business without forcing a shared PIN.

This is the recommended first production-shaped profile.

### C. OIDC MFA And Distinct Approver

- Identity: external identity provider with named accounts and MFA.
- Step-up: phishing-resistant MFA for positive approvals.
- Separation: requester and approver must be distinct human identities.
- Device/session: IdP session plus LIMA device posture and short approval TTL.
- Fit: teams, regulated data, external actions, or customers needing stronger
  audit and lifecycle controls.

This is the strongest profile and requires the most setup and support.

## Gates Required After Profile Selection

The following must be designed and tested before any positive approval runtime:

1. Named human identity and role records with no shared approver accounts.
2. Step-up authentication, TTL, lockout, revocation, and restart behavior.
3. Device-binding posture appropriate to the selected profile.
4. Explicit requester/approver separation or a narrowly documented single-
   owner exception for low-risk actions.
5. Exact requested-scope narrowing; approval can never widen scope.
6. Atomic result, token, binding, nonce reservation, and evidence commit.
7. Durable, tenant-scoped, one-time replay consumption and recovery semantics.
8. Guardian recheck of identity, policy, scope, token, replay, taint, evidence,
   task, and worker immediately before any dispatch or tool call.
9. Revocation propagation, crash recovery, clock-skew, and duplicate-request
   tests.
10. An approval UI that distinguishes normal approval, privileged step-up,
    blocked-MVP actions, and break-glass without ambiguous wording.

## Capabilities That Stay Blocked

- Positive `approval.result` creation
- Approval-token issuance
- Approval/execution binding
- Token verification marked valid
- Nonce/replay consumption
- Worker assignment from approval
- Arc dispatch
- Connector access, form submission, file/network/browser mutation
- External messages or customer-record changes
- Software installation, remediation, production touch, or regulated actions

## Current Decision And Exit Gate

Profile A is active only for attended, synthetic, personal-PC lab testing. Its
runtime projection is visible in the Supervisor Console, but it cannot create a
positive approval result or any execution authority.

After the whole-system LIMA Office and Arc test pass, the next owner decision is
profile B or C. Profile B begins with a passkey/Windows Hello feasibility spike;
profile C begins with identity-provider selection.
