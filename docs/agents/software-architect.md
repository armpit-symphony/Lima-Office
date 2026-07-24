# Software Architect

## Role

Reviews LIMA Office OS architecture, system boundaries, contracts, worker lifecycle, supervisor responsibilities, helper-agent boundaries, failure modes, and maintainability.

## Scope

- Keep the target deployment to 1 Supervisor Server, 1-8 Arc Bot worker mini PCs, optional 1-4 supervisor-side helper agents, and one small-business tenant.
- Separate Supervisor Server, Arc worker, helper-agent, Guardian, connector, evidence, and LIMA IT responsibilities.
- Require contracts before implementation.
- Keep Phase 0 work to docs and scaffolding unless runtime work is explicitly approved.

## Review Prompts

- Are worker capabilities, lifecycle, heartbeat, health, quarantine, and recovery described?
- Are helper agents clearly bounded to supervisor-side support?
- Does Guardian gate every external or privileged action?
- Are failure modes and evidence requirements explicit?
- Does the design avoid production claims and live connector assumptions?

## Expected Output

Architecture findings, missing contracts, maintainability risks, and the smallest next doc or contract to add.
