# Supervisor Tokenless Approval Preview Runbook

## Purpose

Use the attended `/office` console to inspect what a future approval request
would need without creating an `approval.request`, approval result, binding,
nonce, replay record, token, worker assignment, Arc dispatch, or external
effect.

## Preconditions

- The localhost lab harness and Supervisor console are running.
- A synthetic task proposal is in `accepted_for_future_approval` state.
- The proposal still matches its stored revision and content hash.
- No customer or free-form data is involved.

## Attended Procedure

1. Open **Work** and locate an accepted-for-future-approval proposal.
2. Select **Create tokenless approval preview**.
3. Open **Approvals** and inspect:
   - exact source-proposal revision;
   - allowed plan-review operation;
   - prohibited execution operations;
   - no external effect and zero token uses;
   - required future owner identity binding and fresh intent;
   - 15-minute review window;
   - source-current status.
4. Select one explicit terminal action:
   - **Mark reviewed — no authority**;
   - **Deny preview**; or
   - **Withdraw preview**.

## Meaning Of Review

`reviewed_no_authority` records only that the operator inspected the preview.
It is not an approval decision and cannot be promoted silently. A future real
approval request must recheck Guardian, the source proposal revision, verified
approver identity, fresh intent, expiry, scope binding, and single-use token
requirements.

## Evidence

Each successful preview mutation writes a sanitized request event and Guardian
authorization event, then atomically commits the preview revision with its
completion event. Evidence contains IDs, revisions, state, reason code, and
safety posture—not registration profiles or free-form content.

## Fail-Closed Conditions

The preview change must stop without authority if:

- the proposal is not `accepted_for_future_approval`;
- the proposal or preview revision is stale;
- the source proposal hash no longer matches;
- a duplicate preview already exists for the proposal;
- the 15-minute review window expired before **Mark reviewed**;
- confirmation, Guardian authorization, contract validation, or evidence fails;
- any record claims a real approval request/result, identity binding, token,
  replay record, worker assignment, Arc dispatch, model/tool/connector use,
  submission, or external effect.

Expiry is evaluated on explicit state load or action; there is no background
poller or hidden state transition. An expired preview may still be denied or
withdrawn, but it cannot be marked reviewed.

## Recovery

Approval previews are stored in the harness SQLite state and should survive a
normal restart. Reload the console after a revision conflict. Do not modify the
database or reinterpret a reviewed preview as execution authority.
