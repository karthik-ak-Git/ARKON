"""Tests for workflow compiler and planner."""

import pytest
from app.workflow.compiler import WorkflowCompiler
from app.workflow.planner import WorkflowPlanner
from app.workflow.interfaces import WorkflowState
from app.workflow.exceptions import WorkflowCompilationError, WorkflowPlanningError


def _simple_def():
    return {
        "workflow_id": "wf1",
        "metadata": {"name": "test", "version": "1.0.0"},
        "nodes": [
            {"node_id": "n1", "name": "A", "capability": "cap.a"},
            {"node_id": "n2", "name": "B", "capability": "cap.b"},
            {"node_id": "n3", "name": "C", "capability": "cap.c"},
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"},
            {"edge_id": "e2", "source_node_id": "n2", "target_node_id": "n3"},
        ],
    }


def _diamond_def():
    return {
        "workflow_id": "wf2",
        "metadata": {"name": "diamond", "version": "1.0.0"},
        "nodes": [
            {"node_id": "a", "name": "A", "capability": "cap"},
            {"node_id": "b", "name": "B", "capability": "cap"},
            {"node_id": "c", "name": "C", "capability": "cap"},
            {"node_id": "d", "name": "D", "capability": "cap"},
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "a", "target_node_id": "b"},
            {"edge_id": "e2", "source_node_id": "a", "target_node_id": "c"},
            {"edge_id": "e3", "source_node_id": "b", "target_node_id": "d"},
            {"edge_id": "e4", "source_node_id": "c", "target_node_id": "d"},
        ],
    }


class TestPlanner:
    def test_linear_plan(self):
        from app.workflow.node import WorkflowNode
        from app.workflow.edge import WorkflowEdge
        wf = _simple_def()
        nodes = [WorkflowNode.from_dict(nd) for nd in wf["nodes"]]
        edges = [WorkflowEdge.from_dict(ed) for ed in wf["edges"]]
        p = WorkflowPlanner()
        plan = p.plan("wf1", nodes, edges)
        assert len(plan.tasks) == 3
        assert plan.workflow_id == "wf1"

    def test_plan_dependencies(self):
        from app.workflow.node import WorkflowNode
        from app.workflow.edge import WorkflowEdge
        wf = _simple_def()
        nodes = [WorkflowNode.from_dict(nd) for nd in wf["nodes"]]
        edges = [WorkflowEdge.from_dict(ed) for ed in wf["edges"]]
        p = WorkflowPlanner()
        plan = p.plan("wf1", nodes, edges)
        task3 = [t for t in plan.tasks if t.node_id == "n3"][0]
        assert len(task3.dependencies) > 0

    def test_diamond_plan(self):
        from app.workflow.node import WorkflowNode
        from app.workflow.edge import WorkflowEdge
        wf = _diamond_def()
        nodes = [WorkflowNode.from_dict(nd) for nd in wf["nodes"]]
        edges = [WorkflowEdge.from_dict(ed) for ed in wf["edges"]]
        p = WorkflowPlanner()
        plan = p.plan("wf2", nodes, edges)
        assert len(plan.tasks) == 4

    def test_plan_empty_nodes_fails(self):
        p = WorkflowPlanner()
        with pytest.raises(WorkflowPlanningError):
            p.plan("wf1", [], [])


class TestCompiler:
    def test_compile_linear(self):
        c = WorkflowCompiler()
        plan = c.compile(_simple_def())
        assert plan.state == WorkflowState.COMPILED

    def test_compile_diamond(self):
        c = WorkflowCompiler()
        plan = c.compile(_diamond_def())
        assert len(plan.tasks) == 4

    def test_compile_empty_workflow_fails(self):
        c = WorkflowCompiler()
        with pytest.raises(WorkflowCompilationError):
            c.compile({"metadata": {}, "nodes": [], "edges": []})

    def test_plan_has_task_ids(self):
        c = WorkflowCompiler()
        plan = c.compile(_simple_def())
        for task in plan.tasks:
            assert task.task_id is not None
            assert len(task.task_id) > 0

    def test_compile_invalid_refs_fails(self):
        c = WorkflowCompiler()
        d = {
            "workflow_id": "wf",
            "metadata": {"name": "bad", "version": "1.0.0"},
            "nodes": [{"node_id": "n1", "name": "A", "capability": "cap"}],
            "edges": [{"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"}],
        }
        with pytest.raises(WorkflowCompilationError):
            c.compile(d)
