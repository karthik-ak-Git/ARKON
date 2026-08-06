"""Tests for workflow edge."""

import pytest
from app.workflow.edge import WorkflowEdge
from app.workflow.interfaces import EdgeType


class TestWorkflowEdge:
    def _make_edge(self, **overrides):
        defaults = dict(
            edge_id="e1",
            source_node_id="n1",
            target_node_id="n2",
        )
        defaults.update(overrides)
        return WorkflowEdge(**defaults)

    def test_creation(self):
        e = self._make_edge()
        assert e.source_node_id == "n1"
        assert e.target_node_id == "n2"
        assert e.edge_type == EdgeType.DATA

    def test_connects(self):
        e = self._make_edge()
        assert e.connects("n1", "n2") is True
        assert e.connects("n2", "n1") is False

    def test_control_edge(self):
        e = self._make_edge(edge_type=EdgeType.CONTROL)
        assert e.edge_type == EdgeType.CONTROL

    def test_barrier_edge(self):
        e = self._make_edge(edge_type=EdgeType.BARRIER)
        assert e.edge_type == EdgeType.BARRIER

    def test_condition_string(self):
        e = self._make_edge(condition="status == 'ok'")
        assert e.condition == "status == 'ok'"

    def test_to_dict(self):
        e = self._make_edge()
        d = e.to_dict()
        assert d["edge_id"] == "e1"
        assert d["source_node_id"] == "n1"
        assert d["edge_type"] == "data"

    def test_from_dict(self):
        d = {
            "edge_id": "e2",
            "source_node_id": "n1",
            "target_node_id": "n3",
            "edge_type": "control",
        }
        e = WorkflowEdge.from_dict(d)
        assert e.edge_id == "e2"
        assert e.target_node_id == "n3"
        assert e.edge_type == EdgeType.CONTROL

    def test_defaults(self):
        e = self._make_edge()
        assert e.source_port == ""
        assert e.target_port == ""
        assert e.condition == ""
        assert e.metadata == {}
