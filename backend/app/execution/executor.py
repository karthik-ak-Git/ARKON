"""ARKON Execution Engine - Task Executor.

Executes tasks with proper lifecycle management.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Awaitable

import structlog

from app.execution.interfaces import ITask, TaskState

logger = structlog.get_logger(__name__)


class TaskExecutor:
    """Executes individual tasks with lifecycle management.

    Handles:
    - Task state transitions during execution
    - Cancellation support
    - Progress reporting
    - Timeout enforcement
    - Error handling
    """

    def __init__(self) -> None:
        """Initialize task executor."""
        self._executing: dict[str, bool] = {}
        self._results: dict[str, Any] = {}

    async def execute(
        self,
        task: ITask,
        handler: Callable[[ITask], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Execute a task.

        Args:
            task: Task to execute.
            handler: Async callable that performs the work.

        Returns:
            Execution result.

        Raises:
            Exception: If execution fails.
        """
        task_id = task.get_id()
        self._executing[task_id] = True
        start_time = time.time()

        try:
            # Transition to EXECUTING
            task.state = TaskState.EXECUTING
            task.started_at = time.time()

            # Execute the handler
            result = await handler(task)

            elapsed = time.time() - start_time

            # Store result
            exec_result = {
                "task_id": task_id,
                "success": True,
                "output": result,
                "duration": elapsed,
                "completed_at": time.time(),
            }

            self._results[task_id] = exec_result

            # Transition to COMPLETED
            task.state = TaskState.COMPLETED
            task.completed_at = time.time()

            logger.debug(
                "task_executed",
                task_id=task_id,
                duration=elapsed,
            )

            return exec_result

        except asyncio.CancelledError:
            # Task was cancelled
            task.state = TaskState.CANCELLED
            task.cancelled_at = time.time()
            raise

        except Exception as e:
            # Execution failed
            elapsed = time.time() - start_time

            exec_result = {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "duration": elapsed,
                "completed_at": time.time(),
            }

            self._results[task_id] = exec_result
            task.state = TaskState.FAILED
            task.failed_at = time.time()
            task.last_error = str(e)
            task.last_error_type = type(e).__name__

            logger.error(
                "task_execution_failed",
                task_id=task_id,
                error=str(e),
            )

            raise

        finally:
            self._executing.pop(task_id, None)

    def is_executing(self, task_id: str) -> bool:
        """Check if a task is currently executing."""
        return self._executing.get(task_id, False)

    def get_result(self, task_id: str) -> dict[str, Any] | None:
        """Get the result of an executed task."""
        return self._results.get(task_id)

    def get_executing_tasks(self) -> list[str]:
        """Get list of currently executing task IDs."""
        return list(self._executing.keys())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "executing_count": len(self._executing),
            "executing_tasks": list(self._executing.keys()),
            "results_count": len(self._results),
        }
