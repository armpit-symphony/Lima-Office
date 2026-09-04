# Lab 4 Local Form Test Range

Status: approved narrow lab implementation for one attended personal PC.
This contract does not authorize customer data, browser automation, or an
external form submission.

## Purpose

Lab 4 turns the registration curriculum into a complete reviewable workflow:
Arc maps a fixed synthetic record into one of several local form layouts,
identifies gaps, waits for a human decision, asks Guardian to evaluate an
approved mock-submit request, and records a sanitized internal receipt.

## Fixed test range

- 25 built-in fictional records.
- Three localhost form layouts: community program, service intake, and event
  enrollment.
- Reserved `.test` email addresses and fictional `555-01xx` phone numbers.
- Deterministic field validation and scoring; the model does not grade itself.
- Missing or invalid values stay blank and receive `NEEDS_HUMAN_INPUT`.

The layouts use different labels and field order while remaining within the
nine fields defined by the registration practice contract. Unknown fields and
unknown scenarios fail closed.

## Human review and Guardian boundary

Every prepared form stops for an explicit human `approved` or `rejected`
decision. A draft with unresolved fields cannot be mock-submitted.

For an approved complete draft, Guardian receives a structured
`mock_form_submission` request containing only identifiers, counts, fixed
boundary flags, and pre-action evidence references. Guardian permits it only
when all of these are true:

- data is marked synthetic;
- the operator decision is `approved`;
- unresolved issue count is zero;
- the target is exactly `localhost_test_range`;
- execution mode is `mock_only`;
- external effect is `none`;
- pre-action evidence is present.

The allowed result is an internal mock receipt. It does not invoke a browser,
connector, HTTP destination, customer system, or external send. The response
and evidence always state `external_submission_allowed: false` and
`external_side_effects: false`.

Rejected drafts record the human stop without asking Guardian to authorize an
action. Approved incomplete drafts are evaluated and denied by Guardian.
Attempts are single-review: replaying the review fails closed.

## Persistence and evidence

SQLite stores sanitized attempt and review summaries. Review evidence may
contain attempt, scenario, review, Guardian decision, and evidence identifiers;
the operator decision; outcome; issue field names; and boundary flags. It must
not contain fixture values, form contents, or model output.

## Local HTTP surface

- `GET /api/training/registration/catalog`
- `POST /api/training/registration/run`
- `POST /api/training/registration/run-suite`
- `POST /api/training/registration/review`

All POST routes require Training mode. There is no registration submit route.

## Authentication decision

Operator PIN/login work is deferred for this attended personal-PC test. The
server remains bound to `127.0.0.1` and must not be exposed to a LAN, reverse
proxy, shared PC, customer environment, or unattended session. Authentication
remains required before any later shared-device or customer pilot.

## Exit criteria

- All 25 records pass deterministic preparation checks.
- All three layouts render the exact bounded fields.
- A complete approved draft produces one Guardian-allowed internal mock receipt.
- An incomplete approved draft is Guardian-denied.
- A rejected draft records no mock submission.
- Review replay fails closed.
- State and sanitized evidence persist across restart.
- External submission, browser automation, and external side effects remain
  false throughout source and packaged-artifact testing.
