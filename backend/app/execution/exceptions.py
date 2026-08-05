"""ARKON Execution Engine - Exceptions.

All execution-specific exceptions.
"""

from __future__ import annotations


class ExecutionEngineError(Exception):
    """Base execution engine error."""
    pass


# Task errors


class TaskError(ExecutionEngineError):
    """Base task error."""
    pass


class TaskNotFoundError(TaskError):
    """Task not found."""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task not found: '{task_id}'")


class TaskValidationError(TaskError):
    """Task validation failed."""
    def __init__(self, reason: str = ""):
        self.reason = reason
        super().__init__(f"Task validation failed: {reason}")


class TaskAlreadyExistsError(TaskError):
    """Task already exists."""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task already exists: '{task_id}'")


# State errors


class InvalidTaskStateError(TaskError):
    """Invalid task state transition."""
    def __init__(self, task_id: str, from_state: str, to_state: str):
        self.task_id = task_id
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid task transition '{task_id}': {from_state} -> {to_state}"
        )


# Dispatch errors


class DispatchError(TaskError):
    """Dispatch failed."""
    def __init__(self, task_id: str, reason: str = ""):
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Dispatch failed for task '{task_id}': {reason}")


class NoAgentAvailableError(DispatchError):
    """No agent available for the required capability."""
    def __init__(self, task_id: str, capability: str):
        self.capability = capability
        super().__init__(task_id, f"No agent available for capability '{capability}'")


# Dependency errors


class DependencyError(TaskError):
    """Base dependency error."""
    pass


class DependencyNotMetError(DependencyError):
    """Task dependencies not met."""
    def __init__(self, task_id: str, missing: list[str]):
        self.task_id = task_id
        self.missing = missing
        super().__init__(
            f"Dependencies not met for task '{task_id}': {missing}"
        )


class CircularDependencyError(DependencyError):
    """Circular dependency detected."""
    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")


# Timeout errors


class TaskTimeoutError(TaskError):
    """Task execution timed out."""
    def __init__(self, task_id: str, timeout: float = 0):
        self.task_id = task_id
        self.timeout = timeout
        super().__init__(f"Task timed out '{task_id}' after {timeout}s")


# Cancellation errors


class TaskCancelledError(TaskError):
    """Task was cancelled."""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task cancelled: '{task_id}'")


# Checkpoint errors


class CheckpointError(ExecutionEngineError):
    """Base checkpoint error."""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint not found."""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Checkpoint not found for task '{task_id}'")


class CheckpointSaveError(CheckpointError):
    """Failed to save checkpoint."""
    def __init__(self, task_id: str, reason: str = ""):
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Failed to save checkpoint for '{task_id}': {reason}")


# Recovery errors


class RecoveryError(ExecutionEngineError):
    """Base recovery error."""
    pass


class RecoveryFailedError(RecoveryError):
    """Recovery failed."""
    def __init__(self, task_id: str, reason: str = ""):
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Recovery failed for task '{task_id}': {reason}")


# Retry errors


class RetryExhaustedError(TaskError):
    """All retry attempts exhausted."""
    def __init__(self, task_id: str, max_retries: int):
        self.task_id = task_id
        self.max_retries = max_retries
        super().__init__(
            f"Retry exhausted for task '{task_id}' after {max_retries} attempts"
        )


# Engine errors


class EngineNotRunningError(ExecutionEngineError):
    """Engine is not running."""
    pass


class EngineAlreadyRunningError(ExecutionEngineError):
    """Engine is already running."""
    pass
