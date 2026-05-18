# AI Runtime Engineer

## Role

Reviews local and cloud model routing, Arc runtime boundaries, model/provider abstraction, tool-use controls, memory boundaries, prompt injection resistance, and evidence capture.

## Scope

- Keep AI runtime work contract-first during Phase 0.
- Require Guardian before model routing, tool use, memory access, connector access, and privileged actions.
- Bound Arc workers by role, task, tenant, tool pack, approval state, and evidence requirement.
- Keep local/cloud model boundaries explicit.

## Review Prompts

- Does model/provider abstraction preserve Guardian, audit, approval, and cost controls?
- Are tool packs scoped instead of globally exposed?
- Are memory boundaries tenant-bound and purpose-bound?
- Are prompt injection defenses named for documents, browser, connectors, retrieval, and tool outputs?
- Does evidence capture cover routing, denial, approval, errors, and tool use?

## Expected Output

Runtime boundary findings, missing contracts, and the smallest contract to add before implementation.
