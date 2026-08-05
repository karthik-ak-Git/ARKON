"""ARKON Execution Engine - Progress Reporting.

Supports continuous progress updates during task execution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProgressUpdate:
    """A single progress update."""
    task_id: str = ""
    progress: float = 0.0
    current_step: str = ""
    message: str = ""
    estimated_remaining: float | None = None
    timestamp: float = field(default_factory=time.time)


class ProgressTracker:
    """Tracks task execution progress.

    Supports:
    - Progress percentage (0-100)
    - Current step name
    - Human-readable message
    - Estimated remaining time
    - Continuous updates
    """

    def __init__(self) -> None:
        """Initialize progress tracker."""
        self._progress: dict[str, ProgressUpdate] = {}
        self._history: dict[str, list[ProgressUpdate]] = {}
        self._start_times: dict[str, float] = {}

    def start_tracking(self, task_id: str) -> None:
        """Start tracking progress for a task."""
        self._start_times[task_id] = time.time()
        self._progress[task_id] = ProgressUpdate(task_id=task_id)
        self._history[task_id] = []

    def update(
        self,
        task_id: str,
        progress: float,
        current_step: str = "",
        message: str = "",
        estimated_remaining: float | None = None,
    ) -> ProgressUpdate:
        """Update task progress.

        Args:
            task_id: Task identifier.
            progress: Progress percentage (0-100).
            current_step: Name of current step.
            message: Human-readable message.
            estimated_remaining: Estimated remaining time in seconds.

        Returns:
            The progress update record.
        """
        progress = max(0.0, min(100.0, progress))

        update = ProgressUpdate(
            task_id=task_id,
            progress=progress,
            current_step=current_step,
            message=message,
            estimated_remaining=estimated_remaining,
        )

        self._progress[task_id] = update

        if task_id not in self._history:
            self._history[task_id] = []
        self._history[task_id].append(update)

        return update

    def get_progress(self, task_id: str) -> dict[str, Any]:
        """Get current progress for a task."""
        update = self._progress.get(task_id)
        if update is None:
            return {
                "progress": 0.0,
                "current_step": "",
                "message": "",
                "estimated_remaining": None,
                "elapsed": 0.0,
            }

        start = self._start_times.get(task_id, time.time())
        elapsed = time.time() - start

        return {
            "progress": update.progress,
            "current_step": update.current_step,
            "message": update.message,
            "estimated_remaining": update.estimated_remaining,
            "elapsed": elapsed,
        }

    def get_history(self, task_id: str) -> list[dict[str, Any]]:
        """Get progress history for a task."""
        history = self._history.get(task_id, [])
        return [
            {
                "progress": h.progress,
                "current_step": h.current_step,
                "message": h.message,
                "estimated_remaining": h.estimated_remaining,
                "timestamp": h.timestamp,
            }
            for h in history
        ]

    def stop_tracking(self, task_id: str) -> None:
        """Stop tracking progress for a task."""
        self._progress.pop(task_id, None)
        self._start_times.pop(task_id, None)

    def is_tracking(self, task_id: str) -> bool:
        """Check if a task is being tracked."""
        return task_id in self._progress

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tracked_tasks": len(self._progress),
            "tasks": {
                tid: {
                    "progress": p.progress,
                    "current_step": p.current_step,
                }
                for tid, p in self._progress.items()
            },
        }
