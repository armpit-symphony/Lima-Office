# Attended Lab Pending Approval Request Runbook

## Purpose

Use the localhost LIMA Office console to bind the current personal-PC session
and create a durable synthetic form-review request. The request may then be
closed with a non-authorizing deny, original-requester cancel, or explicit
expiry record. This runbook never approves, dispatches, or executes work.

## Preconditions

- Run the attended harness on loopback and open `/office`.
- Use only the fixed synthetic registration workflow.
- Create and accept a task proposal, create its tokenless preview, and mark the
  preview **reviewed — no authority** before its 15-minute expiry.
- Confirm Guardian and evidence storage are healthy.

## Procedure

1. In **Approvals**, select **Bind this Windows session**.
2. Confirm the UI reports **Bound for this process** and
   `personal_pc_attended_lab` assurance.
3. Verify the UI says no PIN/password was collected and the binding is not
   production identity or an approval.
4. On the reviewed preview, select **Create pending approval request**.
5. Verify the request reports `pending_review`, result `pending`, external effect
   `none`, operation `review_prepared_form_plan`, and a 15-minute expiry.
6. Choose one terminal test outcome:
   - **Deny request** while any attended session is active.
   - **Cancel my request** only while the original creating session remains
     active.
   - After the request TTL, **Record expiry** explicitly; do not expect an
     automatic background transition.
7. Verify the card shows `denied`, `cancelled`, or `expired` and a separate
   result ID/reason while approval token, binding, worker, and dispatch remain
   absent.
8. Refresh manually and confirm the terminal request/result remains visible.

## Expected Evidence

- `operator_session_binding_requested`
- `operator_session_binding_committed`
- `office_pending_approval_request_creation_requested`
- `office_pending_approval_request_guardian_required_review`
- `office_pending_approval_request_created`
- `office_non_authorizing_approval_decision_requested`
- `office_non_authorizing_approval_decision_guardian_allowed`
- `office_non_authorizing_approval_decision_recorded`

Evidence must contain only pseudonymous IDs, hashes, state, and safety posture;
it must not contain the raw OS username, registration profile data, credentials,
or secret material.

## Fail-Closed Checks

Request creation must fail when confirmation is missing, the preview is not
reviewed or has expired, the exact preview/proposal revision or hash changed,
the session is absent/expired/from another tenant, Guardian does not return
`requires_approval`, evidence fails, or a request already exists for that
preview. After a process restart, bind a new session; the prior session must not
restore even though the pending request remains durable.
A decision must also fail for an unknown or positive action, missing fixed
confirmation, stale request hash, non-pending request, wrong tenant, duplicate
result, deny/cancel after TTL, expiry before TTL, inactive session, or cancel
from a replacement session. Deny/cancel fail if their proposal/preview source
changed. The request update, result, and completion event must roll back as one
unit if the atomic commit fails.

## Authority Check

Treat any positive/partial-approved result, approved scope, token,
approval/execution binding, token verification, replay record, worker
assignment, Arc dispatch, connector use, form submission, or external side
effect as a release-blocking defect. A negative terminal result is expected;
all authority-bearing values remain null or false and requested `max_uses` is
zero.

## Next Gate

Design the positive-approval readiness gate: production-grade approver identity,
role/separation-of-duties enforcement, narrowed-scope semantics, and single-use
authority lifecycle. Do not enable positive approval, token issuance, execution
binding, or Arc dispatch until that design is approved and validated.
