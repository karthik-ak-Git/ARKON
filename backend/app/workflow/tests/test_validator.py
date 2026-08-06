"""Tests for workflow validator."""

import pytest
from app.workflow.validator import WorkflowValidator
from app.workflow.interfaces import ValidationResult


def _simple_def(node_count=1):
    nodes = [
        {"node_id": f"n{i}", "name": f"Node{i}", "capability": "test.cap"}
        for i in range(1, node_count + 1)
    ]
    return {"metadata": {"name": "test", "version": "1.0.0"}, "nodes": nodes, "edges": []}


class TestSchemaValidation:
    def test_empty_workflow_invalid(self):
        v = WorkflowValidator()
        result = v.validate({"metadata": {}, "edges": []})
        assert result.is_valid is False

    def test_single_node_valid(self):
        v = WorkflowValidator()
        result = v.validate(_simple_def(1))
        assert result.is_valid is True

    def test_nodes_not_list_invalid(self):
        v = WorkflowValidator()
        result = v.validate({"metadata": {}, "nodes": "bad", "edges": []})
        assert result.is_valid is False

    def test_node_missing_required_fields(self):
        v = WorkflowValidator()
        result = v.validate({"metadata": {}, "nodes": [{"node_id": "n1"}], "edges": []})
        assert result.is_valid is False


class TestReferenceValidation:
    def test_dangling_reference(self):
        v = WorkflowValidator()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [{"node_id": "n1", "name": "N", "capability": "cap"}],
            "edges": [{"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"}],
        }
        result = v.validate(d)
        assert result.is_valid is False

    def test_valid_references(self):
        v = WorkflowValidator()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [
                {"node_id": "n1", "name": "A", "capability": "cap"},
                {"node_id": "n2", "name": "B", "capability": "cap"},
            ],
            "edges": [{"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"}],
        }
        result = v.validate(d)
        assert result.is_valid is True


class TestCycleDetection:
    def test_linear_no_cycle(self):
        v = WorkflowValidator()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [
                {"node_id": "n1", "name": "A", "capability": "cap"},
                {"node_id": "n2", "name": "B", "capability": "cap"},
                {"node_id": "n3", "name": "C", "capability": "cap"},
            ],
            "edges": [
                {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"},
                {"edge_id": "e2", "source_node_id": "n2", "target_node_id": "n3"},
            ],
        }
        result = v.validate(d)
        assert result.is_valid is True

    def test_cycle_detected(self):
        v = WorkflowValidator()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [
                {"node_id": "n1", "name": "A", "capability": "cap"},
                {"node_id": "n2", "name": "B", "capability": "cap"},
            ],
            "edges": [
                {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"},
                {"edge_id": "e2", "source_node_id": "n2", "target_node_id": "n1"},
            ],
        }
        result = v.validate(d)
        assert result.is_valid is False


class TestCapabilityValidation:
    def test_empty_capability(self):
        v = WorkflowValidator()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [{"node_id": "n1", "name": "N", "capability": ""}],
            "edges": [],
        }
        result = v.validate(d)
        assert result.is_valid is False


class TestPortValidation:
    def test_valid_ports(self):
        v = WorkflowValidator()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [
                {
                    "node_id": "n1",
                    "name": "N1",
                    "capability": "cap",
                    "outputs": [{"port_id": "p2", "name": "out", "direction": "output"}],
                },
                {
                    "node_id": "n2",
                    "name": "N2",
                    "capability": "cap",
                    "inputs": [{"port_id": "p1", "name": "in", "direction": "input"}],
                },
            ],
            "edges": [
                {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2",
                 "source_port": "out", "target_port": "in"},
            ],
        }
        result = v.validate(d)
        assert result.is_valid is True

    def test_missing_port(self):
        v = WorkflowValidator()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [
                {
                    "node_id": "n1",
                    "name": "N",
                    "capability": "cap",
                    "outputs": [{"port_id": "p2", "name": "out", "direction": "output"}],
                },
            ],
            "edges": [
                {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n1",
                 "source_port": "nonexistent", "target_port": ""},
            ],
        }
        result = v.validate(d)
        assert result.is_valid is False
