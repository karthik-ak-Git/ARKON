"""Workflow validator.

Validates workflow definitions: cycles, missing nodes, capabilities, schema, versions.
"""

from __future__ import annotations

from typing import Any

from app.workflow.edge import WorkflowEdge
from app.workflow.exceptions import WorkflowValidationError
from app.workflow.interfaces import (
    EdgeType,
    PortDirection,
    ValidationResult,
    WorkflowState,
)
from app.workflow.node import WorkflowNode


class WorkflowValidator:
    """Validates workflow definitions."""

    REQUIRED_FIELDS = {"nodes"}
    NODE_REQUIRED_FIELDS = {"node_id", "name", "capability"}

    def validate(self, definition: dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True)

        self._validate_schema(definition, result)
        if not result.is_valid:
            return result

        nodes = self._parse_nodes(definition, result)
        edges = self._parse_edges(definition, result)
        if not result.is_valid:
            return result

        self._validate_references(nodes, edges, result)
        self._validate_cycles(nodes, edges, result)
        self._validate_capabilities(nodes, result)
        self._validate_ports(nodes, edges, result)
        self._validate_versions(definition, result)

        return result

    def _validate_schema(self, definition: dict[str, Any], result: ValidationResult) -> None:
        for field in self.REQUIRED_FIELDS:
            if field not in definition:
                result.add_error(f"Missing required field: {field}")

        nodes_data = definition.get("nodes")
        if nodes_data is not None:
            if not isinstance(nodes_data, list):
                result.add_error("'nodes' must be a list")
                return
            for i, node_data in enumerate(nodes_data):
                if not isinstance(node_data, dict):
                    result.add_error(f"Node at index {i} must be a mapping")
                    continue
                for field in self.NODE_REQUIRED_FIELDS:
                    if field not in node_data:
                        result.add_error(f"Node at index {i} missing required field: {field}")

    def _parse_nodes(
        self, definition: dict[str, Any], result: ValidationResult
    ) -> dict[str, WorkflowNode]:
        nodes: dict[str, WorkflowNode] = {}
        for node_data in definition.get("nodes", []):
            try:
                node = WorkflowNode.from_dict(node_data)
                nodes[node.node_id] = node
            except Exception as e:
                result.add_error(f"Failed to parse node: {e}")
        return nodes

    def _parse_edges(
        self, definition: dict[str, Any], result: ValidationResult
    ) -> dict[str, WorkflowEdge]:
        edges: dict[str, WorkflowEdge] = {}
        for edge_data in definition.get("edges", []):
            try:
                edge = WorkflowEdge.from_dict(edge_data)
                edges[edge.edge_id] = edge
            except Exception as e:
                result.add_error(f"Failed to parse edge: {e}")
        return edges

    def _validate_references(
        self,
        nodes: dict[str, WorkflowNode],
        edges: dict[str, WorkflowEdge],
        result: ValidationResult,
    ) -> None:
        node_ids = set(nodes.keys())
        for edge in edges.values():
            if edge.source_node_id not in node_ids:
                result.add_error(
                    f"Edge '{edge.edge_id}' references missing source node '{edge.source_node_id}'"
                )
            if edge.target_node_id not in node_ids:
                result.add_error(
                    f"Edge '{edge.edge_id}' references missing target node '{edge.target_node_id}'"
                )

    def _validate_cycles(
        self,
        nodes: dict[str, WorkflowNode],
        edges: dict[str, WorkflowEdge],
        result: ValidationResult,
    ) -> None:
        adjacency: dict[str, set[str]] = {nid: set() for nid in nodes}
        for edge in edges.values():
            if edge.source_node_id in nodes and edge.target_node_id in nodes:
                adjacency[edge.source_node_id].add(edge.target_node_id)

        in_degree = {nid: 0 for nid in nodes}
        for children in adjacency.values():
            for child in children:
                in_degree[child] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            nid = queue.pop(0)
            visited += 1
            for child in adjacency[nid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if visited != len(nodes):
            result.add_error("Workflow contains a cycle")

    def _validate_capabilities(
        self, nodes: dict[str, WorkflowNode], result: ValidationResult
    ) -> None:
        for node in nodes.values():
            if not node.capability:
                result.add_error(f"Node '{node.name}' ({node.node_id}) has no capability")

    def _validate_ports(
        self,
        nodes: dict[str, WorkflowNode],
        edges: dict[str, WorkflowEdge],
        result: ValidationResult,
    ) -> None:
        for edge in edges.values():
            if edge.source_node_id not in nodes or edge.target_node_id not in nodes:
                continue

            if edge.source_port:
                source_node = nodes[edge.source_node_id]
                if not source_node.get_output(edge.source_port):
                    result.add_error(
                        f"Edge '{edge.edge_id}' references missing output port "
                        f"'{edge.source_port}' on node '{edge.source_node_id}'"
                    )

            if edge.target_port:
                target_node = nodes[edge.target_node_id]
                if not target_node.get_input(edge.target_port):
                    result.add_error(
                        f"Edge '{edge.edge_id}' references missing input port "
                        f"'{edge.target_port}' on node '{edge.target_node_id}'"
                    )

    def _validate_versions(
        self, definition: dict[str, Any], result: ValidationResult
    ) -> None:
        metadata = definition.get("metadata", {})
        version = metadata.get("version", "1.0.0")
        if not self._is_valid_semver(version):
            result.add_warning(f"Version '{version}' is not valid semver")
        min_version = definition.get("min_version")
        if min_version and not self._is_valid_semver(min_version):
            result.add_warning(f"min_version '{min_version}' is not valid semver")

    def _is_valid_semver(self, version: str) -> bool:
        parts = version.split(".")
        if len(parts) != 3:
            return False
        return all(p.isdigit() for p in parts)
