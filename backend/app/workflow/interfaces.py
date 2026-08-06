"""Workflow Runtime interfaces and types.

The Workflow Runtime describes, validates, compiles, and plans workflows.
It NEVER executes tasks, talks to agents, allocates resources, or calls AI models.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol


# ─────────────────────────────────────
# ENUMS
# ─────────────────────────────────────


class WorkflowState(enum.Enum):
    """Workflow lifecycle states."""

    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    COMPILING = "compiling"
    COMPILED = "compiled"
    PLANNING = "planning"
    PLANNED = "planned"
    FAILED = "failed"


class NodeState(enum.Enum):
    """Node lifecycle states."""

    PENDING = "pending"
    READY = "ready"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EdgeType(enum.Enum):
    """Edge dependency types."""

    DATA = "data"
    CONTROL = "control"
    BARRIER = "barrier"


class PortDirection(enum.Enum):
    """Port direction."""

    INPUT = "input"
    OUTPUT = "output"


class ConditionType(enum.Enum):
    """Condition evaluation types."""

    EXPRESSION = "expression"
    STATUS = "status"
    CUSTOM = "custom"


class LoopStrategy(enum.Enum):
    """Loop execution strategies."""

    FIXED = "fixed"
    UNTIL = "until"
    OVER = "over"


class WorkflowFormat(enum.Enum):
    """Supported workflow definition formats."""

    YAML = "yaml"
    JSON = "json"
    DSL = "dsl"


# ─────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────


@dataclass
class Port:
    """A node input or output port."""

    port_id: str = ""
    name: str = ""
    direction: PortDirection = PortDirection.INPUT
    data_type: str = "any"
    required: bool = True
    default: Any = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "port_id": self.port_id,
            "name": self.name,
            "direction": self.direction.value,
            "data_type": self.data_type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Port:
        data = dict(data)
        data["direction"] = PortDirection(data.get("direction", "input"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Condition:
    """A conditional branch on an edge or node."""

    condition_id: str = ""
    condition_type: ConditionType = ConditionType.EXPRESSION
    expression: str = ""
    target_node_id: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "condition_type": self.condition_type.value,
            "expression": self.expression,
            "target_node_id": self.target_node_id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Condition:
        data = dict(data)
        data["condition_type"] = ConditionType(data.get("condition_type", "expression"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LoopConfig:
    """Loop configuration for a node."""

    loop_id: str = ""
    strategy: LoopStrategy = LoopStrategy.FIXED
    max_iterations: int = 10
    until_expression: str = ""
    over_field: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "strategy": self.strategy.value,
            "max_iterations": self.max_iterations,
            "until_expression": self.until_expression,
            "over_field": self.over_field,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LoopConfig:
        data = dict(data)
        data["strategy"] = LoopStrategy(data.get("strategy", "fixed"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ParallelConfig:
    """Parallel execution configuration for a group of nodes."""

    parallel_id: str = ""
    node_ids: list[str] = field(default_factory=list)
    barrier_node_id: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "parallel_id": self.parallel_id,
            "node_ids": self.node_ids,
            "barrier_node_id": self.barrier_node_id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParallelConfig:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class WorkflowMetadata:
    """Workflow metadata."""

    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    format: WorkflowFormat = WorkflowFormat.YAML

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "format": self.format.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowMetadata:
        data = dict(data)
        data["format"] = WorkflowFormat(data.get("format", "yaml"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ExecutionPlanTask:
    """A single task in an execution plan.

    This is what gets submitted to the Scheduler.
    """

    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    node_id: str = ""
    name: str = ""
    capability: str = ""
    priority: int = 5
    estimated_duration: float | None = None
    timeout: float | None = None
    dependencies: list[str] = field(default_factory=list)
    resource_requirements: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "node_id": self.node_id,
            "name": self.name,
            "capability": self.capability,
            "priority": self.priority,
            "estimated_duration": self.estimated_duration,
            "timeout": self.timeout,
            "dependencies": self.dependencies,
            "resource_requirements": self.resource_requirements,
            "metadata": self.metadata,
            "payload": self.payload,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionPlanTask:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ExecutionPlan:
    """An execution plan produced by the compiler.

    This is consumed by the Scheduler.
    """

    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    workflow_id: str = ""
    workflow_name: str = ""
    version: str = ""
    state: WorkflowState = WorkflowState.DRAFT
    tasks: list[ExecutionPlanTask] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def get_task_by_node(self, node_id: str) -> ExecutionPlanTask | None:
        for task in self.tasks:
            if task.node_id == node_id:
                return task
        return None

    def get_dependencies(self, task_id: str) -> list[str]:
        for task in self.tasks:
            if task.task_id == task_id:
                return task.dependencies
        return []

    def topological_order(self) -> list[str]:
        """Return task IDs in topological order."""
        in_degree: dict[str, int] = {t.task_id: 0 for t in self.tasks}
        dependents: dict[str, list[str]] = {t.task_id: [] for t in self.tasks}

        for task in self.tasks:
            for dep_id in task.dependencies:
                if dep_id in dependents:
                    dependents[dep_id].append(task.task_id)
                    in_degree[task.task_id] += 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            queue.sort()
            tid = queue.pop(0)
            order.append(tid)
            for dep in dependents[tid]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        return order

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "version": self.version,
            "state": self.state.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionPlan:
        data = dict(data)
        data["state"] = WorkflowState(data.get("state", "draft"))
        data["tasks"] = [ExecutionPlanTask.from_dict(t) for t in data.get("tasks", [])]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ValidationResult:
    """Result of workflow validation."""

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# ─────────────────────────────────────
# PROTOCOLS
# ─────────────────────────────────────


class IWorkflowParser(Protocol):
    """Protocol for workflow parsers."""

    def parse(self, content: str, format: WorkflowFormat) -> dict[str, Any]: ...


class IWorkflowValidator(Protocol):
    """Protocol for workflow validators."""

    def validate(self, definition: dict[str, Any]) -> ValidationResult: ...


class IWorkflowCompiler(Protocol):
    """Protocol for workflow compilers."""

    def compile(self, definition: dict[str, Any]) -> ExecutionPlan: ...


class IWorkflowPlanner(Protocol):
    """Protocol for workflow planners."""

    def plan(self, execution_plan: ExecutionPlan) -> ExecutionPlan: ...
