"""Supervisor-side scaffolding and approved non-executing lab boundaries."""

from lima_office.runtime.errors import WorkerEndpointUnavailableError

from .arc_worker import ArcWorkerPreviewEndpoint, LocalArcWorkerPreviewEndpoint
from .control_plane import SupervisorControlPlane, load_lima_runner
from .heartbeat import HeartbeatService
from .health import SupervisorHealthReporter
from .operator_channel import OperatorChannel
from .operator_service import (
    OperatorControlPlaneService,
    build_supervisor_operator_server,
)
from .task_lifecycle_simulator import TaskLifecycleSimulator
from .task_queue import TaskQueue
from .worker_lifecycle_simulator import WorkerLifecycleSimulator
from .worker_lifecycle import AuthenticatedWorkerLifecycleService
from .worker_channel import WorkerChannel
from .worker_client import AuthenticatedArcWorkerClient
from .worker_registry import WorkerRecord, WorkerRegistry

__all__ = [
    "ArcWorkerPreviewEndpoint",
    "AuthenticatedArcWorkerClient",
    "AuthenticatedWorkerLifecycleService",
    "HeartbeatService",
    "LocalArcWorkerPreviewEndpoint",
    "OperatorChannel",
    "OperatorControlPlaneService",
    "SupervisorControlPlane",
    "SupervisorHealthReporter",
    "TaskLifecycleSimulator",
    "TaskQueue",
    "WorkerLifecycleSimulator",
    "WorkerChannel",
    "WorkerEndpointUnavailableError",
    "WorkerRecord",
    "WorkerRegistry",
    "build_supervisor_operator_server",
    "load_lima_runner",
]
