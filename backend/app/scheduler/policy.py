"""Scheduling policies - determines task ordering."""

from __future__ import annotations

import abc
import random
import time
from collections import deque

from app.scheduler.interfaces import SchedulingPolicy, Task


class Policy(abc.ABC):
    """Base scheduling policy."""

    @property
    @abc.abstractmethod
    def policy_type(self) -> SchedulingPolicy:
        ...

    @abc.abstractmethod
    def select(self, tasks: list[Task]) -> Task | None:
        """Select the next task to execute."""
        ...

    def sort(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in scheduling order."""
        return list(tasks)


class FIFOPolicy(Policy):
    """First In, First Out."""

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.FIFO

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        return min(tasks, key=lambda t: t.created_at)

    def sort(self, tasks: list[Task]) -> list[Task]:
        return sorted(tasks, key=lambda t: t.created_at)


class LIFOPolicy(Policy):
    """Last In, First Out."""

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.LIFO

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        return max(tasks, key=lambda t: t.created_at)


class PriorityPolicy(Policy):
    """Priority-based scheduling."""

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.PRIORITY

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        return min(tasks, key=lambda t: (t.priority, t.created_at))

    def sort(self, tasks: list[Task]) -> list[Task]:
        return sorted(tasks, key=lambda t: (t.priority, t.created_at))


class DeadlinePolicy(Policy):
    """Earliest deadline first."""

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.DEADLINE

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        with_deadline = [t for t in tasks if t.deadline is not None]
        if not with_deadline:
            return min(tasks, key=lambda t: t.created_at)
        return min(with_deadline, key=lambda t: t.deadline)


class FairSharePolicy(Policy):
    """Fair share scheduling - round-robin by group."""

    def __init__(self) -> None:
        self._group_counts: dict[str, int] = {}

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.FAIR_SHARE

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        groups: dict[str, list[Task]] = {}
        for t in tasks:
            gid = t.group_id or "default"
            groups.setdefault(gid, []).append(t)
        min_group = min(groups.keys(), key=lambda g: self._group_counts.get(g, 0))
        self._group_counts[min_group] = self._group_counts.get(min_group, 0) + 1
        return min(groups[min_group], key=lambda t: t.created_at)


class WeightedPolicy(Policy):
    """Weighted scheduling - higher weight tasks get preference."""

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.WEIGHTED

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        return max(tasks, key=lambda t: (t.weight, -t.created_at))


class RoundRobinPolicy(Policy):
    """Round-robin scheduling."""

    def __init__(self) -> None:
        self._index = 0

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.ROUND_ROBIN

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        sorted_tasks = sorted(tasks, key=lambda t: t.created_at)
        idx = self._index % len(sorted_tasks)
        self._index += 1
        return sorted_tasks[idx]


class ShortestJobFirstPolicy(Policy):
    """Shortest estimated duration first."""

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.SHORTEST_JOB_FIRST

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        with_duration = [t for t in tasks if t.estimated_duration is not None]
        if not with_duration:
            return min(tasks, key=lambda t: t.created_at)
        return min(with_duration, key=lambda t: t.estimated_duration)


class LongestJobFirstPolicy(Policy):
    """Longest estimated duration first."""

    @property
    def policy_type(self) -> SchedulingPolicy:
        return SchedulingPolicy.LONGEST_JOB_FIRST

    def select(self, tasks: list[Task]) -> Task | None:
        if not tasks:
            return None
        with_duration = [t for t in tasks if t.estimated_duration is not None]
        if not with_duration:
            return min(tasks, key=lambda t: t.created_at)
        return max(with_duration, key=lambda t: t.estimated_duration)


POLICY_MAP: dict[SchedulingPolicy, type[Policy]] = {
    SchedulingPolicy.FIFO: FIFOPolicy,
    SchedulingPolicy.LIFO: LIFOPolicy,
    SchedulingPolicy.PRIORITY: PriorityPolicy,
    SchedulingPolicy.DEADLINE: DeadlinePolicy,
    SchedulingPolicy.FAIR_SHARE: FairSharePolicy,
    SchedulingPolicy.WEIGHTED: WeightedPolicy,
    SchedulingPolicy.ROUND_ROBIN: RoundRobinPolicy,
    SchedulingPolicy.SHORTEST_JOB_FIRST: ShortestJobFirstPolicy,
    SchedulingPolicy.LONGEST_JOB_FIRST: LongestJobFirstPolicy,
}


def create_policy(policy_type: SchedulingPolicy) -> Policy:
    cls = POLICY_MAP.get(policy_type)
    if cls is None:
        raise ValueError(f"Unknown policy: {policy_type}")
    return cls()
