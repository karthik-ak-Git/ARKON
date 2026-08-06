"""Tests for workflow node."""

import pytest
from app.workflow.node import WorkflowNode
from app.workflow.interfaces import Port, PortDirection, Condition, ConditionType


class TestWorkflowNode:
    def _make_node(self, **overrides):
        defaults = dict(
            node_id="n1",
            name="Test Node",
            capability="video.render",
        )
        defaults.update(overrides)
        return WorkflowNode(**defaults)

    def test_creation(self):
        n = self._make_node()
        assert n.node_id == "n1"
        assert n.capability == "video.render"
        assert n.max_retries == 3

    def test_defaults(self):
        n = self._make_node()
        assert n.priority == 5
        assert n.config == {}
        assert n.inputs == []
        assert n.outputs == []
        assert n.timeout is None
        assert n.resource_requirements == {}

    def test_add_input_port(self):
        n = self._make_node()
        p = Port(port_id="p1", name="in", direction=PortDirection.INPUT)
        n.inputs.append(p)
        assert len(n.inputs) == 1

    def test_add_output_port(self):
        n = self._make_node()
        p = Port(port_id="p2", name="out", direction=PortDirection.OUTPUT)
        n.outputs.append(p)
        assert len(n.outputs) == 1

    def test_get_input(self):
        n = self._make_node()
        p = Port(port_id="p1", name="in", direction=PortDirection.INPUT)
        n.inputs.append(p)
        found = n.get_input("in")
        assert found is p
        assert n.get_input("nope") is None

    def test_get_output(self):
        n = self._make_node()
        p = Port(port_id="p2", name="out", direction=PortDirection.OUTPUT)
        n.outputs.append(p)
        found = n.get_output("out")
        assert found is p
        assert n.get_output("nope") is None

    def test_add_condition(self):
        n = self._make_node()
        c = Condition(condition_id="c1", expression="status == 'ok'")
        n.conditions.append(c)
        assert len(n.conditions) == 1
        assert n.conditions[0].expression == "status == 'ok'"

    def test_to_dict(self):
        n = self._make_node(name="NodeA")
        d = n.to_dict()
        assert d["node_id"] == "n1"
        assert d["name"] == "NodeA"
        assert d["capability"] == "video.render"
        assert d["priority"] == 5

    def test_from_dict(self):
        d = {
            "node_id": "n2",
            "name": "B",
            "capability": "audio.mix",
            "timeout": 30,
        }
        n = WorkflowNode.from_dict(d)
        assert n.node_id == "n2"
        assert n.timeout == 30

    def test_to_dict_includes_ports(self):
        n = self._make_node()
        p = Port(port_id="p1", name="in", direction=PortDirection.INPUT)
        n.inputs.append(p)
        d = n.to_dict()
        assert len(d["inputs"]) == 1

    def test_to_dict_includes_conditions(self):
        n = self._make_node()
        c = Condition(condition_id="c1", condition_type=ConditionType.STATUS, expression="ok")
        n.conditions.append(c)
        d = n.to_dict()
        assert len(d["conditions"]) == 1

    def test_has_required_inputs_true(self):
        n = self._make_node()
        n.inputs.append(Port(name="a", required=True))
        assert n.has_required_inputs() is True

    def test_has_required_inputs_false(self):
        n = self._make_node()
        n.inputs.append(Port(name="a", required=False))
        assert n.has_required_inputs() is False
