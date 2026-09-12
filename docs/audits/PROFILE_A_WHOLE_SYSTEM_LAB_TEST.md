# Profile A Whole-System Lab Test

Date: 2026-09-09
Result: automated current-scope pass; owner-reported primary attended workflow pass
Scope: one LIMA Office Supervisor and 1, 2, or 8 temporary Arc workers on localhost

## Safety Boundary

This report covers the currently implemented synthetic lab surface. It is not a
production-readiness report. Profile A does not establish a named owner
identity, MFA, customer-data authority, positive approval authority, approval
tokens, execution bindings, external submission, or general Arc dispatch.

## Automated Results

- Full regression: 920 passed, 1 skipped. The only warning was the known local
  `.pytest_cache` permission warning.
- Contracts: 85 schemas and 233 examples passed full Draft 2020-12 validation.
- Taxonomy: 627 schema and 337 example reason-code values passed conformance.
- Documentation: 1,147 local links across 187 Markdown files passed.
- Office helper: five fixed synthetic scenarios completed; no model, tool,
  customer profile persistence, Arc dispatch, or external effect occurred.
- Task proposals and approval previews survived store restart without creating
  approval authority.
- Pending approval requests survived restart while attended operator bindings
  correctly did not survive restart.
- Deny, cancel, and expire produced durable non-authorizing results. No positive
  result or approval token was created.
- Arc control plane passed authenticated loopback registration, heartbeat,
  restart recovery, evidence persistence, and dry-run acknowledgement.
- Operator preflight passed policy classification and rejected nonce replay.
- The read-only execution seam required both Supervisor and Arc opt-ins and a
  configured document root. Each missing gate denied the read.
- One, two, and eight worker runs passed. An offline worker stayed visible and
  blocked while healthy workers remained isolated and usable.
- A readable synthetic document completed at tier 1. A missing document stopped
  safely, created an SOP gap, and escalated to the executive-manager tier.

## Not Tested Or Authorized

- Positive approval, token creation, token consumption, or replay-backed action authority
- General worker assignment or action dispatch from the LIMA Office console
- External form submission, messaging, connectors, browser automation, or file mutation
- Customer, employee, financial, legal, medical, credential, or other sensitive data
- Named owner identity, Windows Hello/passkey, OIDC, MFA, or production device trust
- Installer/package clean-install behavior for a build containing this milestone

## Owner-Attended Result

On 2026-09-11, the owner reported that the **Complete fictional contact** path
completed according to the supplied walkthrough. This records a successful
attended pass through the visible Profile A helper, proposal, tokenless preview,
pending-request, and non-authorizing decision path. It does not authorize a
positive result, token, Arc dispatch, customer data, or external effect.

The remaining package-level gate is a clean-install/restart/reboot pass from the
future lab.6 ZIP. That pass must also confirm worker/evidence visibility, durable
request/result restoration, and that the process-only operator session must be
bound again after restart.

The owner walkthrough covered this current-source sequence:

1. Open the LIMA Office Supervisor Console and confirm the Profile A lab-only card.
2. Bind the attended Windows session and confirm the 30-minute, process-only warning.
3. Run one fixed synthetic registration review and create its task draft.
4. Move the draft to future-approval review, create and review its tokenless preview.
5. Create a pending synthetic request, then deny or cancel it.
6. Refresh Arc inventory and confirm worker/evidence state is visible.
7. Treat restart persistence and attended-session rebinding as package-level
   checks that must be repeated against the exact lab.6 ZIP.

Stop immediately if the UI claims a positive approval, token, worker dispatch,
external effect, production identity, or customer-ready status.
