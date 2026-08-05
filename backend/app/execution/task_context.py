"""ARKON Execution Engine - Task Context.

Provides execution context for a running task.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskContext:
    """Execution context passed to task execution.

    Provides access to workspace, configuration,
    cancellation tokens, and progress reporting.
    """

    task_id: str = ""
    workspace_id: str = ""
    agent_id: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    storage_path: str = ""

    # Cancellation
    _cancelled: bool = field(default=False, repr=False)

    # Progress
    _progress: float = field(default=0.0, repr=False)
    _current_step: str = field(default="", repr=False)
    _message: str = field(default="", repr=False)

    # Timing
    started_at: float = field(default_factory=time.time)

    # Intermediate results
    results: dict[str, Any] = field(default_factory=dict)

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True

    def update_progress(
        self,
        progress: float,
        current_step: str = "",
        message: str = "",
    ) -> None:
        """Update task progress.

        Args:
            progress: Progress percentage (0-100).
            current_step: Name of current step.
            message: Human-readable message.
        """
        self._progress = max(0.0, min(100.0, progress))
        self._current_step = current_step
        self._message = message

    def get_progress(self) -> dict[str, Any]:
        """Get current progress."""
        elapsed = time.time() - self.started_at
        estimated_remaining = None
        if self._progress > 0:
            total_estimated = elapsed / (self._progress / 100.0)
            estimated_remaining = max(0, total_estimated - elapsed)

        return {
            "progress": self._progress,
            "current_step": self._current_step,
            "message": self._message,
            "elapsed": elapsed,
            "estimated_remaining": estimated_remaining,
        }

    def set_result(self, key: str, value: Any) -> None:
        """Store an intermediate result."""
        self.results[key] = value

    def get_result(self, key: str) -> Any:
        """Get an intermediate result."""
        return self.results.get(key)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "config": self.config,
            "storage_path": self.storage_path,
            "cancelled": self._cancelled,
            "progress": self._progress,
            "current_step": self._current_step,
            "message": self._message,
            "started_at": self.started_at,
            "results": self.results,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskContext:
        """Create from dictionary."""
        ctx = cls(
            task_id=data.get("task_id", ""),
            workspace_id=data.get("workspace_id", ""),
            agent_id=data.get("agent_id", ""),
            config=data.get("config", {}),
            storage_path=data.get("storage_path", ""),
            started_at=data.get("started_at", time.time()),
        )
        ctx._cancelled = data.get("cancelled", False)
        ctx._progress = data.get("progress", 0.0)
        ctx._current_step = data.get("current_step", "")
        ctx._message = data.get("message", "")
        ctx.results = data.get("results", {})
        return ctx
