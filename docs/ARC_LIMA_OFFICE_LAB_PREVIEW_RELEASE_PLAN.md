# Arc + LIMA Office Lab Preview Release Plan

**Date:** August 27, 2026
**Status:** Proposed release-hardening lane
**Authority:** Planning only. This document does not authorize a release, tag, customer pilot, production deployment, or expansion of runtime authority.

## Product decision

The active product lane is LIMA Office Supervisor plus Arc worker nodes.

Sparkbot is not a dependency, operator shell, package component, or release gate for this preview. Historical Sparkbot research may remain as reference material, but preview completion must not require Sparkbot code, UI, services, or deployment.

## Preview target

The first downloadable preview is an attended, local lab deployment with:

- one LIMA Office Supervisor;
- one to eight Arc worker mini PCs;
- one tenant at a time;
- Guardian enforcement on every governed action;
- separate opt-ins for model execution and tool execution;
- reviewable, sanitized evidence for important decisions and actions.

This is a lab preview, not a production release.

## Included scope

- Localhost-only operator UI.
- Training and Working modes.
- Arc task queue, approvals, SOP view, and task lifecycle.
- Bounded document-list and document-read operations.
- Single-use grants for governed document operations.
- Separate execution opt-ins; preview or planning does not imply execution.
- SQLite-backed evidence, replay, and restart behavior.
- Windows operator install, start, status, stop, upgrade rollback, and uninstall lifecycle.

## Explicitly excluded

- Sparkbot integration or packaging.
- Production or unattended operation.
- LAN exposure or remote multi-user access.
- Customer data, production secrets, or regulated data.
- Live model execution.
- Connectors, OAuth, or general network access.
- External email, chat, form submission, or other outbound sends.
- File mutation, deletion, or overwrite.
- Software installation, remediation, or production server changes by Arc.
- Robotics or physical-device control.
- Hidden background actions.
- Live LIMA IT remediation.

The current operator UI has no operator authentication. It is suitable only for an attended, localhost lab until an authentication contract and implementation are approved.

## Release units

The preview is a coordinated stack, not four independent floating branches:

1. LIMA Office Supervisor
2. Arc worker
3. LIMA Runtime
4. Guardian

The release manifest must record an exact commit for every unit. If any commit moves after validation, the affected release gates must be rerun.

## Current blockers

1. The coordinated Windows artifact has not yet completed a clean extracted install and smoke run.
2. There is no approved or published GitHub prerelease for the four-unit stack.
3. Operator authentication remains absent, so the preview is attended and localhost-only.
4. Live models, connectors, customer data, and privileged actions remain blocked for this preview.

## Release gates

### Gate 1 — Exact stack coherence

Status: passed locally on August 27, 2026.

- Classify every dependency as tracking or intentionally frozen.
- Select exact Arc, LIMA Runtime, and Guardian commits for the preview.
- Run dependency pin checks with currency and installed-package verification.
- Produce a machine-readable release manifest.

### Gate 2 — Governed runtime validation

Status: passed locally against Arc 17ff82e, LIMA Runtime 4a59940, and Guardian 69e8432.

- Pass the complete LIMA Office, Arc, Guardian, and focused LIMA Runtime test suites.
- Pass the two-worker and eight-worker LIMA Office smoke tests.
- Pass an attended document-list and document-read session with grants.
- Verify risky, ungranted, expired, replayed, and malformed actions fail closed.
- Verify evidence does not contain document contents or secrets.

### Gate 3 — Windows operator package

Status: packaging implementation complete; clean artifact install validation pending.

- Install from a clean, versioned artifact on a disposable Windows environment.
- Verify idempotent install, start, status, stop, upgrade rollback, and uninstall.
- Verify uninstall preserves operator data as documented.
- Verify the preview does not require a model download or unrestricted network access.

### Gate 4 — Artifact and evidence review

- Build a versioned archive or installer.
- Publish SHA-256 checksums and the exact dependency manifest.
- Include install, smoke-test, evidence-review, rollback, and uninstall instructions.
- Repeat smoke testing from the clean extracted artifact rather than a developer worktree.

### Gate 5 — Explicit operator decision

After Gates 1-4 pass, the operator must explicitly approve or reject creation of a version tag and downloadable prerelease. Passing tests alone does not authorize publication.

## Ordered work plan

1. Reconcile and document the exact four-unit commit set.
2. Repair the dependency-currency workflows so a clean stack is green in CI.
3. Refresh status, architecture links, and Windows operator instructions.
4. Run coordinated clean test and smoke matrices against the selected commits.
5. Build and inspect the versioned artifact, checksum, and release manifest.
6. Test the artifact on this Windows PC or a disposable Windows environment.
7. Present the evidence for an explicit prerelease decision.

## Preview completion criterion

The preview is ready when a new operator can download one versioned artifact, verify its checksum and manifest, install it on an attended Windows lab PC, run the bounded smoke workflow, inspect sanitized evidence, perform rollback or uninstall, and understand every blocked capability without relying on an uncommitted developer worktree.
