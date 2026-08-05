"""ARKON Execution Engine - Cancellation System.

Task cancellation with proper resource cleanup.
"""

from __future__ import annotations

import time
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class CancellationManager:
    """Manages task cancellation.

    Supports:
    - Graceful cancellation
    - Immediate cancellation
    - Cancellation propagation
    - Cleanup callbacks
    """

    def __init__(self) -> None:
        """Initialize cancellation manager."""
        self._cancelled: set[str] = set()
        self._callbacks: dict[str, list[Any]] = {}
        self._cancel_history: list[dict[str, Any]] = []

    def request_cancellation(
        self,
        task_id: str,
        reason: str = "",
        immediate: bool = False,
    ) -> dict[str, Any]:
        """Request task cancellation.

        Args:
            task_id: Task to cancel.
            reason: Cancellation reason.
            immediate: If True, skip graceful shutdown.

        Returns:
            Cancellation record.
        """
        self._cancelled.add(task_id)

        record = {
            "task_id": task_id,
            "reason": reason,
            "immediate": immediate,
            "cancelled_at": time.time(),
        }

        self._cancel_history.append(record)

        logger.info(
            "task_cancellation_requested",
            task_id=task_id,
            reason=reason,
            immediate=immediate,
        )

        return record

    def is_cancelled(self, task_id: str) -> bool:
        """Check if a task has been cancelled."""
        return task_id in self._cancelled

    def acknowledge_cancellation(self, task_id: str) -> None:
        """Acknowledge that cancellation has been processed."""
        self._cancelled.discard(task_id)

    def register_cleanup(self, task_id: str, callback: Any) -> None:
        """Register a cleanup callback for cancellation.

        Args:
            task_id: Task identifier.
            callback: Async callable to run on cancellation.
        """
        if task_id not in self._callbacks:
            self._callbacks[task_id] = []
        self._callbacks[task_id].append(callback)

    async def execute_cleanup(self, task_id: str) -> None:
        """Execute all cleanup callbacks for a task."""
        callbacks = self._callbacks.pop(task_id, [])
        for callback in callbacks:
            try:
                if callable(callback):
                    import asyncio
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
            except Exception as e:
                logger.error(
                    "cleanup_callback_failed",
                    task_id=task_id,
                    error=str(e),
                )

    def get_cancelled_tasks(self) -> set[str]:
        """Get all cancelled task IDs."""
        return self._cancelled.copy()

    def get_history(self, task_id: str | None = None) -> list[dict[str, Any]]:
        """Get cancellation history."""
        if task_id:
            return [r for r in self._cancel_history if r["task_id"] == task_id]
        return self._cancel_history.copy()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cancelled_count": len(self._cancelled),
            "cancelled_tasks": list(self._cancelled),
        }
