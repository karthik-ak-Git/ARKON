"""Tests for workflow loader."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from app.workflow.loader import WorkflowLoader
from app.workflow.exceptions import LoaderError


class TestLoaderFromString:
    def test_load_json_string(self):
        l = WorkflowLoader()
        d = json.dumps({
            "workflow_id": "wf1",
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [],
            "edges": [],
        })
        result = l.load_string(d)
        assert result["workflow_id"] == "wf1"

    def test_load_yaml_string(self):
        l = WorkflowLoader()
        yaml_str = """
workflow_id: wf1
metadata:
  name: test
  version: "1.0.0"
nodes: []
edges: []
"""
        result = l.load_string(yaml_str)
        assert result["workflow_id"] == "wf1"


class TestLoaderFromFile:
    def test_load_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "workflow_id": "wf1",
                "metadata": {"name": "test", "version": "1.0.0"},
                "nodes": [],
                "edges": [],
            }, f)
            f.flush()
            l = WorkflowLoader()
            result = l.load_file(f.name)
            assert result["workflow_id"] == "wf1"
        os.unlink(f.name)

    def test_load_yaml_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("workflow_id: wf1\nmetadata:\n  name: test\n  version: '1.0.0'\nnodes: []\nedges: []\n")
            f.flush()
            l = WorkflowLoader()
            result = l.load_file(f.name)
            assert result["workflow_id"] == "wf1"
        os.unlink(f.name)

    def test_load_nonexistent_file(self):
        l = WorkflowLoader()
        with pytest.raises(LoaderError):
            l.load_file("/nonexistent/workflow.json")

    def test_load_not_a_file(self):
        l = WorkflowLoader()
        with pytest.raises(LoaderError):
            l.load_file("/tmp")


class TestLoaderSaveToFile:
    def test_save_json(self):
        l = WorkflowLoader()
        defn = {
            "workflow_id": "wf1",
            "metadata": {"name": "test", "version": "1.0.0"},
            "nodes": [],
            "edges": [],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            l.save_file(defn, f.name)
            with open(f.name) as rf:
                d = json.load(rf)
                assert d["workflow_id"] == "wf1"
        os.unlink(f.name)
