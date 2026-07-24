---
name: contracts-first-engineer
description: Use when defining LIMA Office contracts before implementation, including Guardian decisions, worker lifecycle, task routing, evidence records, approvals, connector posture, or LIMA IT handoff.
---

# Contracts-First Engineer

Use this skill when a task could lead to implementation before interfaces, states, or evidence requirements are documented.

## Mission

Keep LIMA Office OS in Phase 0 until core contracts exist. Prefer markdown contracts, state machines, schemas, and interface notes over runtime code.

## Contract Areas

Define contracts for:

- Guardian decision envelope
- Approval request and approval result
- Evidence record
- Task lifecycle and routing
- Supervisor to Arc worker assignment
- Worker registration, heartbeat, health, and quarantine
- Helper-agent scope and supervisor-side limits
- Connector readiness and risk posture
- LIMA IT diagnostic, helpdesk, and remediation handoff
- Audit export and retention posture

## Review Checklist

- Is there a named contract before behavior is implemented?
- Are states, inputs, outputs, denied cases, and evidence fields named?
- Are privileged paths approval-gated?
- Are failure, timeout, retry, rollback, and quarantine states included?
- Are examples sanitized and free of secrets or customer data?

## Output Standard

When implementation is requested too early, propose the smallest contract artifact needed first. Keep examples concise and non-executable unless explicitly approved.
