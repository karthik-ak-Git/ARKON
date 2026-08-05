"""Constraint checking for tasks."""

from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field

from app.scheduler.interfaces import ConstraintType, Task


@dataclass
class ConstraintResult:
    """Result of a constraint check."""

    satisfied: bool = True
    reason: str = ""
    constraint_type: ConstraintType = ConstraintType.CUSTOM


class Constraint(abc.ABC):
    """Base constraint."""

    @property
    @abc.abstractmethod
    def constraint_type(self) -> ConstraintType:
        ...

    @abc.abstractmethod
    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        ...


class WorkspaceAffinityConstraint(Constraint):
    """Ensures task runs in compatible workspace."""

    def __init__(self, allowed_workspaces: list[str] | None = None) -> None:
        self._allowed = set(allowed_workspaces) if allowed_workspaces else set()

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.WORKSPACE_AFFINITY

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        if not self._allowed:
            return ConstraintResult(satisfied=True)
        if task.workspace_id and task.workspace_id in self._allowed:
            return ConstraintResult(satisfied=True)
        if not task.workspace_id:
            return ConstraintResult(satisfied=True)
        return ConstraintResult(
            satisfied=False,
            reason=f"Workspace {task.workspace_id} not in allowed set",
            constraint_type=self.constraint_type,
        )


class CapabilityConstraint(Constraint):
    """Ensures task's capability requirements can be met."""

    def __init__(self, available_capabilities: set[str] | None = None) -> None:
        self._available = available_capabilities or set()

    def set_available(self, capabilities: set[str]) -> None:
        self._available = capabilities

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.CAPABILITY_REQUIREMENT

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        if not task.capability_requirements:
            return ConstraintResult(satisfied=True)
        missing = set(task.capability_requirements) - self._available
        if missing:
            return ConstraintResult(
                satisfied=False,
                reason=f"Missing capabilities: {missing}",
                constraint_type=self.constraint_type,
            )
        return ConstraintResult(satisfied=True)


class ResourceConstraint(Constraint):
    """Ensures resource requirements can be met."""

    def __init__(self, available_resources: dict[str, float] | None = None) -> None:
        self._available = dict(available_resources) if available_resources else {}

    def set_available(self, resources: dict[str, float]) -> None:
        self._available = dict(resources)

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.RESOURCE_REQUIREMENT

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        if not task.resource_requirements:
            return ConstraintResult(satisfied=True)
        for res, required in task.resource_requirements.items():
            available = self._available.get(res, 0.0)
            if available < required:
                return ConstraintResult(
                    satisfied=False,
                    reason=f"Insufficient {res}: need {required}, have {available}",
                    constraint_type=self.constraint_type,
                )
        return ConstraintResult(satisfied=True)


class TimeWindowConstraint(Constraint):
    """Ensures task runs within allowed time window."""

    def __init__(self, allowed_start: float | None = None, allowed_end: float | None = None) -> None:
        self._start = allowed_start
        self._end = allowed_end

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.TIME_WINDOW

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        now = time.time()
        if self._start and now < self._start:
            return ConstraintResult(
                satisfied=False,
                reason=f"Too early: window opens at {self._start}",
                constraint_type=self.constraint_type,
            )
        if self._end and now > self._end:
            return ConstraintResult(
                satisfied=False,
                reason=f"Too late: window closed at {self._end}",
                constraint_type=self.constraint_type,
            )
        return ConstraintResult(satisfied=True)


class ConcurrencyConstraint(Constraint):
    """Limits max concurrent tasks matching a pattern."""

    def __init__(self, max_concurrent: int = 1, pattern: str | None = None) -> None:
        self._max = max_concurrent
        self._pattern = pattern
        self._running: dict[str, int] = {}

    def add_running(self, key: str) -> None:
        self._running[key] = self._running.get(key, 0) + 1

    def remove_running(self, key: str) -> None:
        if key in self._running:
            self._running[key] = max(0, self._running[key] - 1)
            if self._running[key] == 0:
                del self._running[key]

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.MAX_CONCURRENCY

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        key = task.group_id or task.capability or "global"
        current = self._running.get(key, 0)
        if current >= self._max:
            return ConstraintResult(
                satisfied=False,
                reason=f"Concurrency limit {self._max} reached for {key}",
                constraint_type=self.constraint_type,
            )
        return ConstraintResult(satisfied=True)


class ExecutionLimitConstraint(Constraint):
    """Limits total execution time or count."""

    def __init__(self, max_executions: int | None = None, max_total_time: float | None = None) -> None:
        self._max_executions = max_executions
        self._max_total_time = max_total_time
        self._execution_count = 0
        self._total_time = 0.0

    def record_execution(self, duration: float) -> None:
        self._execution_count += 1
        self._total_time += duration

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.EXECUTION_LIMIT

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        if self._max_executions and self._execution_count >= self._max_executions:
            return ConstraintResult(
                satisfied=False,
                reason=f"Execution limit {self._max_executions} reached",
                constraint_type=self.constraint_type,
            )
        if self._max_total_time and self._total_time >= self._max_total_time:
            return ConstraintResult(
                satisfied=False,
                reason=f"Total time limit {self._max_total_time}s reached",
                constraint_type=self.constraint_type,
            )
        return ConstraintResult(satisfied=True)


class CustomConstraint(Constraint):
    """User-provided constraint function."""

    def __init__(self, name: str, check_fn: any) -> None:
        self._name = name
        self._check_fn = check_fn

    @property
    def constraint_type(self) -> ConstraintType:
        return ConstraintType.CUSTOM

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        result = self._check_fn(task, context)
        if isinstance(result, ConstraintResult):
            return result
        return ConstraintResult(satisfied=bool(result), reason=str(result) if not result else "")


class ConstraintChain:
    """Chain of constraints checked in order."""

    def __init__(self) -> None:
        self._constraints: list[Constraint] = []

    def add(self, constraint: Constraint) -> None:
        self._constraints.append(constraint)

    def remove(self, constraint_type: ConstraintType) -> None:
        self._constraints = [c for c in self._constraints if c.constraint_type != constraint_type]

    def check_all(self, task: Task, context: dict | None = None) -> list[ConstraintResult]:
        results = []
        for c in self._constraints:
            result = c.check(task, context)
            results.append(result)
        return results

    def check(self, task: Task, context: dict | None = None) -> ConstraintResult:
        """Check all constraints. Returns first failure or success."""
        for c in self._constraints:
            result = c.check(task, context)
            if not result.satisfied:
                return result
        return ConstraintResult(satisfied=True)

    def clear(self) -> None:
        self._constraints.clear()
