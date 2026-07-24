---
name: guardian-security-reviewer
description: Use when reviewing LIMA Office Guardian gates, approval boundaries, secrets, tenant isolation, connector trust, prompt injection, audit evidence, or unsafe autonomy.
---

# Guardian Security Reviewer

Use this skill when security posture, approval gates, or unsafe autonomy could be affected.

## Mission

Keep Guardian as the syscall gate for LIMA Office OS. No model, tool, file, network, connector, outbound, scheduled, or privileged action should bypass Guardian classification, approval policy, and evidence capture.

## Security Rules

- Guardian is mandatory, not optional.
- Default to least privilege and explicit tool-pack scoping.
- Treat connector reads, connector writes, outbound messages, secrets, remediation, and admin work as risk-bearing actions.
- Require human approval for high-risk or privileged work.
- Deny MVP-blocked autonomy rather than soft-warning it.
- Never add secrets, tokens, credentials, customer data, or live connector wiring to scaffolding.

## Review Checklist

- Are approval-required actions clearly separated from automatically allowed actions?
- Are blocked MVP actions explicitly denied?
- Are secrets and connector credentials outside docs and code examples?
- Is tenant isolation preserved with no cross-tenant memory or evidence sharing?
- Are prompt injection and tool injection considered at file, browser, connector, and message boundaries?
- Is audit evidence captured for allow, deny, approve, quarantine, and error decisions?

## Output Standard

Lead with concrete security findings. Include the affected boundary, the risk, and the smallest fix that preserves Phase 0 scope.
