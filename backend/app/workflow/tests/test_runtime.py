"""Tests for workflow runtime (orchestrator)."""

import pytest
import json
from app.workflow.runtime import WorkflowRuntime
from app.workflow.interfaces import WorkflowFormat
from app.workflow.exceptions import WorkflowCompilationError, WorkflowNotFoundError


def _simple_def():
    return {
        "workflow_id": "wf1",
        "metadata": {"name": "test", "version": "1.0.0"},
        "nodes": [
            {"node_id": "n1", "name": "A", "capability": "cap.a"},
            {"node_id": "n2", "name": "B", "capability": "cap.b"},
        ],
        "edges": [],
    }


class TestRuntimeLoad:
    def test_load_workflow(self):
        r = WorkflowRuntime()
        wf_id = r.load(_simple_def())
        assert wf_id == "wf1"
        assert r.has_workflow("wf1")

    def test_load_returns_id(self):
        r = WorkflowRuntime()
        wf_id = r.load({"workflow_id": "my_wf", "nodes": []})
        assert wf_id == "my_wf"

    def test_load_from_string_json(self):
        r = WorkflowRuntime()
        d = json.dumps({
            "workflow_id": "wf_json",
            "metadata": {"name": "j", "version": "1.0.0"},
            "nodes": [],
            "edges": [],
        })
        wf_id = r.load_from_string(d)
        assert wf_id == "wf_json"

    def test_load_from_string_yaml(self):
        r = WorkflowRuntime()
        yaml_str = "workflow_id: wf_yaml\nmetadata:\n  name: y\n  version: '1.0.0'\nnodes: []\nedges: []\n"
        wf_id = r.load_from_string(yaml_str)
        assert wf_id == "wf_yaml"

    def test_get_workflow(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        wf = r.get_workflow("wf1")
        assert wf["workflow_id"] == "wf1"

    def test_get_missing_workflow(self):
        r = WorkflowRuntime()
        with pytest.raises(WorkflowNotFoundError):
            r.get_workflow("nope")

    def test_list_workflows(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        r.load({"workflow_id": "wf2", "nodes": []})
        assert len(r.list_workflows()) == 2

    def test_has_workflow(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        assert r.has_workflow("wf1") is True
        assert r.has_workflow("nope") is False

    def test_remove_workflow(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        r.remove_workflow("wf1")
        assert r.has_workflow("wf1") is False


class TestRuntimeValidate:
    def test_validate_workflow(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        result = r.validate("wf1")
        assert result.is_valid is True

    def test_validate_missing(self):
        r = WorkflowRuntime()
        with pytest.raises(WorkflowNotFoundError):
            r.validate("nope")

    def test_validate_definition(self):
        r = WorkflowRuntime()
        result = r.validate_definition(_simple_def())
        assert result.is_valid is True

    def test_validate_invalid_definition(self):
        r = WorkflowRuntime()
        result = r.validate_definition({"metadata": {}, "edges": []})
        assert result.is_valid is False


class TestRuntimeCompile:
    def test_compile_workflow(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        plan = r.compile("wf1")
        assert plan.workflow_id == "wf1"
        assert len(plan.tasks) == 2

    def test_compile_missing(self):
        r = WorkflowRuntime()
        with pytest.raises(WorkflowNotFoundError):
            r.compile("nope")

    def test_compile_definition(self):
        r = WorkflowRuntime()
        plan = r.compile_definition(_simple_def())
        assert len(plan.tasks) == 2

    def test_compile_and_store_plan(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        plan = r.compile("wf1")
        found = r.get_plan(plan.plan_id)
        assert found is plan

    def test_get_plan_for_workflow(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        plan = r.compile("wf1")
        found = r.get_plan_for_workflow("wf1")
        assert found is plan

    def test_get_plan_missing(self):
        r = WorkflowRuntime()
        assert r.get_plan("nonexistent") is None


class TestRuntimeVersioning:
    def test_save_version(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        v_id = r.save_version("wf1", "1.0.0", "Initial")
        assert v_id is not None

    def test_get_version(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        r.save_version("wf1", "1.0.0")
        v = r.get_version("wf1", "1.0.0")
        assert v["workflow_id"] == "wf1"

    def test_list_versions(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        r.save_version("wf1", "1.0.0")
        r.save_version("wf1", "2.0.0")
        versions = r.list_versions("wf1")
        assert len(versions) == 2

    def test_get_latest_version(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        r.save_version("wf1", "1.0.0")
        r.save_version("wf1", "2.0.0")
        v = r.get_latest_version("wf1")
        assert v["workflow_id"] == "wf1"


class TestRuntimeTemplates:
    def test_list_templates(self):
        r = WorkflowRuntime()
        templates = r.list_templates()
        assert len(templates) >= 3

    def test_get_template(self):
        r = WorkflowRuntime()
        t = r.get_template("linear_pipeline")
        assert t is not None
        assert t.name == "Linear Pipeline"

    def test_get_template_missing(self):
        r = WorkflowRuntime()
        with pytest.raises(Exception):
            r.get_template("nonexistent")

    def test_register_custom_template(self):
        from app.workflow.registry import WorkflowTemplate
        r = WorkflowRuntime()
        t = WorkflowTemplate(template_id="custom", name="Custom", definition={"nodes": []})
        r.register_template(t)
        found = r.get_template("custom")
        assert found.name == "Custom"


class TestRuntimeSerialize:
    def test_serialize_yaml(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        output = r.serialize("wf1", WorkflowFormat.YAML)
        assert "name: test" in output

    def test_serialize_json(self):
        r = WorkflowRuntime()
        r.load(_simple_def())
        output = r.serialize("wf1", WorkflowFormat.JSON)
        d = json.loads(output)
        assert d["workflow_id"] == "wf1"

    def test_serialize_missing(self):
        r = WorkflowRuntime()
        with pytest.raises(WorkflowNotFoundError):
            r.serialize("nope")
