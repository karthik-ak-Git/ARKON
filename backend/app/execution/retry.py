"""ARKON Execution Engine - Retry System.

Supports multiple retry policies with configurable behavior.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import structlog

from app.execution.interfaces import RetryPolicy

logger = structlog.get_logger(__name__)


class RetryManager:
    """Manages task retry logic.

    Supports:
    - Immediate retry
    - Fixed delay
    - Exponential backoff
    - Maximum attempts
    - Custom retry predicates
    """

    def __init__(self) -> None:
        """Initialize retry manager."""
        self._retry_history: dict[str, list[dict[str, Any]]] = {}
        self._predicates: dict[str, Callable[[Exception], bool]] = {}

    def register_predicate(
        self, task_id: str, predicate: Callable[[Exception], bool]
    ) -> None:
        """Register a custom retry predicate for a task.

        Args:
            task_id: Task identifier.
            predicate: Function that returns True if retry should be attempted.
        """
        self._predicates[task_id] = predicate

    def should_retry(
        self,
        task_id: str,
        attempt: int,
        max_retries: int,
        error: Exception | None = None,
    ) -> bool:
        """Check if a task should be retried.

        Args:
            task_id: Task identifier.
            attempt: Current attempt number.
            max_retries: Maximum retry attempts.
            error: The error that caused failure.

        Returns:
            True if retry should be attempted.
        """
        if attempt >= max_retries:
            return False

        if error is not None and task_id in self._predicates:
            return self._predicates[task_id](error)

        return True

    def get_delay(
        self,
        policy: RetryPolicy,
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
    ) -> float:
        """Calculate delay before next retry.

        Args:
            policy: Retry policy type.
            attempt: Current attempt number.
            base_delay: Base delay in seconds.
            max_delay: Maximum delay in seconds.
            backoff_multiplier: Backoff multiplier.

        Returns:
            Delay in seconds.
        """
        if policy == RetryPolicy.IMMEDIATE:
            return 0.0
        elif policy == RetryPolicy.FIXED_DELAY:
            return min(base_delay, max_delay)
        elif policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (backoff_multiplier ** attempt)
            return min(delay, max_delay)
        return 0.0

    def record_retry(
        self,
        task_id: str,
        attempt: int,
        error: str,
        delay: float,
    ) -> None:
        """Record a retry attempt.

        Args:
            task_id: Task identifier.
            attempt: Attempt number.
            error: Error message.
            delay: Delay before retry.
        """
        if task_id not in self._retry_history:
            self._retry_history[task_id] = []

        self._retry_history[task_id].append({
            "attempt": attempt,
            "error": error,
            "delay": delay,
            "timestamp": time.time(),
        })

    def get_history(self, task_id: str) -> list[dict[str, Any]]:
        """Get retry history for a task."""
        return self._retry_history.get(task_id, []).copy()

    def clear_history(self, task_id: str) -> None:
        """Clear retry history for a task."""
        self._retry_history.pop(task_id, None)
        self._predicates.pop(task_id, None)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tasks_with_retries": len(self._retry_history),
            "total_retries": sum(
                len(r) for r in self._retry_history.values()
            ),
        }
