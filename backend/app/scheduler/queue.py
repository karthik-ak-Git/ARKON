"""Task queue with priority ordering."""

from __future__ import annotations

import bisect
import time
from dataclasses import dataclass, field

from app.scheduler.interfaces import Task, TaskState


class TaskQueue:
    """Priority-ordered task queue."""

    def __init__(self, max_size: int = 10000) -> None:
        self._max_size = max_size
        self._tasks: dict[str, Task] = {}
        self._order: list[str] = []
        self._enqueue_times: dict[str, float] = {}

    def enqueue(self, task: Task) -> bool:
        """Add task to queue. Returns False if full."""
        if len(self._tasks) >= self._max_size:
            return False
        if task.task_id in self._tasks:
            return False
        self._tasks[task.task_id] = task
        self._enqueue_times[task.task_id] = time.time()
        self._insert_sorted(task)
        return True

    def dequeue(self) -> Task | None:
        """Remove and return highest priority task."""
        if not self._order:
            return None
        task_id = self._order.pop(0)
        task = self._tasks.pop(task_id, None)
        self._enqueue_times.pop(task_id, None)
        if task:
            task.state = TaskState.DISPATCHING
        return task

    def peek(self) -> Task | None:
        """Return highest priority task without removing."""
        if not self._order:
            return None
        return self._tasks.get(self._order[0])

    def remove(self, task_id: str) -> Task | None:
        """Remove a specific task."""
        task = self._tasks.pop(task_id, None)
        if task_id in self._order:
            self._order.remove(task_id)
        self._enqueue_times.pop(task_id, None)
        return task

    def contains(self, task_id: str) -> bool:
        return task_id in self._tasks

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def size(self) -> int:
        return len(self._tasks)

    def is_empty(self) -> bool:
        return len(self._tasks) == 0

    def is_full(self) -> bool:
        return len(self._tasks) >= self._max_size

    def get_all(self) -> list[Task]:
        return [self._tasks[tid] for tid in self._order if tid in self._tasks]

    def get_by_state(self, state: TaskState) -> list[Task]:
        return [t for t in self._tasks.values() if t.state == state]

    def get_wait_time(self, task_id: str) -> float | None:
        enqueue_time = self._enqueue_times.get(task_id)
        if enqueue_time is None:
            return None
        return time.time() - enqueue_time

    def update_priority(self, task_id: str, new_priority: int) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.priority = new_priority
        if task_id in self._order:
            self._order.remove(task_id)
        self._insert_sorted(task)
        return True

    def clear(self) -> None:
        self._tasks.clear()
        self._order.clear()
        self._enqueue_times.clear()

    def to_dict(self) -> dict:
        return {
            "size": self.size(),
            "max_size": self._max_size,
            "tasks": [t.to_dict() for t in self.get_all()],
        }

    def _insert_sorted(self, task: Task) -> None:
        """Insert task maintaining sort order: priority (asc), then created_at (asc)."""
        key = (task.priority, task.created_at)
        lo = 0
        hi = len(self._order)
        while lo < hi:
            mid = (lo + hi) // 2
            mid_task = self._tasks.get(self._order[mid])
            if mid_task is None:
                hi = mid
                continue
            mid_key = (mid_task.priority, mid_task.created_at)
            if mid_key <= key:
                lo = mid + 1
            else:
                hi = mid
        self._order.insert(lo, task.task_id)
