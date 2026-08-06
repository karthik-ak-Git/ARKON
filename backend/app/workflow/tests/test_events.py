"""Tests for workflow events."""

import pytest
from app.workflow.events import (
    workflow_compiled_event,
    workflow_failed_event,
    workflow_loaded_event,
    workflow_validated_event,
)


class TestWorkflowEvents:
    def test_loaded_event(self):
        e = workflow_loaded_event("wf1", name="Test", version="1.0.0", node_count=3)
        assert e.event_type == "workflow.loaded"
        assert e.payload["workflow_id"] == "wf1"
        assert e.payload["name"] == "Test"
        assert e.payload["node_count"] == 3

    def test_validated_event(self):
        e = workflow_validated_event("wf1", is_valid=True, error_count=0)
        assert e.event_type == "workflow.validated"
        assert e.payload["is_valid"] is True

    def test_compiled_event(self):
        e = workflow_compiled_event("wf1", plan_id="plan1", task_count=5)
        assert e.event_type == "workflow.compiled"
        assert e.payload["plan_id"] == "plan1"
        assert e.payload["task_count"] == 5

    def test_failed_event(self):
        e = workflow_failed_event("wf1", error="bad input", phase="validation")
        assert e.event_type == "workflow.failed"
        assert e.payload["error"] == "bad input"
        assert e.payload["phase"] == "validation"

    def test_loaded_event_has_source(self):
        e = workflow_loaded_event("wf1")
        assert e.metadata.source == "workflow_runtime"

    def test_loaded_event_has_tag(self):
        e = workflow_loaded_event("wf1")
        assert "workflow:wf1" in e.metadata.tags
