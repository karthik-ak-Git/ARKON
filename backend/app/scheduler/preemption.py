"""Preemption - pausing lower priority tasks for higher priority."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.scheduler.interfaces import PreemptionMode, Task, TaskState


@dataclass
class PreemptionEvent:
    """Record of a preemption action."""

    preempted_task_id: str
    promoted_task_id: str
    preempted_priority: int
    promoted_priority: int
    timestamp: float = field(default_factory=time.time)


class PreemptionManager:
    """Manages task preemption and priority aging."""

    def __init__(
        self,
        mode: PreemptionMode = PreemptionMode.PRIORITY_BASED,
        aging_enabled: bool = True,
        aging_interval: float = 60.0,
        max_aging_boost: int = 5,
    ) -> None:
        self._mode = mode
        self._aging_enabled = aging_enabled
        self._aging_interval = aging_interval
        self._max_aging_boost = max_aging_boost
        self._preemption_history: list[PreemptionEvent] = []
        self._original_priorities: dict[str, int] = {}
        self._aging_counters: dict[str, int] = {}
        self._last_aging_check: dict[str, float] = {}

    @property
    def mode(self) -> PreemptionMode:
        return self._mode

    def set_mode(self, mode: PreemptionMode) -> None:
        self._mode = mode

    def should_preempt(self, running_task: Task, new_task: Task) -> bool:
        """Determine if running task should be preempted."""
        if self._mode == PreemptionMode.NONE:
            return False
        if new_task.priority >= running_task.priority:
            return False
        if running_task.state not in (TaskState.EXECUTING, TaskState.READY):
            return False
        return True

    def preempt(self, running_task: Task, new_task: Task) -> PreemptionEvent | None:
        """Attempt to preempt a running task."""
        if not self.should_preempt(running_task, new_task):
            return None

        event = PreemptionEvent(
            preempted_task_id=running_task.task_id,
            promoted_task_id=new_task.task_id,
            preempted_priority=running_task.priority,
            promoted_priority=new_task.priority,
        )
        self._preemption_history.append(event)

        if self._mode in (PreemptionMode.PRIORITY_BASED, PreemptionMode.BOTH):
            running_task.state = TaskState.PAUSED
            self._original_priorities[running_task.task_id] = running_task.priority
        elif self._mode == PreemptionMode.AGE_BASED:
            running_task.state = TaskState.PAUSED
            self._original_priorities[running_task.task_id] = running_task.priority

        return event

    def resume_task(self, task: Task) -> None:
        """Resume a paused task."""
        if task.state == TaskState.PAUSED:
            task.state = TaskState.READY
            original = self._original_priorities.pop(task.task_id, None)
            if original is not None:
                task.priority = original

    def cancel_task(self, task: Task) -> None:
        """Cancel a paused task."""
        if task.state in (TaskState.PAUSED, TaskState.QUEUED, TaskState.READY):
            task.state = TaskState.CANCELLED

    def apply_aging(self, tasks: list[Task]) -> list[Task]:
        """Apply priority aging to tasks waiting too long."""
        if not self._aging_enabled:
            return tasks

        now = time.time()
        aged: list[Task] = []

        for task in tasks:
            if task.state not in (TaskState.QUEUED, TaskState.READY, TaskState.WAITING_DEPS):
                continue

            last_check = self._last_aging_check.get(task.task_id, task.created_at)
            elapsed = now - last_check
            intervals = elapsed / self._aging_interval

            if intervals >= 1.0:
                boosts = min(int(intervals), self._max_aging_boost)
                current_boost = self._aging_counters.get(task.task_id, 0)
                new_boost = min(current_boost + boosts, self._max_aging_boost)
                delta = new_boost - current_boost

                if delta > 0:
                    task.priority = max(0, task.priority - delta)
                    self._aging_counters[task.task_id] = new_boost
                    self._last_aging_check[task.task_id] = now
                    aged.append(task)

        return aged

    def reset_aging(self, task_id: str) -> None:
        self._aging_counters.pop(task_id, None)
        self._last_aging_check.pop(task_id, None)
        self._original_priorities.pop(task_id, None)

    def get_history(self) -> list[PreemptionEvent]:
        return list(self._preemption_history)

    def is_starved(self, task: Task, threshold: float = 300.0) -> bool:
        """Check if task is being starved (waiting too long)."""
        wait_time = time.time() - task.created_at
        return wait_time > threshold and task.priority < 3

    def to_dict(self) -> dict:
        return {
            "mode": self._mode.value,
            "aging_enabled": self._aging_enabled,
            "aging_interval": self._aging_interval,
            "max_aging_boost": self._max_aging_boost,
            "preemption_count": len(self._preemption_history),
            "aged_tasks": len(self._aging_counters),
        }
