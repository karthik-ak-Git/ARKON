"""ARKON Execution Engine - Interfaces.

Defines the contracts for all execution engine components.
The Execution Engine manages tasks.
The Runtime manages agents.
These are different responsibilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


# =============================================================================
# Task States
# =============================================================================


class TaskState(str, Enum):
    """Valid task states.

    State transitions must be validated.
    Illegal transitions throw exceptions.
    """

    CREATED = "created"
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    EXECUTING = "executing"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    RECOVERING = "recovering"


# Valid task state transitions
TASK_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.CREATED: {TaskState.QUEUED, TaskState.CANCELLED},
    TaskState.QUEUED: {TaskState.DISPATCHED, TaskState.CANCELLED},
    TaskState.DISPATCHED: {TaskState.EXECUTING, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.EXECUTING: {
        TaskState.WAITING,
        TaskState.PAUSED,
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELLED,
        TaskState.TIMED_OUT,
    },
    TaskState.WAITING: {
        TaskState.EXECUTING,
        TaskState.CANCELLED,
        TaskState.FAILED,
    },
    TaskState.PAUSED: {
        TaskState.EXECUTING,
        TaskState.CANCELLED,
        TaskState.FAILED,
    },
    TaskState.COMPLETED: set(),
    TaskState.FAILED: {TaskState.RECOVERING, TaskState.CANCELLED},
    TaskState.CANCELLED: set(),
    TaskState.TIMED_OUT: {TaskState.RECOVERING, TaskState.CANCELLED},
    TaskState.RECOVERING: {TaskState.EXECUTING, TaskState.FAILED, TaskState.CANCELLED},
}


# =============================================================================
# Retry Policy
# =============================================================================


class RetryPolicy(str, Enum):
    """Retry strategy types."""

    IMMEDIATE = "immediate"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"


# =============================================================================
# Checkpoint Policy
# =============================================================================


class CheckpointPolicy(str, Enum):
    """Checkpoint trigger types."""

    MANUAL = "manual"
    PERIODIC = "periodic"
    BEFORE_RETRY = "before_retry"
    BEFORE_SHUTDOWN = "before_shutdown"


# =============================================================================
# ITask
# =============================================================================


class ITask(ABC):
    """Interface for a task."""

    @abstractmethod
    def get_id(self) -> str: ...

    @abstractmethod
    def get_state(self) -> TaskState: ...

    @abstractmethod
    def get_capability(self) -> str: ...

    @abstractmethod
    def get_payload(self) -> dict[str, Any]: ...

    @abstractmethod
    def get_priority(self) -> int: ...

    @abstractmethod
    def get_dependencies(self) -> list[str]: ...

    @abstractmethod
    def get_timeout(self) -> float | None: ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...


# =============================================================================
# IExecutionEngine
# =============================================================================


class IExecutionEngine(ABC):
    """Interface for the execution engine.

    Responsible for:
    - Task creation, dispatch, execution
    - Pause, resume, cancel, retry, recover
    - Progress reporting, checkpointing
    - Timeout management
    - Execution history
    """

    @abstractmethod
    async def create_task(
        self,
        capability: str,
        payload: dict[str, Any],
        workspace_id: str | None = None,
        agent_id: str | None = None,
        priority: int = 0,
        dependencies: list[str] | None = None,
        timeout: float | None = None,
        retry_policy: RetryPolicy = RetryPolicy.IMMEDIATE,
        max_retries: int = 3,
        checkpoint_policy: CheckpointPolicy = CheckpointPolicy.MANUAL,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new task.

        Returns:
            Task ID.
        """
        ...

    @abstractmethod
    async def dispatch(self, task_id: str) -> None:
        """Dispatch a task to an agent."""
        ...

    @abstractmethod
    async def execute(self, task_id: str) -> Any:
        """Execute a task."""
        ...

    @abstractmethod
    async def pause(self, task_id: str) -> None:
        """Pause a running task."""
        ...

    @abstractmethod
    async def resume(self, task_id: str) -> None:
        """Resume a paused task."""
        ...

    @abstractmethod
    async def cancel(self, task_id: str) -> None:
        """Cancel a task."""
        ...

    @abstractmethod
    async def retry(self, task_id: str) -> None:
        """Retry a failed task."""
        ...

    @abstractmethod
    async def recover(self, task_id: str) -> None:
        """Recover a task from checkpoint."""
        ...

    @abstractmethod
    async def get_task(self, task_id: str) -> Any:
        """Get a task by ID."""
        ...

    @abstractmethod
    async def list_tasks(self, state: TaskState | None = None) -> list[Any]:
        """List tasks, optionally filtered by state."""
        ...

    @abstractmethod
    async def get_progress(self, task_id: str) -> dict[str, Any]:
        """Get task progress."""
        ...

    @abstractmethod
    async def get_result(self, task_id: str) -> Any:
        """Get task result."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the engine."""
        ...


# =============================================================================
# IDispatcher
# =============================================================================


class IDispatcher(ABC):
    """Interface for task dispatcher.

    Receives tasks and hands them to the Runtime.
    Does NOT schedule globally.
    """

    @abstractmethod
    async def dispatch(self, task: ITask) -> str:
        """Dispatch a task to an eligible agent.

        Returns:
            Agent ID the task was dispatched to.
        """
        ...

    @abstractmethod
    async def find_agent(self, capability: str) -> str | None:
        """Find an eligible agent for a capability.

        Returns:
            Agent ID or None.
        """
        ...

    @abstractmethod
    async def cancel(self, task_id: str) -> None:
        """Cancel a dispatched task."""
        ...


# =============================================================================
# ITaskQueue
# =============================================================================


class ITaskQueue(ABC):
    """Interface for the task queue."""

    @abstractmethod
    async def enqueue(self, task: ITask) -> None:
        """Add a task to the queue."""
        ...

    @abstractmethod
    async def dequeue(self) -> ITask | None:
        """Remove the highest priority task from the queue."""
        ...

    @abstractmethod
    async def peek(self) -> ITask | None:
        """View the next task without removing."""
        ...

    @abstractmethod
    async def size(self) -> int:
        """Get queue size."""
        ...

    @abstractmethod
    async def is_empty(self) -> bool:
        """Check if queue is empty."""
        ...

    @abstractmethod
    async def remove(self, task_id: str) -> bool:
        """Remove a specific task from the queue."""
        ...


# =============================================================================
# ICheckpointStore
# =============================================================================


class ICheckpointStore(ABC):
    """Interface for checkpoint persistence."""

    @abstractmethod
    async def save(self, checkpoint: dict[str, Any]) -> None:
        """Save a checkpoint."""
        ...

    @abstractmethod
    async def load(self, task_id: str) -> dict[str, Any] | None:
        """Load the latest checkpoint for a task."""
        ...

    @abstractmethod
    async def list_checkpoints(self, task_id: str) -> list[dict[str, Any]]:
        """List all checkpoints for a task."""
        ...

    @abstractmethod
    async def delete(self, task_id: str) -> None:
        """Delete all checkpoints for a task."""
        ...
