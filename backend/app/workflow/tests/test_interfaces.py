"""Tests for workflow interfaces."""

import pytest
from app.workflow.interfaces import (
    Condition,
    ConditionType,
    EdgeType,
    ExecutionPlan,
    ExecutionPlanTask,
    LoopConfig,
    LoopStrategy,
    ParallelConfig,
    Port,
    PortDirection,
    ValidationResult,
    WorkflowFormat,
    WorkflowMetadata,
    WorkflowState,
)


class TestPort:
    def test_creation(self):
        p = Port(port_id="p1", name="input", direction=PortDirection.INPUT)
        assert p.port_id == "p1"
        assert p.direction == PortDirection.INPUT

    def test_to_dict(self):
        p = Port(port_id="p1", name="x", direction=PortDirection.OUTPUT, data_type="str")
        d = p.to_dict()
        assert d["port_id"] == "p1"
        assert d["direction"] == "output"
        assert d["data_type"] == "str"

    def test_from_dict(self):
        p = Port.from_dict({"port_id": "p1", "name": "x", "direction": "input"})
        assert p.direction == PortDirection.INPUT

    def test_defaults(self):
        p = Port()
        assert p.required is True
        assert p.default is None


class TestCondition:
    def test_creation(self):
        c = Condition(condition_id="c1", expression="x > 5")
        assert c.expression == "x > 5"

    def test_to_dict(self):
        c = Condition(condition_id="c1", condition_type=ConditionType.STATUS, expression="done")
        d = c.to_dict()
        assert d["condition_type"] == "status"

    def test_from_dict(self):
        c = Condition.from_dict({"condition_id": "c1", "condition_type": "expression", "expression": "ok"})
        assert c.condition_type == ConditionType.EXPRESSION


class TestLoopConfig:
    def test_creation(self):
        lc = LoopConfig(strategy=LoopStrategy.UNTIL, until_expression="done")
        assert lc.strategy == LoopStrategy.UNTIL

    def test_to_dict(self):
        lc = LoopConfig(strategy=LoopStrategy.OVER, over_field="items")
        d = lc.to_dict()
        assert d["strategy"] == "over"

    def test_from_dict(self):
        lc = LoopConfig.from_dict({"strategy": "fixed", "max_iterations": 5})
        assert lc.strategy == LoopStrategy.FIXED
        assert lc.max_iterations == 5


class TestParallelConfig:
    def test_creation(self):
        pc = ParallelConfig(parallel_id="p1", node_ids=["a", "b"])
        assert len(pc.node_ids) == 2

    def test_to_dict(self):
        pc = ParallelConfig(parallel_id="p1", node_ids=["a"], barrier_node_id="barrier")
        d = pc.to_dict()
        assert d["barrier_node_id"] == "barrier"


class TestWorkflowMetadata:
    def test_creation(self):
        m = WorkflowMetadata(name="test", version="2.0.0")
        assert m.name == "test"

    def test_to_dict(self):
        m = WorkflowMetadata(name="test", tags=["a"])
        d = m.to_dict()
        assert d["name"] == "test"
        assert d["tags"] == ["a"]

    def test_from_dict(self):
        m = WorkflowMetadata.from_dict({"name": "x", "format": "json"})
        assert m.format == WorkflowFormat.JSON


class TestExecutionPlanTask:
    def test_creation(self):
        t = ExecutionPlanTask(node_id="n1", name="task1", capability="cap")
        assert t.node_id == "n1"

    def test_to_dict(self):
        t = ExecutionPlanTask(node_id="n1", capability="cap", priority=3)
        d = t.to_dict()
        assert d["priority"] == 3

    def test_from_dict(self):
        t = ExecutionPlanTask.from_dict({"node_id": "n1", "capability": "cap"})
        assert t.node_id == "n1"


class TestExecutionPlan:
    def test_creation(self):
        plan = ExecutionPlan(workflow_id="wf1")
        assert plan.workflow_id == "wf1"

    def test_get_task_by_node(self):
        t = ExecutionPlanTask(task_id="t1", node_id="n1")
        plan = ExecutionPlan(tasks=[t])
        assert plan.get_task_by_node("n1") is t
        assert plan.get_task_by_node("n2") is None

    def test_get_dependencies(self):
        t = ExecutionPlanTask(task_id="t1", dependencies=["t0"])
        plan = ExecutionPlan(tasks=[t])
        assert plan.get_dependencies("t1") == ["t0"]
        assert plan.get_dependencies("missing") == []

    def test_topological_order(self):
        t1 = ExecutionPlanTask(task_id="t1", dependencies=[])
        t2 = ExecutionPlanTask(task_id="t2", dependencies=["t1"])
        t3 = ExecutionPlanTask(task_id="t3", dependencies=["t2"])
        plan = ExecutionPlan(tasks=[t1, t2, t3])
        order = plan.topological_order()
        assert order.index("t1") < order.index("t2")
        assert order.index("t2") < order.index("t3")

    def test_to_dict(self):
        plan = ExecutionPlan(workflow_id="wf1")
        d = plan.to_dict()
        assert d["workflow_id"] == "wf1"
        assert d["tasks"] == []

    def test_from_dict(self):
        plan = ExecutionPlan.from_dict({"workflow_id": "wf1", "state": "compiled"})
        assert plan.state == WorkflowState.COMPILED


class TestValidationResult:
    def test_valid(self):
        r = ValidationResult()
        assert r.is_valid is True
        assert r.errors == []

    def test_add_error(self):
        r = ValidationResult()
        r.add_error("bad")
        assert r.is_valid is False
        assert "bad" in r.errors

    def test_add_warning(self):
        r = ValidationResult()
        r.add_warning("heads up")
        assert r.is_valid is True
        assert "heads up" in r.warnings

    def test_to_dict(self):
        r = ValidationResult()
        r.add_error("e1")
        r.add_warning("w1")
        d = r.to_dict()
        assert d["is_valid"] is False
        assert d["errors"] == ["e1"]
        assert d["warnings"] == ["w1"]
