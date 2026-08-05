"""High-level load balancer - wraps strategy for task dispatch."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.scheduler.interfaces import LoadBalancingStrategy, Task
from app.scheduler.strategy import LoadBalancer, Target, create_balancer


@dataclass
class DispatchRecord:
    """Record of a dispatch decision."""

    task_id: str
    target_id: str
    timestamp: float = field(default_factory=time.time)


class TaskBalancer:
    """High-level load balancer for task dispatch."""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED) -> None:
        self._strategy = strategy
        self._balancer: LoadBalancer = create_balancer(strategy)
        self._targets: dict[str, Target] = {}
        self._history: list[DispatchRecord] = []

    @property
    def strategy(self) -> LoadBalancingStrategy:
        return self._strategy

    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        self._strategy = strategy
        self._balancer = create_balancer(strategy)

    def register_target(self, target: Target) -> None:
        self._targets[target.target_id] = target

    def unregister_target(self, target_id: str) -> None:
        self._targets.pop(target_id, None)

    def get_target(self, target_id: str) -> Target | None:
        return self._targets.get(target_id)

    def get_targets(self) -> list[Target]:
        return list(self._targets.values())

    def select_target(self, task: Task) -> Target | None:
        """Select best target for a task."""
        targets = list(self._targets.values())
        required = set(task.capability_requirements) if task.capability_requirements else None
        return self._balancer.select(targets, required)

    def record_dispatch(self, task_id: str, target_id: str) -> None:
        self._history.append(DispatchRecord(task_id=task_id, target_id=target_id))
        target = self._targets.get(target_id)
        if target:
            target.active_tasks += 1

    def record_completion(self, target_id: str) -> None:
        target = self._targets.get(target_id)
        if target:
            target.active_tasks = max(0, target.active_tasks - 1)

    def update_target_load(self, target_id: str, load: float) -> None:
        target = self._targets.get(target_id)
        if target:
            target.load = load

    def get_history(self) -> list[DispatchRecord]:
        return list(self._history)

    def to_dict(self) -> dict:
        return {
            "strategy": self._strategy.value,
            "targets": {tid: {"load": t.load, "capacity": t.capacity, "active": t.active_tasks} for tid, t in self._targets.items()},
            "history_size": len(self._history),
        }
