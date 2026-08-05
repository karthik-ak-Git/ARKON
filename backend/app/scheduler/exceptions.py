"""Scheduler exceptions."""


class SchedulerError(Exception):
    """Base scheduler error."""


class TaskValidationError(SchedulerError):
    """Task failed validation."""


class DependencyCycleError(SchedulerError):
    """Dependency graph contains a cycle."""


class DependencyNotMetError(SchedulerError):
    """Required dependency not satisfied."""


class TaskNotFoundError(SchedulerError):
    """Task not found in scheduler."""


class PolicyError(SchedulerError):
    """Scheduling policy error."""


class PreemptionError(SchedulerError):
    """Preemption error."""


class BackpressureError(SchedulerError):
    """Backpressure error."""


class CapacityExceededError(SchedulerError):
    """Scheduler capacity exceeded."""


class SchedulerPausedError(SchedulerError):
    """Scheduler is paused."""


class ConstraintViolationError(SchedulerError):
    """Task constraints not satisfied."""
