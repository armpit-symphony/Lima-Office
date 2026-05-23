# Deployment Docs

This directory contains docs-only deployment planning for LIMA Office OS. These
blueprints do not implement installers, services, daemons, databases, queues,
web servers, UI, live connectors, OAuth/provider wiring, external sends,
external model calls, browser automation, remediation, or production operations.

## Documents

- [Worker Deployment Blueprint](WORKER_DEPLOYMENT_BLUEPRINT.md)
- [Network Blueprint](NETWORK_BLUEPRINT.md)
- [Worker Hardware Baseline](WORKER_HARDWARE_BASELINE.md)
- [Worker Install Layout](WORKER_INSTALL_LAYOUT.md)
- [Worker Lifecycle](WORKER_LIFECYCLE.md)
- [Update Rollback Blueprint](UPDATE_ROLLBACK_BLUEPRINT.md)
- [Field IT Checklist](FIELD_IT_CHECKLIST.md)

## Related Runbooks

- [Worker deployment runbook](../runbooks/worker-deployment.md)
- [Worker update rollback runbook](../runbooks/worker-update-rollback.md)
- [Field IT preflight runbook](../runbooks/field-it-preflight.md)

## Phase Rule

Deployment docs define the shape of a future lab deployment only. They do not
authorize live customer connectors, external sends, real remediation, production
server touch, or worker runtime services.
