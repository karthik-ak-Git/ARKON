"""ARKON Execution Engine - Task Queue.

Priority-based task queue for execution scheduling.
"""

from __future__ import annotations

import heapq
import time
from typing import Any

import structlog

from app.execution.interfaces import ITask

logger = structlog.get_logger(__name__)


class TaskQueue:
    """Priority-based task queue.

    Tasks are ordered by:
    1. Priority (lower number = higher priority)
    2. Creation time (FIFO within same priority)
    """

    def __init__(self) -> None:
        """Initialize task queue."""
        self._heap: list[tuple[int, float, str, ITask]] = []
        self._tasks: dict[str, ITask] = {}
        self._counter = 0

    async def enqueue(self, task: ITask) -> None:
        """Add a task to the queue."""
        task_id = task.get_id()
        if task_id in self._tasks:
            logger.warning("task_already_queued", task_id=task_id)
            return

        self._counter += 1
        entry = (task.get_priority(), time.time(), task_id, task)
        heapq.heappush(self._heap, entry)
        self._tasks[task_id] = task

        logger.debug("task_enqueued", task_id=task_id, priority=task.get_priority())

    async def dequeue(self) -> ITask | None:
        """Remove the highest priority task from the queue."""
        while self._heap:
            priority, timestamp, task_id, task = heapq.heappop(self._heap)
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.debug("task_dequeued", task_id=task_id)
                return task
        return None

    async def peek(self) -> ITask | None:
        """View the next task without removing."""
        while self._heap:
            priority, timestamp, task_id, task = self._heap[0]
            if task_id in self._tasks:
                return task
            heapq.heappop(self._heap)
        return None

    async def size(self) -> int:
        """Get queue size."""
        return len(self._tasks)

    async def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._tasks) == 0

    async def remove(self, task_id: str) -> bool:
        """Remove a specific task from the queue."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.debug("task_removed_from_queue", task_id=task_id)
            return True
        return False

    async def contains(self, task_id: str) -> bool:
        """Check if a task is in the queue."""
        return task_id in self._tasks

    async def get_task(self, task_id: str) -> ITask | None:
        """Get a task by ID without removing."""
        return self._tasks.get(task_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "size": len(self._tasks),
            "task_ids": list(self._tasks.keys()),
        }
