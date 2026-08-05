"""ARKON Execution Engine - Events.

All execution event types.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionEvent:
    """Base execution event."""
    timestamp: float = field(default_factory=time.time)
    event_type: str = ""
    task_id: str = ""


@dataclass
class TaskCreated(ExecutionEvent):
    """Task created."""
    event_type: str = "task_created"
    capability: str = ""
    priority: int = 0
    workspace_id: str = ""


@dataclass
class TaskQueued(ExecutionEvent):
    """Task queued."""
    event_type: str = "task_queued"
    position: int = 0


@dataclass
class TaskDispatched(ExecutionEvent):
    """Task dispatched to agent."""
    event_type: str = "task_dispatched"
    agent_id: str = ""


@dataclass
class TaskStarted(ExecutionEvent):
    """Task execution started."""
    event_type: str = "task_started"


@dataclass
class TaskProgress(ExecutionEvent):
    """Task progress update."""
    event_type: str = "task_progress"
    progress: float = 0.0
    current_step: str = ""
    message: str = ""
    estimated_remaining: float | None = None


@dataclass
class TaskCheckpointCreated(ExecutionEvent):
    """Checkpoint created."""
    event_type: str = "task_checkpoint_created"
    checkpoint_id: str = ""


@dataclass
class TaskRecovered(ExecutionEvent):
    """Task recovered from checkpoint."""
    event_type: str = "task_recovered"
    checkpoint_id: str = ""


@dataclass
class TaskRetried(ExecutionEvent):
    """Task retry attempted."""
    event_type: str = "task_retried"
    attempt: int = 0
    max_retries: int = 0
    reason: str = ""


@dataclass
class TaskCompleted(ExecutionEvent):
    """Task completed successfully."""
    event_type: str = "task_completed"
    result: Any = None
    duration: float = 0.0


@dataclass
class TaskFailed(ExecutionEvent):
    """Task failed."""
    event_type: str = "task_failed"
    error: str = ""
    error_type: str = ""


@dataclass
class TaskCancelled(ExecutionEvent):
    """Task cancelled."""
    event_type: str = "task_cancelled"
    reason: str = ""


@dataclass
class TaskTimedOut(ExecutionEvent):
    """Task timed out."""
    event_type: str = "task_timed_out"
    timeout: float = 0.0


@dataclass
class TaskPaused(ExecutionEvent):
    """Task paused."""
    event_type: str = "task_paused"


@dataclass
class TaskResumed(ExecutionEvent):
    """Task resumed."""
    event_type: str = "task_resumed"


# Event type registry
EXECUTION_EVENT_TYPES: dict[str, type[ExecutionEvent]] = {
    "task_created": TaskCreated,
    "task_queued": TaskQueued,
    "task_dispatched": TaskDispatched,
    "task_started": TaskStarted,
    "task_progress": TaskProgress,
    "task_checkpoint_created": TaskCheckpointCreated,
    "task_recovered": TaskRecovered,
    "task_retried": TaskRetried,
    "task_completed": TaskCompleted,
    "task_failed": TaskFailed,
    "task_cancelled": TaskCancelled,
    "task_timed_out": TaskTimedOut,
    "task_paused": TaskPaused,
    "task_resumed": TaskResumed,
}
