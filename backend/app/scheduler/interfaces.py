"""Scheduler interfaces and types."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


class TaskState(enum.Enum):
    """Task lifecycle states."""

    PENDING = "pending"
    QUEUED = "queued"
    WAITING_DEPS = "waiting_deps"
    READY = "ready"
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"
    PREEMPTED = "preempted"


TASK_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.PENDING: {TaskState.QUEUED, TaskState.CANCELLED},
    TaskState.QUEUED: {TaskState.WAITING_DEPS, TaskState.READY, TaskState.DEFERRED, TaskState.CANCELLED},
    TaskState.WAITING_DEPS: {TaskState.READY, TaskState.DEFERRED, TaskState.CANCELLED},
    TaskState.READY: {TaskState.DISPATCHING, TaskState.PREEMPTED, TaskState.CANCELLED},
    TaskState.DISPATCHING: {TaskState.EXECUTING, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.EXECUTING: {TaskState.PAUSED, TaskState.COMPLETED, TaskState.FAILED, TaskState.PREEMPTED},
    TaskState.PAUSED: {TaskState.READY, TaskState.CANCELLED},
    TaskState.PREEMPTED: {TaskState.QUEUED, TaskState.READY},
    TaskState.COMPLETED: set(),
    TaskState.FAILED: {TaskState.QUEUED},
    TaskState.CANCELLED: set(),
    TaskState.DEFERRED: {TaskState.QUEUED},
}


class SchedulingPolicy(enum.Enum):
    """Supported scheduling policies."""

    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"
    DEADLINE = "deadline"
    FAIR_SHARE = "fair_share"
    WEIGHTED = "weighted"
    ROUND_ROBIN = "round_robin"
    SHORTEST_JOB_FIRST = "shortest_job_first"
    LONGEST_JOB_FIRST = "longest_job_first"


class LoadBalancingStrategy(enum.Enum):
    """Load balancing strategies."""

    LEAST_LOADED = "least_loaded"
    LEAST_BUSY = "least_busy"
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    CAPABILITY_SCORE = "capability_score"


class PreemptionMode(enum.Enum):
    """Preemption modes."""

    NONE = "none"
    PRIORITY_BASED = "priority_based"
    AGE_BASED = "age_based"
    BOTH = "both"


class BackpressureMode(enum.Enum):
    """Backpressure modes."""

    NONE = "none"
    THROTTLE = "throttle"
    REJECT = "reject"
    DELAY = "delay"
    ADAPTIVE = "adaptive"


class DependencyType(enum.Enum):
    """Dependency types between tasks."""

    PARENT = "parent"
    CHILD = "child"
    BARRIER = "barrier"
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"


class ConstraintType(enum.Enum):
    """Constraint types."""

    WORKSPACE_AFFINITY = "workspace_affinity"
    CAPABILITY_REQUIREMENT = "capability_requirement"
    RESOURCE_REQUIREMENT = "resource_requirement"
    TIME_WINDOW = "time_window"
    MAX_CONCURRENCY = "max_concurrency"
    EXECUTION_LIMIT = "execution_limit"
    CUSTOM = "custom"


@dataclass
class Task:
    """A schedulable task."""

    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = ""
    capability: str = ""
    priority: int = 5
    weight: float = 1.0
    estimated_duration: float | None = None
    deadline: float | None = None
    workspace_id: str | None = None
    resource_requirements: dict[str, float] = field(default_factory=dict)
    capability_requirements: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.PARENT
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    state: TaskState = TaskState.PENDING
    created_at: float = field(default_factory=lambda: __import__("time").time())
    scheduled_at: float | None = None
    dispatched_at: float | None = None
    started_at: float | None = None
    completed_at: float | None = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float | None = None
    group_id: str | None = None
    custom_constraints: dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.state in {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "capability": self.capability,
            "priority": self.priority,
            "weight": self.weight,
            "estimated_duration": self.estimated_duration,
            "deadline": self.deadline,
            "workspace_id": self.workspace_id,
            "resource_requirements": self.resource_requirements,
            "capability_requirements": self.capability_requirements,
            "dependencies": self.dependencies,
            "dependency_type": self.dependency_type.value,
            "metadata": self.metadata,
            "tags": self.tags,
            "payload": self.payload,
            "state": self.state.value,
            "created_at": self.created_at,
            "scheduled_at": self.scheduled_at,
            "dispatched_at": self.dispatched_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "group_id": self.group_id,
            "custom_constraints": self.custom_constraints,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        data = dict(data)
        data["state"] = TaskState(data.get("state", "pending"))
        data["dependency_type"] = DependencyType(data.get("dependency_type", "parent"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SchedulingDecision:
    """A record of a scheduling decision."""

    decision_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    task_id: str = ""
    action: str = ""  # queued, dispatched, deferred, preempted, rejected
    reason: str = ""
    target: str | None = None  # execution target
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerStatus:
    """Scheduler operational status."""

    is_running: bool = False
    is_paused: bool = False
    queue_size: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    deferred_tasks: int = 0
    overloaded: bool = False
    policy: str = "fifo"
    preemption_mode: str = "none"
    backpressure_mode: str = "none"
