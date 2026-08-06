"""Tests for workflow registry and templates."""

import pytest
from app.workflow.registry import TemplateRegistry, WorkflowTemplate
from app.workflow.templates import register_builtins
from app.workflow.exceptions import TemplateNotFoundError, RegistryError


class TestWorkflowTemplate:
    def test_creation(self):
        t = WorkflowTemplate(
            template_id="tpl1",
            name="Test",
            definition={"nodes": [], "edges": []},
            description="A test template",
        )
        assert t.template_id == "tpl1"
        assert t.tags == []

    def test_creation_with_tags(self):
        t = WorkflowTemplate(
            template_id="tpl1",
            name="T",
            definition={},
            tags=["video", "render"],
        )
        assert t.tags == ["video", "render"]

    def test_to_dict(self):
        t = WorkflowTemplate(template_id="tpl1", name="T", definition={}, description="d")
        d = t.to_dict()
        assert d["template_id"] == "tpl1"
        assert d["name"] == "T"
        assert d["description"] == "d"


class TestTemplateRegistry:
    def test_empty_registry(self):
        r = TemplateRegistry()
        assert r.list_templates() == []
        assert r.count() == 0

    def test_register_and_get(self):
        r = TemplateRegistry()
        t = WorkflowTemplate(template_id="t1", name="T", definition={})
        r.register(t)
        found = r.get("t1")
        assert found.name == "T"

    def test_register_duplicate_raises(self):
        r = TemplateRegistry()
        t = WorkflowTemplate(template_id="t1", name="T", definition={})
        r.register(t)
        with pytest.raises(RegistryError, match="already"):
            r.register(t)

    def test_get_missing_raises(self):
        r = TemplateRegistry()
        with pytest.raises(TemplateNotFoundError):
            r.get("nope")

    def test_unregister(self):
        r = TemplateRegistry()
        t = WorkflowTemplate(template_id="t1", name="T", definition={})
        r.register(t)
        r.unregister("t1")
        assert r.has("t1") is False

    def test_list_by_tag(self):
        r = TemplateRegistry()
        r.register(WorkflowTemplate(template_id="t1", name="A", definition={}, tags=["video"]))
        r.register(WorkflowTemplate(template_id="t2", name="B", definition={}, tags=["audio"]))
        r.register(WorkflowTemplate(template_id="t3", name="C", definition={}, tags=["video"]))
        video = r.list_by_tag("video")
        assert len(video) == 2

    def test_has(self):
        r = TemplateRegistry()
        assert r.has("x") is False
        r.register(WorkflowTemplate(template_id="x", name="X", definition={}))
        assert r.has("x") is True

    def test_count(self):
        r = TemplateRegistry()
        assert r.count() == 0
        r.register(WorkflowTemplate(template_id="t1", name="A", definition={}))
        assert r.count() == 1

    def test_clear(self):
        r = TemplateRegistry()
        r.register(WorkflowTemplate(template_id="t1", name="A", definition={}))
        r.clear()
        assert r.count() == 0


class TestBuiltInTemplates:
    def test_register_builtins(self):
        r = TemplateRegistry()
        register_builtins(r)
        assert r.count() >= 3

    def test_linear_pipeline_exists(self):
        r = TemplateRegistry()
        register_builtins(r)
        t = r.get("linear_pipeline")
        assert t.name == "Linear Pipeline"

    def test_fan_out_fan_in_exists(self):
        r = TemplateRegistry()
        register_builtins(r)
        t = r.get("fan_out_fan_in")
        assert t.name == "Fan-Out Fan-In"

    def test_conditional_exists(self):
        r = TemplateRegistry()
        register_builtins(r)
        t = r.get("conditional")
        assert t.name == "Conditional Branch"
