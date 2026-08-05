"""Tests for Resource Manager - Providers and Metrics."""

import pytest
from app.resources.providers import GPUProvider, ModelProvider, APIProvider, WorkspaceProvider
from app.resources.metrics import MetricsCollector
from app.resources.resource import Resource
from app.resources.interfaces import ResourceType


class TestGPUProvider:
    def test_register_gpu(self):
        gp = GPUProvider()
        gpu = gp.register_gpu("RTX 4090", 24576.0, 20000.0)
        assert gpu.name == "RTX 4090"
        assert gpu.capacity == 24576.0

    def test_vram_usage(self):
        gp = GPUProvider()
        gp.register_gpu("RTX 4090", 24576.0, 20000.0)
        gp.register_gpu("A100", 81920.0, 70000.0)
        usage = gp.get_vram_usage()
        assert usage["gpu_count"] == 2
        assert usage["total_vram_mb"] == 24576.0 + 81920.0

    def test_clear(self):
        gp = GPUProvider()
        gp.register_gpu("RTX 4090", 24576.0)
        gp.clear()
        assert len(gp.get_all()) == 0


class TestModelProvider:
    def test_register_model(self):
        mp = ModelProvider()
        model = mp.register_model("gpt-4", max_concurrent=5, rate_limit=10.0)
        assert model.name == "gpt-4"
        assert model.capacity == 5.0

    def test_get_model(self):
        mp = ModelProvider()
        mp.register_model("gpt-4")
        assert mp.get_model("gpt-4") is not None
        assert mp.get_model("claude-3") is None


class TestAPIProvider:
    def test_register_api(self):
        ap = APIProvider()
        api = ap.register_api("openai", rate_limit=100.0, token_budget=1_000_000.0)
        assert api.name == "openai"
        assert api.capacity == 100.0

    def test_get_all(self):
        ap = APIProvider()
        ap.register_api("openai")
        ap.register_api("anthropic")
        assert len(ap.get_all()) == 2


class TestWorkspaceProvider:
    def test_register_workspace(self):
        wp = WorkspaceProvider()
        ws = wp.register_workspace("ws-1", max_agents=5)
        assert ws.name == "ws-1"
        assert ws.capacity == 5.0


class TestMetricsCollector:
    def test_record_allocation(self):
        mc = MetricsCollector()
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=8.0, available=4.0, allocated=4.0)
        mc.record_allocation(r, 4.0, 10.5)
        m = mc.get_metrics(r.resource_id)
        assert m.allocation_count == 1

    def test_utilization_stats(self):
        mc = MetricsCollector()
        r = Resource(name="test", resource_type=ResourceType.CPU, capacity=100.0, available=40.0)
        mc.record_utilization(r)
        mc.record_utilization(r)
        stats = mc.get_utilization_stats(r.resource_id)
        assert stats["sample_count"] == 2
        assert stats["current"] == pytest.approx(0.6)

    def test_clear(self):
        mc = MetricsCollector()
        r = Resource(name="test", resource_type=ResourceType.CPU)
        mc.record_allocation(r, 1.0)
        mc.clear()
        assert len(mc.get_all_metrics()) == 0
