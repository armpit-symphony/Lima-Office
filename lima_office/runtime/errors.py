"""Explicit fail-closed runtime exceptions."""


class LimaOfficeRuntimeError(RuntimeError):
    """Base error for Phase 1A mock runtime failures."""


class ContractLoadError(LimaOfficeRuntimeError):
    """Raised when a contract schema cannot be loaded unambiguously."""


class ContractValidationError(LimaOfficeRuntimeError):
    """Raised when contract validation cannot run or a payload is invalid."""


class PolicyDenyError(LimaOfficeRuntimeError):
    """Raised when Guardian policy denies an action."""


class WorkerStateError(LimaOfficeRuntimeError):
    """Raised when worker state blocks a runtime operation."""


class WorkerLifecycleValidationError(WorkerStateError):
    """Raised when worker lifecycle metadata validation fails."""


class WorkerLifecycleTransitionError(WorkerStateError):
    """Raised when worker lifecycle transition safety checks fail."""


class TaskLifecycleValidationError(LimaOfficeRuntimeError):
    """Raised when task lifecycle metadata validation fails."""


class TaskLifecycleTransitionError(LimaOfficeRuntimeError):
    """Raised when task lifecycle transition safety checks fail."""


class EvidenceRequiredError(LimaOfficeRuntimeError):
    """Raised when required evidence is missing before an action can proceed."""


class EvidenceWriteError(LimaOfficeRuntimeError):
    """Raised when the mock evidence writer cannot record an in-memory artifact."""


class UnsafeRuntimeActionError(LimaOfficeRuntimeError):
    """Raised when scaffolding is asked to perform out-of-scope runtime work."""


class CrossContractInvariantError(UnsafeRuntimeActionError):
    """Raised when individually valid contracts form an unsafe flow."""
