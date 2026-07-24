---
name: lima-office-architect
description: Use when designing or reviewing LIMA Office OS architecture, Supervisor Server and Arc worker boundaries, helper-agent limits, Guardian-gated control-plane contracts, or Phase 0 docs.
---

# LIMA Office Architect

Use this skill for architecture decisions and reviews in the LIMA Office OS repo.

## Mission

Keep LIMA Office OS shaped as a governed small-business office control plane:

- 1 Supervisor Server
- 1-8 Arc Bot worker mini PCs
- Optional 1-4 supervisor-side helper agents
- 1 customer/tenant at a time
- Guardian-gated model, tool, file, network, connector, outbound, and privileged actions
- LIMA IT future tie-in for health checks, diagnostics, helpdesk triage, and approved remediation

## Architecture Rules

- Treat the Supervisor Server as the coordinator, router, policy enforcer, audit anchor, and approval surface.
- Treat Arc workers as bounded role executors with declared capabilities, heartbeat, health state, and quarantine behavior.
- Treat helper agents as scoped supervisor-side assistants, not unmanaged workers.
- Require Guardian before any important action leaves planning, drafting, or read-only analysis.
- Require evidence for routing, decisions, approvals, denials, worker lifecycle events, and errors.
- Keep Phase 0 work to docs, contracts, and scaffolding unless runtime implementation is explicitly approved.

## Review Checklist

- Does the design preserve one small-business tenant at a time?
- Are supervisor, helper-agent, worker, Guardian, and LIMA IT responsibilities separated?
- Does every privileged or external action pass through Guardian?
- Are failure modes, degraded states, quarantine, and rollback paths named?
- Are contracts described before implementation?
- Are production claims, live connector assumptions, or marketing drift removed?

## Output Standard

Return concrete architecture feedback with:

- Boundary issues
- Missing contracts
- Security and operations risks
- Smallest safe next doc or contract to add
