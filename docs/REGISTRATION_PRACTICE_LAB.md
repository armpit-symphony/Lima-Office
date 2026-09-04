# Registration Practice Lab Contract

Status: lab-only runtime contract for the attended LIMA Office + Arc preview.
It is not a production connector, browser driver, or customer-data workflow.

## Purpose

The practice lab lets an operator teach and test Arc against repeatable,
built-in registration scenarios without accessing a real website or using real
personal information. The lab measures whether Arc can map supplied values,
identify missing or invalid values, and stop at human review.

## Trust boundary

- All scenario values are fixed synthetic fixtures shipped with the source.
- Synthetic emails use the reserved `.test` domain and phone numbers use the
  fictional `555-01xx` range.
- No file, connector, browser, or non-loopback network capability is exposed.
- Form submission is always disabled and `submission_allowed` is always false.
- The local model may draft an SOP through the existing Guardian decision and
  single-use LIMA grant path. It never determines the practice score.
- The deterministic practice engine owns field mapping, validation, scoring,
  and the submit denial.

## Practice fields

The bounded form contains:

- `full_name`
- `email`
- `phone`
- `address_line1`
- `city`
- `state`
- `postal_code`
- `preferred_contact`
- `consent_to_contact`

Unknown fields are rejected. Missing or invalid input is rendered as an empty
form value plus a `NEEDS_HUMAN_INPUT` issue. The engine must never invent a
replacement value.

## Scenario and attempt contract

The catalog exposes a small fixed curriculum covering complete input, missing
contact information, invalid postal data, and absent contact consent. Each
practice attempt returns:

- the selected synthetic scenario identifier and title;
- the prepared mock-form fields;
- field issues and deterministic checks;
- a score and pass/fail result;
- `synthetic_data_only: true`;
- `submission_allowed: false`;
- `external_side_effects: false`;
- an attempt ID and evidence reference.

Passing means every valid supplied value was copied exactly, every expected
missing or invalid field was flagged, no unexpected issue was introduced, and
the submission boundary remained blocked. A suite passes only when every
scenario passes.

## Persistence and evidence

SQLite stores only sanitized attempt summaries: attempt ID, scenario ID,
score, pass/fail state, issue field names, and timestamps. Harness evidence may
record counts, identifiers, scores, and boundary flags. Raw fixture values and
model drafts are not written to evidence events.

## HTTP surface

The localhost harness adds three training-only routes:

- `GET /api/training/registration/catalog`
- `POST /api/training/registration/run`
- `POST /api/training/registration/run-suite`

Both POST routes fail closed outside training mode. None of these routes can
submit a form, authorize working-mode execution, or grant a browser capability.

## Explicitly out of scope

- Real customer or employee information.
- Authentication to third-party sites.
- Browser automation or connector access.
- CAPTCHA handling.
- Saving to or modifying a customer system.
- Automatic form submission.
- Model fine-tuning or weight updates.

"Training" in this lab means reviewed SOP instruction plus repeatable practice
and measured evidence. It does not mean modifying the Qwen model weights.
