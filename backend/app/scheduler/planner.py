"""DAG planning - dependency resolution and execution ordering."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.scheduler.exceptions import (
    DependencyCycleError,
    DependencyNotMetError,
    TaskNotFoundError,
)
from app.scheduler.interfaces import DependencyType, Task, TaskState


@dataclass
class DependencyEdge:
    """A dependency edge between two tasks."""

    from_task_id: str
    to_task_id: str
    dep_type: DependencyType = DependencyType.PARENT

    def to_dict(self) -> dict:
        return {
            "from": self.from_task_id,
            "to": self.to_task_id,
            "type": self.dep_type.value,
        }


@dataclass
class ExecutionBatch:
    """A set of tasks that can execute in parallel."""

    batch_index: int
    task_ids: list[str]
    ready_at: float = 0.0

    def to_dict(self) -> dict:
        return {"batch_index": self.batch_index, "task_ids": list(self.task_ids)}


class DAGPlanner:
    """Plans execution order based on task dependencies."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._edges: list[DependencyEdge] = []
        self._adjacency: dict[str, list[str]] = {}
        self._reverse_adjacency: dict[str, list[str]] = {}

    def add_task(self, task: Task) -> None:
        self._tasks[task.task_id] = task
        self._adjacency.setdefault(task.task_id, [])
        self._reverse_adjacency.setdefault(task.task_id, [])

    def remove_task(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)
        self._edges = [e for e in self._edges if e.from_task_id != task_id and e.to_task_id != task_id]
        self._adjacency.pop(task_id, None)
        self._reverse_adjacency.pop(task_id, None)
        for adj in self._adjacency.values():
            if task_id in adj:
                adj.remove(task_id)
        for radj in self._reverse_adjacency.values():
            if task_id in radj:
                radj.remove(task_id)

    def add_dependency(
        self,
        from_task_id: str,
        to_task_id: str,
        dep_type: DependencyType = DependencyType.PARENT,
    ) -> None:
        if from_task_id not in self._tasks:
            raise TaskNotFoundError(f"Task {from_task_id} not found")
        if to_task_id not in self._tasks:
            raise TaskNotFoundError(f"Task {to_task_id} not found")
        if from_task_id == to_task_id:
            raise DependencyNotMetError("Task cannot depend on itself")

        edge = DependencyEdge(from_task_id=from_task_id, to_task_id=to_task_id, dep_type=dep_type)
        self._edges.append(edge)
        self._adjacency[from_task_id].append(to_task_id)
        self._reverse_adjacency[to_task_id].append(from_task_id)

        if self._has_cycle():
            self._edges.pop()
            self._adjacency[from_task_id].remove(to_task_id)
            self._reverse_adjacency[to_task_id].remove(from_task_id)
            raise DependencyCycleError(f"Adding dependency {from_task_id} -> {to_task_id} creates a cycle")

    def get_predecessors(self, task_id: str) -> list[str]:
        return list(self._reverse_adjacency.get(task_id, []))

    def get_successors(self, task_id: str) -> list[str]:
        return list(self._adjacency.get(task_id, []))

    def get_ready_tasks(self) -> list[Task]:
        """Tasks whose dependencies are all satisfied."""
        ready = []
        for task_id, task in self._tasks.items():
            if task.state not in (TaskState.PENDING, TaskState.WAITING_DEPS, TaskState.QUEUED):
                continue
            predecessors = self._reverse_adjacency.get(task_id, [])
            all_done = all(
                self._tasks[p].state in (TaskState.COMPLETED, TaskState.FAILED)
                for p in predecessors
                if p in self._tasks
            )
            if all_done:
                ready.append(task)
        return ready

    def get_execution_batches(self) -> list[ExecutionBatch]:
        """Topological sort producing parallel batches."""
        in_degree: dict[str, int] = {tid: 0 for tid in self._tasks}
        for edge in self._edges:
            in_degree[edge.to_task_id] = in_degree.get(edge.to_task_id, 0) + 1

        batches: list[ExecutionBatch] = []
        processed: set[str] = set()
        remaining = dict(self._tasks)

        batch_idx = 0
        while remaining:
            batch_tasks = [
                tid for tid, deg in in_degree.items()
                if deg == 0 and tid not in processed
            ]
            if not batch_tasks:
                raise DependencyCycleError("Circular dependency detected in remaining tasks")

            batches.append(ExecutionBatch(batch_index=batch_idx, task_ids=batch_tasks))
            batch_idx += 1
            processed.update(batch_tasks)

            for tid in batch_tasks:
                remaining.pop(tid, None)
                for succ in self._adjacency.get(tid, []):
                    if succ in in_degree:
                        in_degree[succ] -= 1

        return batches

    def validate(self) -> list[str]:
        """Validate the DAG. Returns list of error messages."""
        errors: list[str] = []
        if self._has_cycle():
            errors.append("DAG contains a cycle")
        for task_id in self._tasks:
            if self._tasks[task_id].state == TaskState.PENDING:
                preds = self._reverse_adjacency.get(task_id, [])
                for p in preds:
                    if p in self._tasks and self._tasks[p].state not in (TaskState.COMPLETED,):
                        pass  # Normal waiting
        return errors

    def get_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def get_edges(self) -> list[DependencyEdge]:
        return list(self._edges)

    def _has_cycle(self) -> bool:
        """DFS cycle detection."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {tid: WHITE for tid in self._tasks}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in self._adjacency.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    return True
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        return any(dfs(tid) for tid, c in color.items() if c == WHITE)

    def to_dict(self) -> dict:
        return {
            "task_count": len(self._tasks),
            "edge_count": len(self._edges),
            "edges": [e.to_dict() for e in self._edges],
        }
