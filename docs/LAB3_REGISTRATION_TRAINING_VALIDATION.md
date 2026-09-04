# Lab 3 Registration Training Validation

Validation date: 2026-09-03 (America/New_York)

Status: source and packaged-artifact validation complete; prerelease
publication requires explicit approval of the final public assets.

## Training performed

- Started one attended Supervisor plus one Arc worker on `127.0.0.1:8766`.
- Enabled loopback Ollama `qwen2.5:7b` with separate Supervisor and Arc opt-ins.
- Ran the full fixed synthetic registration curriculum.
- Generated a registration-preparation SOP draft through Guardian, a single-use
  LIMA grant, and the Arc local-model executor.
- Prepended the mandatory no-invention, missing-data, consent, human-review,
  no-browser, and no-submit rules.
- Saved one operator-directed reviewed instruction for
  `registration-form-preparation-v1`.
- Stopped and restarted the harness against the same SQLite state directory.

## Results

- UI HTTP status: 200.
- Registration practice panel present: yes.
- Submit control disabled: yes.
- Synthetic scenarios: 5.
- Passed: 5.
- Failed: 0.
- Average deterministic score: 100%.
- Guardian decision recorded for model draft: yes.
- LIMA decision recorded for model draft: yes.
- Draft and save evidence references recorded: yes.
- Reviewed SOP instruction persisted after restart: yes.
- Five attempt summaries persisted after restart: yes.
- Browser automation performed: no.
- Form submission performed: no.
- External side effects performed: no.

## Packaged-artifact validation

The `0.1.0-lab.3` ZIP built from the merged Office commit was extracted and
installed into fresh Windows directories. The installer verified the exact
Arc, Guardian, and LIMA pins. The packaged smoke suite passed. The installed
UI then repeated all five scenarios at 100%, generated and saved the guarded
registration SOP, stopped, and restarted from the same SQLite state.

The trained packaged installation is running attended on `127.0.0.1:8766`.
It reports five passed practice attempts, zero failed attempts, one instructed
SOP, local model ready, submission disabled, browser automation disabled, and
external side effects false.

## Scenario coverage

1. Complete fictional contact record.
2. Missing fictional phone number.
3. Invalid fictional email.
4. Invalid fictional postal code.
5. Contact consent not granted.

## Evidence posture

Practice persistence contains scenario IDs, pass/fail values, scores, issue
field names, timestamps, attempt IDs, and evidence references. It does not put
fixture field values or model draft text into evidence event payloads.

## Remaining boundary

This proves a local synthetic preparation-and-review curriculum. It does not
authorize real personal information, third-party authentication, browser
automation, connector access, customer-system mutation, or form submission.
The localhost UI remains unauthenticated and attended-only.
