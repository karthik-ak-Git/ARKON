"""Tests for workflow parser."""

import pytest
import json
from app.workflow.parser import WorkflowParser
from app.workflow.exceptions import WorkflowParseError
from app.workflow.interfaces import WorkflowFormat


class TestParserJSON:
    def test_parse_simple(self):
        p = WorkflowParser()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [{"node_id": "n1", "name": "Node1", "capability": "test"}],
            "edges": [],
        }
        result = p.parse(json.dumps(d), WorkflowFormat.JSON)
        assert result["metadata"]["name"] == "test"
        assert len(result["nodes"]) == 1

    def test_parse_with_edges(self):
        p = WorkflowParser()
        d = {
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [
                {"node_id": "n1", "name": "A", "capability": "cap"},
                {"node_id": "n2", "name": "B", "capability": "cap"},
            ],
            "edges": [{"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"}],
        }
        result = p.parse(json.dumps(d), WorkflowFormat.JSON)
        assert len(result["edges"]) == 1

    def test_parse_empty_dict_json(self):
        p = WorkflowParser()
        d = json.dumps({"metadata": {}, "nodes": [], "edges": []})
        result = p.parse(d, WorkflowFormat.JSON)
        assert result["nodes"] == []

    def test_parse_invalid_json(self):
        p = WorkflowParser()
        with pytest.raises(WorkflowParseError):
            p.parse("not json at all", WorkflowFormat.JSON)

    def test_parse_json_array_rejected(self):
        p = WorkflowParser()
        with pytest.raises(WorkflowParseError):
            p.parse("[1, 2, 3]", WorkflowFormat.JSON)


class TestParserYAML:
    def test_parse_yaml(self):
        p = WorkflowParser()
        yaml_str = """
metadata:
  name: test
  version: "1.0.0"
nodes:
  - node_id: n1
    name: Node1
    capability: test.cap
edges: []
"""
        result = p.parse(yaml_str, WorkflowFormat.YAML)
        assert result["metadata"]["name"] == "test"
        assert len(result["nodes"]) == 1

    def test_parse_yaml_simple(self):
        p = WorkflowParser()
        yaml_str = "metadata:\n  name: x\n  version: '1.0.0'\nnodes: []\nedges: []\n"
        result = p.parse(yaml_str, WorkflowFormat.YAML)
        assert result["metadata"]["name"] == "x"

    def test_parse_yaml_invalid(self):
        p = WorkflowParser()
        with pytest.raises(WorkflowParseError):
            p.parse("}{invalid yaml{[", WorkflowFormat.YAML)


class TestParserAutoDetect:
    def test_detect_json(self):
        p = WorkflowParser()
        fmt = p.detect_format('{"workflow_id": "test"}')
        assert fmt == WorkflowFormat.JSON

    def test_detect_yaml(self):
        p = WorkflowParser()
        fmt = p.detect_format("workflow_id: test\n")
        assert fmt == WorkflowFormat.YAML

    def test_parse_auto_json(self):
        p = WorkflowParser()
        d = json.dumps({"metadata": {}, "nodes": [], "edges": []})
        result = p.parse(d, WorkflowFormat.JSON)
        assert result is not None

    def test_parse_auto_yaml(self):
        p = WorkflowParser()
        yaml_str = "metadata:\n  name: y\n  version: '1.0.0'\nnodes: []\nedges: []\n"
        result = p.parse(yaml_str, WorkflowFormat.YAML)
        assert result is not None
