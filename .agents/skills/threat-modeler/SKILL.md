---
name: threat-modeler
description: Use when creating or reviewing LIMA Office threat models, trust boundaries, misuse cases, attack paths, mitigations, evidence requirements, or open security questions.
---

# Threat Modeler

Use this skill for threat modeling LIMA Office OS designs, docs, and contracts.

## Mission

Identify realistic small-business threats before runtime implementation. Focus on Supervisor Server, Arc worker nodes, helper agents, Guardian, connectors, local network exposure, secrets, approvals, evidence, and LIMA IT handoff.

## Threat Modeling Scope

Cover at least:

- Assets: customer data, credentials, approvals, audit evidence, worker identity, connector tokens, business records.
- Actors: business operator, admin, worker node, helper agent, connector, local attacker, compromised endpoint, malicious email or document, external service.
- Trust boundaries: supervisor to worker, Guardian to tools, model to tool pack, connector to business system, LIMA Office to LIMA IT, local network to internet.
- Abuse cases: prompt injection, forged approval, stolen worker identity, connector overreach, evidence tampering, hidden background work, unsafe remediation, data exfiltration.

## Review Checklist

- Are trust boundaries explicit?
- Are assumptions marked as assumptions?
- Are mitigations tied to Guardian, approval, least privilege, logging, quarantine, or rollback?
- Are residual risks and open questions recorded?
- Is the threat model scoped to 1 Supervisor Server, 1-8 workers, and one tenant?

## Output Standard

Summarize threats as scenario, impact, likely path, mitigation, evidence, and open question. Keep recommendations contract-first.
