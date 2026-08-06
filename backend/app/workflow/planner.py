"""Workflow planner — constructs execution plans.

Takes a compiled workflow and produces an ExecutionPlan for the Scheduler.
"""

from __future__ import annotations

from typing import Any

from app.workflow.dag import WorkflowDAG
from app.workflow.edge import WorkflowEdge
from app.workflow.exceptions import WorkflowPlanningError
from app.workflow.interfaces import (
    EdgeType,
    ExecutionPlan,
    ExecutionPlanTask,
    NodeState,
    WorkflowState,
)
from app.workflow.node import WorkflowNode


class WorkflowPlanner:
    """Constructs ExecutionPlans from validated workflow graphs."""

    def plan(
        self,
        workflow_id: str,
        nodes: list[WorkflowNode],
        edges: list[WorkflowEdge],
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionPlan:
        if not nodes:
            raise WorkflowPlanningError("No nodes to plan")

        dag = WorkflowDAG(nodes, edges)
        errors = dag.validate_dag()
        if errors:
            raise WorkflowPlanningError(f"DAG validation failed: {'; '.join(errors)}")

        order = dag.topological_sort()
        tasks = self._build_tasks(order, nodes, edges, dag)

        meta = metadata or {}
        return ExecutionPlan(
            workflow_id=workflow_id,
            workflow_name=meta.get("name", ""),
            version=meta.get("version", "1.0.0"),
            state=WorkflowState.PLANNED,
            tasks=tasks,
            metadata=meta,
        )

    def _build_tasks(
        self,
        order: list[str],
        nodes: list[WorkflowNode],
        edges: list[WorkflowEdge],
        dag: WorkflowDAG,
    ) -> list[ExecutionPlanTask]:
        node_map = {n.node_id: n for n in nodes}
        task_map: dict[str, ExecutionPlanTask] = {}
        tasks: list[ExecutionPlanTask] = []

        for node_id in order:
            node = node_map[node_id]
            dep_node_ids = dag.get_parents(node_id)
            dep_task_ids = [
                task_map[dep_id].task_id
                for dep_id in dep_node_ids
                if dep_id in task_map
            ]

            task = ExecutionPlanTask(
                node_id=node.node_id,
                name=node.name,
                capability=node.capability,
                priority=node.priority,
                estimated_duration=node.timeout,
                timeout=node.timeout,
                dependencies=dep_task_ids,
                resource_requirements=dict(node.resource_requirements),
                metadata=dict(node.metadata),
                payload=dict(node.config),
                tags=list(node.tags),
            )
            task_map[node_id] = task
            tasks.append(task)

        return tasks
