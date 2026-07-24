---
name: runbook-writer
description: Use when writing LIMA Office runbooks for deployment checks, health checks, incidents, quarantine, rollback, approvals, evidence capture, or LIMA IT handoff.
---

# Runbook Writer

Use this skill for operational docs and small-business field procedures.

## Mission

Write practical runbooks for a small-business LIMA Office deployment with one Supervisor Server, 1-8 Arc worker mini PCs, optional supervisor-side helper agents, Guardian gates, and future LIMA IT handoff.

## Runbook Rules

- State prerequisites, operator role, risk, approval requirement, expected evidence, and rollback or escalation path.
- Keep commands conceptual unless implementation exists and has been approved.
- Separate read-only diagnostics from remediation.
- Require approval before software install/update, endpoint changes, network changes, production server touch, or customer-data mutation.
- Include degraded, offline, quarantine, and failed-approval paths.
- Avoid hidden background work.

## Runbook Template

Use this structure unless the repo has a stronger local pattern:

- Purpose
- Scope
- Preconditions
- Required approval
- Evidence to capture
- Procedure
- Rollback or stop condition
- Escalation
- Open questions

## Output Standard

Runbooks should be short, operator-readable, and honest about Phase 0 gaps. Mark future implementation dependencies clearly.
