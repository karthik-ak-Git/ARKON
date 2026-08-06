"""Tests for workflow versioning."""

import pytest
from app.workflow.versioning import WorkflowVersionManager, WorkflowVersion
from app.workflow.exceptions import WorkflowVersionError


class TestWorkflowVersion:
    def test_creation(self):
        v = WorkflowVersion(
            version_id="wf1:1.0.0",
            version="1.0.0",
            workflow_id="wf1",
            definition={"nodes": []},
        )
        assert v.version == "1.0.0"
        assert v.workflow_id == "wf1"

    def test_to_dict(self):
        v = WorkflowVersion(
            version_id="wf1:2.0.0",
            version="2.0.0",
            workflow_id="wf1",
            definition={"nodes": []},
            description="Updated nodes",
        )
        d = v.to_dict() if hasattr(v, 'to_dict') else v.__dict__
        assert d["version"] == "2.0.0"
        assert d["description"] == "Updated nodes"


class TestVersionManager:
    def test_empty_manager(self):
        m = WorkflowVersionManager()
        assert m.list_versions("wf1") == []

    def test_create_version(self):
        m = WorkflowVersionManager()
        v = m.create_version("wf1", {"nodes": []}, "1.0.0", "Initial")
        assert v.version == "1.0.0"
        assert v.workflow_id == "wf1"

    def test_get_version(self):
        m = WorkflowVersionManager()
        m.create_version("wf1", {}, "1.0.0")
        v = m.get_version("wf1", "1.0.0")
        assert v.version == "1.0.0"

    def test_get_missing_version(self):
        m = WorkflowVersionManager()
        with pytest.raises(WorkflowVersionError):
            m.get_version("wf1", "9.0.0")

    def test_list_versions(self):
        m = WorkflowVersionManager()
        m.create_version("wf1", {}, "1.0.0")
        m.create_version("wf1", {}, "2.0.0")
        m.create_version("wf2", {}, "1.0.0")
        v1 = m.list_versions("wf1")
        assert len(v1) == 2

    def test_get_latest(self):
        m = WorkflowVersionManager()
        m.create_version("wf1", {}, "1.0.0")
        m.create_version("wf1", {"updated": True}, "2.0.0")
        latest = m.get_latest("wf1")
        assert latest.version == "2.0.0"

    def test_get_latest_empty(self):
        m = WorkflowVersionManager()
        with pytest.raises(WorkflowVersionError):
            m.get_latest("wf1")

    def test_compatible_versions(self):
        m = WorkflowVersionManager()
        assert m.is_compatible("1.0.0", "1.1.0") is True
        assert m.is_compatible("1.0.0", "2.0.0") is False

    def test_bump_major(self):
        m = WorkflowVersionManager()
        new_ver = m.bump_version("1.2.3", "major")
        assert new_ver == "2.0.0"

    def test_bump_minor(self):
        m = WorkflowVersionManager()
        new_ver = m.bump_version("1.2.3", "minor")
        assert new_ver == "1.3.0"

    def test_bump_patch(self):
        m = WorkflowVersionManager()
        new_ver = m.bump_version("1.2.3", "patch")
        assert new_ver == "1.2.4"

    def test_invalid_bump_type(self):
        m = WorkflowVersionManager()
        with pytest.raises(WorkflowVersionError):
            m.bump_version("1.0.0", "invalid")

    def test_invalid_version_format(self):
        m = WorkflowVersionManager()
        with pytest.raises(WorkflowVersionError):
            m.bump_version("1.0", "patch")

    def test_list_workflows(self):
        m = WorkflowVersionManager()
        m.create_version("wf1", {}, "1.0.0")
        m.create_version("wf2", {}, "1.0.0")
        workflows = m.list_workflows()
        assert len(workflows) == 2
