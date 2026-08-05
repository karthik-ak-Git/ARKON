"""Dispatcher - routes tasks to execution targets."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from app.scheduler.balancer import TaskBalancer
from app.scheduler.interfaces import LoadBalancingStrategy, Task, TaskState
from app.scheduler.strategy import Target


@dataclass
class DispatchResult:
    """Result of a dispatch attempt."""

    success: bool
    task_id: str = ""
    target_id: str = ""
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "target_id": self.target_id,
            "reason": self.reason,
        }


class Dispatcher:
    """Dispatches tasks to execution targets."""

    def __init__(self, balancer: TaskBalancer | None = None) -> None:
        self._balancer = balancer or TaskBalancer()
        self._dispatch_history: list[DispatchResult] = []
        self._on_dispatch: Callable[[Task, Target], None] | None = None
        self._on_failure: Callable[[Task, str], None] | None = None

    @property
    def balancer(self) -> TaskBalancer:
        return self._balancer

    def on_dispatch(self, callback: Callable[[Task, Target], None]) -> None:
        self._on_dispatch = callback

    def on_failure(self, callback: Callable[[Task, str], None]) -> None:
        self._on_failure = callback

    def dispatch(self, task: Task) -> DispatchResult:
        """Dispatch a single task to a target."""
        if task.state not in (TaskState.QUEUED, TaskState.DISPATCHING, TaskState.WAITING_DEPS):
            return DispatchResult(
                success=False,
                task_id=task.task_id,
                reason=f"Task in invalid state: {task.state.value}",
            )

        target = self._balancer.select_target(task)
        if not target:
            result = DispatchResult(
                success=False,
                task_id=task.task_id,
                reason="No suitable target available",
            )
            self._dispatch_history.append(result)
            if self._on_failure:
                self._on_failure(task, result.reason)
            return result

        task.state = TaskState.EXECUTING
        task.started_at = time.time()
        task.assigned_target = target.target_id

        self._balancer.record_dispatch(task.task_id, target.target_id)

        result = DispatchResult(
            success=True,
            task_id=task.task_id,
            target_id=target.target_id,
        )
        self._dispatch_history.append(result)

        if self._on_dispatch:
            self._on_dispatch(task, target)

        return result

    def dispatch_batch(self, tasks: list[Task]) -> list[DispatchResult]:
        results = []
        for task in tasks:
            result = self.dispatch(task)
            results.append(result)
        return results

    def complete(self, task_id: str, target_id: str, success: bool = True) -> None:
        """Record task completion."""
        self._balancer.record_completion(target_id)

    def get_history(self) -> list[DispatchResult]:
        return list(self._dispatch_history)

    def get_success_rate(self) -> float:
        if not self._dispatch_history:
            return 0.0
        successes = sum(1 for r in self._dispatch_history if r.success)
        return successes / len(self._dispatch_history)

    def to_dict(self) -> dict:
        return {
            "balancer": self._balancer.to_dict(),
            "dispatch_count": len(self._dispatch_history),
            "success_rate": self.get_success_rate(),
        }
