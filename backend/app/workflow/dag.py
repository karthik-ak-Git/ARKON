"""DAG operations for workflow graphs.

Pure graph algorithms — no execution logic.
"""

from __future__ import annotations

from typing import Any

from app.workflow.edge import WorkflowEdge
from app.workflow.exceptions import CyclicDependencyError, DAGError
from app.workflow.node import WorkflowNode


class WorkflowDAG:
    """Directed Acyclic Graph for workflow nodes and edges."""

    def __init__(
        self,
        nodes: list[WorkflowNode] | None = None,
        edges: list[WorkflowEdge] | None = None,
    ) -> None:
        self._nodes: dict[str, WorkflowNode] = {}
        self._edges: dict[str, WorkflowEdge] = {}
        self._adjacency: dict[str, set[str]] = {}
        self._reverse: dict[str, set[str]] = {}

        for node in (nodes or []):
            self.add_node(node)
        for edge in (edges or []):
            self.add_edge(edge)

    def add_node(self, node: WorkflowNode) -> None:
        self._nodes[node.node_id] = node
        if node.node_id not in self._adjacency:
            self._adjacency[node.node_id] = set()
        if node.node_id not in self._reverse:
            self._reverse[node.node_id] = set()

    def add_edge(self, edge: WorkflowEdge) -> None:
        self._edges[edge.edge_id] = edge
        src = edge.source_node_id
        tgt = edge.target_node_id

        if src not in self._nodes:
            raise DAGError(f"Source node '{src}' not in DAG")
        if tgt not in self._nodes:
            raise DAGError(f"Target node '{tgt}' not in DAG")

        self._adjacency.setdefault(src, set()).add(tgt)
        self._reverse.setdefault(tgt, set()).add(src)

    def remove_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            return
        del self._nodes[node_id]
        self._adjacency.pop(node_id, None)
        self._reverse.pop(node_id, None)
        for deps in self._adjacency.values():
            deps.discard(node_id)
        for deps in self._reverse.values():
            deps.discard(node_id)
        to_remove = [
            eid for eid, e in self._edges.items()
            if e.source_node_id == node_id or e.target_node_id == node_id
        ]
        for eid in to_remove:
            del self._edges[eid]

    def get_node(self, node_id: str) -> WorkflowNode | None:
        return self._nodes.get(node_id)

    def get_nodes(self) -> list[WorkflowNode]:
        return list(self._nodes.values())

    def get_edges(self) -> list[WorkflowEdge]:
        return list(self._edges.values())

    def get_children(self, node_id: str) -> list[str]:
        return list(self._adjacency.get(node_id, set()))

    def get_parents(self, node_id: str) -> list[str]:
        return list(self._reverse.get(node_id, set()))

    def has_cycle(self) -> bool:
        try:
            self.topological_sort()
            return False
        except CyclicDependencyError:
            return True

    def topological_sort(self) -> list[str]:
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        for nid, children in self._adjacency.items():
            for child in children:
                in_degree[child] = in_degree.get(child, 0) + 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            queue.sort()
            nid = queue.pop(0)
            order.append(nid)
            for child in self._adjacency.get(nid, set()):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(order) != len(self._nodes):
            missing = set(self._nodes.keys()) - set(order)
            raise CyclicDependencyError(
                f"Cycle detected involving nodes: {sorted(missing)}"
            )

        return order

    def get_roots(self) -> list[str]:
        return [nid for nid in self._nodes if not self._reverse.get(nid)]

    def get_leaves(self) -> list[str]:
        return [nid for nid in self._nodes if not self._adjacency.get(nid)]

    def get_all_descendants(self, node_id: str) -> set[str]:
        visited: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for child in self._adjacency.get(current, set()):
                if child not in visited:
                    visited.add(child)
                    stack.append(child)
        return visited

    def get_all_ancestors(self, node_id: str) -> set[str]:
        visited: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for parent in self._reverse.get(current, set()):
                if parent not in visited:
                    visited.add(parent)
                    stack.append(parent)
        return visited

    def get_critical_path(self) -> list[str]:
        """Return the longest path through the DAG (by node count)."""
        order = self.topological_sort()
        dist: dict[str, int] = {nid: 0 for nid in order}
        prev: dict[str, str | None] = {nid: None for nid in order}

        for nid in order:
            for child in self._adjacency.get(nid, set()):
                if dist[nid] + 1 > dist[child]:
                    dist[child] = dist[nid] + 1
                    prev[child] = nid

        if not dist:
            return []
        end = max(dist, key=lambda k: dist[k])
        path: list[str] = []
        current: str | None = end
        while current is not None:
            path.append(current)
            current = prev[current]
        path.reverse()
        return path

    def validate_dag(self) -> list[str]:
        """Validate DAG integrity. Returns list of errors (empty = valid)."""
        errors: list[str] = []

        if self.has_cycle():
            errors.append("DAG contains a cycle")

        for edge in self._edges.values():
            if edge.source_node_id not in self._nodes:
                errors.append(f"Edge '{edge.edge_id}' references missing source '{edge.source_node_id}'")
            if edge.target_node_id not in self._nodes:
                errors.append(f"Edge '{edge.edge_id}' references missing target '{edge.target_node_id}'")
            if edge.source_node_id == edge.target_node_id:
                errors.append(f"Edge '{edge.edge_id}' is a self-loop")

        return errors

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }
