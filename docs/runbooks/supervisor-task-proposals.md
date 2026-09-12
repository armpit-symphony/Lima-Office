# Supervisor Synthetic Task Proposal Runbook

## Purpose

Use the attended `/office` console to turn one completed fixed synthetic Office
Helper review into a durable, reviewable task proposal. This runbook does not
authorize approval tokens, Arc dispatch, tools, connectors, form submission, or
customer-data work.

## Preconditions

- The localhost lab harness is running and `/office` reports the Supervisor and
  Office Helper ready.
- The operator is working only with one of the five fixed synthetic registration
  scenarios.
- No customer, credential, HR, finance, legal, medical, or other sensitive data
  is entered.

## Attended Procedure

1. In **Supervisor**, select a fixed scenario, check the synthetic-review
   confirmation, and run the Office Helper review.
2. Inspect its findings, Guardian decision, and completion-evidence reference.
3. Select **Create task draft from this review**. One helper result may create
   only one proposal.
4. In **Work**, optionally change priority between `low` and `normal` and select
   at least one of the three fixed review steps. Select **Save draft**.
5. Select **Propose for owner decision** when the draft is ready.
6. Select **Accept for future approval**, **Deny**, or **Cancel**.

Every button press is an explicit foreground action. Reload before retrying if
the UI reports a revision conflict.

## Expected Evidence

Each successful proposal mutation records:

- a sanitized request event;
- a Guardian authorization event; and
- an atomic completion event stored with the new proposal revision.

Evidence contains IDs, state, revision, reason code, and safety posture. It does
not contain the synthetic registration profile or free-form business content.

## Fail-Closed Conditions

Stop and inspect the evidence/log output if any of these occurs:

- missing or stale revision;
- invalid priority, step identifier, state transition, or confirmation;
- duplicate proposal for a helper result;
- Guardian denial or invalid decision contract;
- request, Guardian, or atomic completion-evidence write failure;
- any record claiming an approval token, worker assignment, Arc dispatch,
  model/tool/connector use, form submission, or external side effect.

## Meaning Of Acceptance

`accepted_for_future_approval` means the owner accepted the plan for a later,
separate approval-request workflow. It is not an approval result and cannot be
used as execution authority. No Arc worker receives the proposal in this
milestone.

## Recovery

Task proposals are stored in the harness SQLite state and should survive a
normal harness restart. If a state change fails, reload the Work view. Do not
manually edit the database or retry with broadened values. Export diagnostics
before destructive support action; resetting synthetic history is a separate
Guardian-gated support path.
