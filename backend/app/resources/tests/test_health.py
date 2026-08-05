"""Tests for Resource Manager - Health and Monitor."""

import pytest
from app.resources.health import ResourceHealthTracker
from app.resources.monitor import ResourceMonitor
from app.resources.resource import Resource
from app.resources.interfaces import ResourceHealth, ResourceType


@pytest.fixture
def resources():
    return [
        Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=6.0),
        Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=20.0),
    ]


class TestResourceHealthTracker:
    def test_record_health(self):
        tracker = ResourceHealthTracker()
        r = Resource(name="test", resource_type=ResourceType.CPU)
        tracker.record_health(r, ResourceHealth.HEALTHY)
        assert r.health == ResourceHealth.HEALTHY

        tracker.record_health(r, ResourceHealth.DEGRADED)
        assert r.health == ResourceHealth.DEGRADED

    def test_health_history(self):
        tracker = ResourceHealthTracker()
        r = Resource(name="test", resource_type=ResourceType.CPU)
        tracker.record_health(r, ResourceHealth.HEALTHY)
        tracker.record_health(r, ResourceHealth.DEGRADED)
        tracker.record_health(r, ResourceHealth.BUSY)

        history = tracker.get_history(r.resource_id)
        assert len(history) == 3
        assert history[2].health == ResourceHealth.BUSY

    def test_get_healthy_resources(self, resources):
        tracker = ResourceHealthTracker()
        resources[0].health = ResourceHealth.HEALTHY
        resources[1].health = ResourceHealth.DEGRADED
        healthy = tracker.get_healthy_resources(resources)
        assert len(healthy) == 1
        assert healthy[0].name == "cpu-1"

    def test_get_unhealthy_resources(self, resources):
        tracker = ResourceHealthTracker()
        resources[0].health = ResourceHealth.UNAVAILABLE
        resources[1].health = ResourceHealth.MAINTENANCE
        unhealthy = tracker.get_unhealthy_resources(resources)
        assert len(unhealthy) == 2


class TestResourceMonitor:
    def test_check_resource_ok(self):
        monitor = ResourceMonitor()
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=8.0, available=6.0)
        report = monitor.check_resource(r)
        assert report["status"] == "ok"

    def test_check_resource_warning(self):
        monitor = ResourceMonitor()
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=8.0, available=1.5)
        report = monitor.check_resource(r)
        assert report["status"] == "warning"

    def test_check_resource_critical(self):
        monitor = ResourceMonitor()
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=8.0, available=0.3)
        report = monitor.check_resource(r)
        assert report["status"] == "critical"

    def test_check_all(self, resources):
        monitor = ResourceMonitor()
        reports = monitor.check_all(resources)
        assert len(reports) == 2

    def test_utilization_report(self, resources):
        monitor = ResourceMonitor()
        report = monitor.get_utilization_report(resources)
        assert report["resource_count"] == 2
        assert "by_type" in report

    def test_health_change_callback(self):
        monitor = ResourceMonitor()
        changes = []
        monitor.on_health_change(lambda rid, h, d: changes.append((rid, h)))
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=8.0, available=0.3)
        monitor.check_resource(r)
        assert len(changes) == 1
