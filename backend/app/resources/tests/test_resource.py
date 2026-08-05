"""Tests for Resource Manager - Resource model."""

import pytest
from app.resources.resource import Resource
from app.resources.interfaces import ResourceHealth, ResourceStatus, ResourceType


class TestResource:
    def test_create_resource(self):
        r = Resource(name="cpu", resource_type=ResourceType.CPU, capacity=8.0)
        assert r.name == "cpu"
        assert r.resource_type == ResourceType.CPU
        assert r.capacity == 8.0
        assert r.available == 8.0
        assert r.health == ResourceHealth.UNKNOWN

    def test_resource_id_auto(self):
        r = Resource(name="test", resource_type=ResourceType.RAM)
        assert r.resource_id is not None
        assert len(r.resource_id) == 16

    def test_resource_to_dict(self):
        r = Resource(name="gpu", resource_type=ResourceType.GPU, capacity=24.0)
        d = r.to_dict()
        assert d["name"] == "gpu"
        assert d["resource_type"] == "gpu"
        assert d["capacity"] == 24.0

    def test_resource_from_dict(self):
        data = {"name": "disk", "resource_type": "disk", "capacity": 100.0}
        r = Resource.from_dict(data)
        assert r.name == "disk"
        assert r.resource_type == ResourceType.DISK
        assert r.capacity == 100.0

    def test_update_status_free(self):
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=8.0, available=8.0)
        r.update_status()
        assert r.status == ResourceStatus.FREE

    def test_update_status_exhausted(self):
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=8.0, available=0.0)
        r.update_status()
        assert r.status == ResourceStatus.EXHAUSTED

    def test_update_status_allocated(self):
        r = Resource(
            name="test",
            resource_type=ResourceType.CPU,
            capacity=8.0,
            available=4.0,
            allocated=4.0,
            health=ResourceHealth.HEALTHY,
        )
        r.update_status()
        assert r.status == ResourceStatus.ALLOCATED

    def test_tags_and_metadata(self):
        r = Resource(
            name="test",
            resource_type=ResourceType.GPU,
            tags=["cuda", "compute"],
            metadata={"device": "cuda:0"},
        )
        assert r.get_tags() == ["cuda", "compute"]
        assert r.get_metadata() == {"device": "cuda:0"}

    def test_utilization(self):
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=100.0, available=40.0)
        assert r.utilization == pytest.approx(0.6)

    def test_priority(self):
        r = Resource(name="test", resource_type=ResourceType.CPU, priority=5)
        assert r.get_priority() == 5
