"""Workflow compiler — transforms workflow definitions into Execution Plans.

The compiler is the bridge between workflow description and execution.
It NEVER executes anything. It produces ExecutionPlans for the Scheduler.
"""

from __future__ import annotations

from typing import Any

from app.workflow.dag import WorkflowDAG
from app.workflow.edge import WorkflowEdge
from app.workflow.exceptions import WorkflowCompilationError
from app.workflow.interfaces import (
    ExecutionPlan,
    ValidationResult,
    WorkflowState,
)
from app.workflow.node import WorkflowNode
from app.workflow.planner import WorkflowPlanner
from app.workflow.validator import WorkflowValidator


class WorkflowCompiler:
    """Compiles workflow definitions into ExecutionPlans."""

    def __init__(self) -> None:
        self._validator = WorkflowValidator()
        self._planner = WorkflowPlanner()

    def compile(self, definition: dict[str, Any]) -> ExecutionPlan:
        validation = self._validator.validate(definition)
        if not validation.is_valid:
            raise WorkflowCompilationError(
                f"Validation failed: {'; '.join(validation.errors)}"
            )

        nodes = self._extract_nodes(definition)
        edges = self._extract_edges(definition)
        workflow_id = definition.get("workflow_id", "unknown")
        metadata = definition.get("metadata", {})

        try:
            plan = self._planner.plan(workflow_id, nodes, edges, metadata)
            plan.state = WorkflowState.COMPILED
            return plan
        except Exception as e:
            raise WorkflowCompilationError(f"Compilation failed: {e}") from e

    def compile_validated(
        self,
        definition: dict[str, Any],
        validation: ValidationResult,
    ) -> ExecutionPlan:
        if not validation.is_valid:
            raise WorkflowCompilationError(
                f"Cannot compile invalid workflow: {'; '.join(validation.errors)}"
            )
        return self.compile(definition)

    def _extract_nodes(self, definition: dict[str, Any]) -> list[WorkflowNode]:
        nodes: list[WorkflowNode] = []
        for node_data in definition.get("nodes", []):
            try:
                nodes.append(WorkflowNode.from_dict(node_data))
            except Exception as e:
                raise WorkflowCompilationError(f"Failed to parse node: {e}") from e
        return nodes

    def _extract_edges(self, definition: dict[str, Any]) -> list[WorkflowEdge]:
        edges: list[WorkflowEdge] = []
        for edge_data in definition.get("edges", []):
            try:
                edges.append(WorkflowEdge.from_dict(edge_data))
            except Exception as e:
                raise WorkflowCompilationError(f"Failed to parse edge: {e}") from e
        return edges
