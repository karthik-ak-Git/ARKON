"""ARKON Execution Engine - Dependency Graph.

Tasks may depend on other tasks.
Supports DAG validation, cycle detection, and execution ordering.
"""

from __future__ import annotations

from typing import Any

from app.execution.exceptions import CircularDependencyError


class DependencyGraph:
    """Directed Acyclic Graph for task dependencies.

    Supports:
    - DAG validation
    - Cycle detection
    - Topological ordering
    - Dependency resolution
    """

    def __init__(self) -> None:
        """Initialize dependency graph."""
        self._edges: dict[str, set[str]] = {}
        self._nodes: set[str] = set()
        self._completed: set[str] = set()
        self._failed: set[str] = set()

    def add_node(self, task_id: str) -> None:
        """Add a node to the graph."""
        self._nodes.add(task_id)
        if task_id not in self._edges:
            self._edges[task_id] = set()

    def add_task(self, task_id: str) -> None:
        """Add a task node (alias for add_node)."""
        self.add_node(task_id)

    def mark_done(self, task_id: str) -> None:
        """Mark a task as completed."""
        self._completed.add(task_id)
        self._failed.discard(task_id)

    def mark_failed(self, task_id: str) -> None:
        """Mark a task as failed."""
        self._failed.add(task_id)
        self._completed.discard(task_id)

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add a dependency edge.

        Args:
            task_id: Task that depends on another.
            depends_on: Task that must complete first.

        Raises:
            CircularDependencyError: If adding would create a cycle.
        """
        self.add_node(task_id)
        self.add_node(depends_on)

        # Check for cycle before adding
        if self._would_create_cycle(task_id, depends_on):
            cycle = self._find_cycle_path(task_id, depends_on)
            raise CircularDependencyError(cycle)

        self._edges[task_id].add(depends_on)

    def remove_dependency(self, task_id: str, depends_on: str) -> None:
        """Remove a dependency edge."""
        if task_id in self._edges:
            self._edges[task_id].discard(depends_on)

    def get_dependencies(self, task_id: str) -> set[str]:
        """Get direct dependencies of a task."""
        return self._edges.get(task_id, set()).copy()

    def get_dependents(self, task_id: str) -> set[str]:
        """Get tasks that depend on the given task."""
        dependents = set()
        for node, deps in self._edges.items():
            if task_id in deps:
                dependents.add(node)
        return dependents

    def get_ready_tasks(self, completed: set[str] | None = None) -> list[str]:
        """Get tasks whose dependencies are all satisfied.

        Args:
            completed: Set of completed task IDs. If None, uses internal tracking.

        Returns:
            List of task IDs ready to execute.
        """
        if completed is None:
            completed = self._completed

        ready = []
        for task_id in self._nodes:
            if task_id in self._completed or task_id in self._failed:
                continue
            deps = self._edges.get(task_id, set())
            if deps.issubset(completed):
                ready.append(task_id)
        return sorted(ready)

    def topological_sort(self) -> list[str]:
        """Get topological ordering of tasks.

        Returns:
            List of task IDs in execution order.

        Raises:
            CircularDependencyError: If graph contains a cycle.
        """
        in_degree: dict[str, int] = {node: 0 for node in self._nodes}
        for task_id, deps in self._edges.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[task_id] += 1

        queue = [n for n, d in in_degree.items() if d == 0]
        result: list[str] = []

        while queue:
            queue.sort()  # Deterministic ordering
            node = queue.pop(0)
            result.append(node)

            for dependent in self.get_dependents(node):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self._nodes):
            raise CircularDependencyError(
                list(self._nodes - set(result))
            )

        return result

    def has_cycle(self) -> bool:
        """Check if the graph contains a cycle."""
        try:
            self.topological_sort()
            return False
        except CircularDependencyError:
            return True

    def validate(self) -> list[str]:
        """Validate the graph.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        if self.has_cycle():
            errors.append("Graph contains circular dependencies")

        # Check for self-dependencies
        for task_id, deps in self._edges.items():
            if task_id in deps:
                errors.append(f"Task '{task_id}' depends on itself")

        return errors

    def remove_node(self, task_id: str) -> None:
        """Remove a node and all its edges."""
        self._nodes.discard(task_id)
        self._edges.pop(task_id, None)
        for deps in self._edges.values():
            deps.discard(task_id)

    def size(self) -> int:
        """Get number of nodes."""
        return len(self._nodes)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "nodes": list(self._nodes),
            "edges": {
                k: list(v) for k, v in self._edges.items()
            },
            "size": self.size(),
            "has_cycle": self.has_cycle(),
        }

    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of graph state."""
        return {
            "total_nodes": self.size(),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "pending": self.size() - len(self._completed) - len(self._failed),
            "has_cycle": self.has_cycle(),
        }

    def _would_create_cycle(self, task_id: str, depends_on: str) -> bool:
        """Check if adding an edge would create a cycle."""
        if depends_on == task_id:
            return True
        visited = set()
        stack = [depends_on]
        while stack:
            current = stack.pop()
            if current == task_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._edges.get(current, set()))
        return False

    def _find_cycle_path(self, task_id: str, depends_on: str) -> list[str]:
        """Find the cycle path for error reporting."""
        path = [task_id]
        visited = {task_id}
        stack = [(depends_on, [depends_on])]

        while stack:
            current, current_path = stack.pop()
            if current == task_id:
                return current_path + [task_id]
            if current in visited:
                continue
            visited.add(current)
            for dep in self._edges.get(current, set()):
                stack.append((dep, current_path + [dep]))

        return [task_id, depends_on, task_id]
