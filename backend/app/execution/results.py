"""ARKON Execution Engine - Results.

Task results including artifacts, logs, output, metrics,
duration, errors, and warnings.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskResult:
    """Result of a completed task.

    Contains:
    - Artifacts
    - Logs
    - Output
    - Metrics
    - Duration
    - Errors
    - Warnings
    """

    task_id: str = ""
    success: bool = True

    # Output
    output: Any = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    # Logs
    logs: list[str] = field(default_factory=list)

    # Metrics
    metrics: dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0

    # Issues
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Timing
    started_at: float | None = None
    completed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "metrics": self.metrics,
            "duration": self.duration,
            "errors": self.errors,
            "warnings": self.warnings,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskResult:
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id", ""),
            success=data.get("success", True),
            output=data.get("output"),
            artifacts=data.get("artifacts", []),
            logs=data.get("logs", []),
            metrics=data.get("metrics", {}),
            duration=data.get("duration", 0.0),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at", time.time()),
        )


class ResultStore:
    """Stores task results.

    In-memory store for task results.
    """

    def __init__(self) -> None:
        """Initialize result store."""
        self._results: dict[str, TaskResult] = {}

    def store(self, result: TaskResult) -> None:
        """Store a task result."""
        self._results[result.task_id] = result

    def get(self, task_id: str) -> TaskResult | None:
        """Get a task result."""
        return self._results.get(task_id)

    def exists(self, task_id: str) -> bool:
        """Check if a result exists."""
        return task_id in self._results

    def delete(self, task_id: str) -> bool:
        """Delete a task result."""
        return self._results.pop(task_id, None) is not None

    def list_all(self) -> list[str]:
        """List all task IDs with results."""
        return list(self._results.keys())

    def count(self) -> int:
        """Get number of stored results."""
        return len(self._results)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_count": len(self._results),
            "task_ids": list(self._results.keys()),
        }
