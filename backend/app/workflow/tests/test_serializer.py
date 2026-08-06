"""Tests for workflow serializer."""

import pytest
import json
from app.workflow.serializer import WorkflowSerializer
from app.workflow.interfaces import WorkflowFormat
from app.workflow.exceptions import SerializerError


def _simple_def():
    return {
        "workflow_id": "wf1",
        "metadata": {"name": "test", "version": "1.0.0"},
        "nodes": [{"node_id": "n1", "name": "A", "capability": "cap"}],
        "edges": [],
    }


class TestYAMLSer:
    def test_serialize_yaml(self):
        s = WorkflowSerializer()
        output = s.serialize(_simple_def(), WorkflowFormat.YAML)
        assert "name: test" in output
        assert "node_id: n1" in output

    def test_roundtrip_yaml(self):
        s = WorkflowSerializer()
        output = s.serialize(_simple_def(), WorkflowFormat.YAML)
        result = s.deserialize(output, WorkflowFormat.YAML)
        assert result["workflow_id"] == "wf1"
        assert len(result["nodes"]) == 1


class TestJSONSer:
    def test_serialize_json(self):
        s = WorkflowSerializer()
        output = s.serialize(_simple_def(), WorkflowFormat.JSON)
        d = json.loads(output)
        assert d["workflow_id"] == "wf1"

    def test_roundtrip_json(self):
        s = WorkflowSerializer()
        output = s.serialize(_simple_def(), WorkflowFormat.JSON)
        result = s.deserialize(output, WorkflowFormat.JSON)
        assert result["workflow_id"] == "wf1"
        assert len(result["nodes"]) == 1

    def test_canonical_json(self):
        s = WorkflowSerializer()
        canonical = s.to_canonical(_simple_def())
        d = json.loads(canonical)
        assert "workflow_id" in d
        assert d["workflow_id"] == "wf1"


class TestSerializerErrors:
    def test_invalid_yaml(self):
        s = WorkflowSerializer()
        with pytest.raises(SerializerError):
            s.deserialize("}{bad yaml{[", WorkflowFormat.YAML)

    def test_invalid_json(self):
        s = WorkflowSerializer()
        with pytest.raises(SerializerError):
            s.deserialize("not json", WorkflowFormat.JSON)

    def test_empty_content(self):
        s = WorkflowSerializer()
        with pytest.raises(SerializerError):
            s.deserialize("", WorkflowFormat.YAML)
