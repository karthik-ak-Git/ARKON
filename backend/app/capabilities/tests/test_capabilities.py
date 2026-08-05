"""ARKON Capability Registry Tests.

Comprehensive tests for the capability registry module.
"""

from __future__ import annotations

import asyncio
import os

import pytest

os.environ.setdefault("ARKON_ENV", "test")

from app.capabilities.interfaces import (
    ProviderHealth,
    RankingStrategy,
    ProviderType,
)
from app.capabilities.exceptions import (
    ProviderNotFoundError,
    ProviderAlreadyExistsError,
    NoProviderAvailableError,
    CapabilityNotFoundError,
)
from app.capabilities.capability import Capability
from app.capabilities.provider import Provider
from app.capabilities.matcher import ProviderMatcher
from app.capabilities.ranking import ProviderRanker
from app.capabilities.health import HealthTracker
from app.capabilities.resolver import CapabilityResolver
from app.capabilities.registry import CapabilityRegistry


# =============================================================================
# Capability Tests
# =============================================================================


class TestCapability:
    """Tests for Capability dataclass."""

    def test_create_capability(self):
        cap = Capability(name="transcription")
        assert cap.get_name() == "transcription"
        assert cap.get_category() == "general"
        assert cap.get_tags() == []

    def test_create_with_details(self):
        cap = Capability(
            name="video_rendering",
            description="Render video files",
            category="media",
            tags=["gpu", "video"],
            version="2.0.0",
        )
        assert cap.get_description() == "Render video files"
        assert cap.get_category() == "media"
        assert "gpu" in cap.get_tags()
        assert cap.get_version() == "2.0.0"

    def test_tags_are_copy(self):
        cap = Capability(name="test", tags=["a"])
        tags = cap.get_tags()
        tags.append("b")
        assert cap.get_tags() == ["a"]

    def test_roundtrip(self):
        cap = Capability(
            name="test",
            description="desc",
            category="cat",
            tags=["t1"],
            metadata={"k": "v"},
        )
        d = cap.to_dict()
        restored = Capability.from_dict(d)
        assert restored.name == "test"
        assert restored.description == "desc"
        assert restored.category == "cat"
        assert restored.tags == ["t1"]
        assert restored.metadata == {"k": "v"}


# =============================================================================
# Provider Tests
# =============================================================================


class TestProvider:
    """Tests for Provider dataclass."""

    def test_create_provider(self):
        p = Provider(name="agent-1", capabilities=["transcription"])
        assert p.get_name() == "agent-1"
        assert "transcription" in p.get_capabilities()
        assert p.get_health() == ProviderHealth.UNKNOWN

    def test_provider_availability(self):
        p = Provider(name="test", health=ProviderHealth.HEALTHY)
        assert p.is_available() is True

        p.health = ProviderHealth.UNAVAILABLE
        assert p.is_available() is False

    def test_provider_capabilities_copy(self):
        p = Provider(name="test", capabilities=["a", "b"])
        caps = p.get_capabilities()
        caps.append("c")
        assert p.get_capabilities() == ["a", "b"]

    def test_roundtrip(self):
        p = Provider(
            name="test",
            version="2.0.0",
            provider_type=ProviderType.AGENT,
            capabilities=["cap1", "cap2"],
            priority=5,
            cost=1.5,
            latency=100.0,
            health=ProviderHealth.HEALTHY,
            tags=["gpu"],
            required_resources={"gpu": True},
            workspace_scope="ws1",
        )
        d = p.to_dict()
        restored = Provider.from_dict(d)
        assert restored.name == "test"
        assert restored.version == "2.0.0"
        assert restored.provider_type == ProviderType.AGENT
        assert restored.capabilities == ["cap1", "cap2"]
        assert restored.priority == 5
        assert restored.cost == 1.5
        assert restored.latency == 100.0
        assert restored.health == ProviderHealth.HEALTHY
        assert restored.tags == ["gpu"]
        assert restored.required_resources == {"gpu": True}
        assert restored.workspace_scope == "ws1"


# =============================================================================
# Matcher Tests
# =============================================================================


class TestProviderMatcher:
    """Tests for ProviderMatcher."""

    @pytest.fixture
    def matcher(self):
        return ProviderMatcher()

    @pytest.fixture
    def providers(self):
        return [
            Provider(
                name="agent-1",
                capabilities=["transcription", "caption"],
                tags=["gpu", "fast"],
                priority=1,
                cost=0.5,
                latency=50.0,
                health=ProviderHealth.HEALTHY,
            ),
            Provider(
                name="agent-2",
                capabilities=["transcription", "reasoning"],
                tags=["cpu"],
                priority=2,
                cost=0.1,
                latency=200.0,
                health=ProviderHealth.DEGRADED,
            ),
            Provider(
                name="agent-3",
                capabilities=["vision"],
                tags=["gpu"],
                priority=3,
                cost=2.0,
                latency=100.0,
                health=ProviderHealth.UNAVAILABLE,
                available=False,
            ),
        ]

    def test_match_by_capability(self, matcher, providers):
        result = matcher.match(providers, capability="transcription")
        assert len(result) == 2

    def test_match_by_tags(self, matcher, providers):
        # Pass require_healthy=False to isolate tag matching from health filtering
        result = matcher.match(providers, tags=["gpu"], require_healthy=False)
        assert len(result) == 2

    def test_match_by_priority(self, matcher, providers):
        result = matcher.match(providers, max_priority=1)
        assert len(result) == 1
        assert result[0].get_name() == "agent-1"

    def test_match_by_cost(self, matcher, providers):
        result = matcher.match(providers, max_cost=0.5)
        assert len(result) == 2

    def test_match_by_latency(self, matcher, providers):
        # Pass require_healthy=False to include agent-3 (UNAVAILABLE, latency=100)
        result = matcher.match(providers, max_latency=100.0, require_healthy=False)
        assert len(result) == 2

    def test_match_healthy_only(self, matcher, providers):
        result = matcher.match(providers, require_healthy=True)
        assert len(result) == 2  # healthy + degraded, not unavailable

    def test_match_all_filters(self, matcher, providers):
        result = matcher.match(
            providers,
            capability="transcription",
            tags=["gpu"],
            max_cost=1.0,
            require_healthy=True,
        )
        assert len(result) == 1
        assert result[0].get_name() == "agent-1"

    def test_match_no_results(self, matcher, providers):
        result = matcher.match(providers, capability="nonexistent")
        assert len(result) == 0

    def test_match_any_capability(self, matcher, providers):
        result = matcher.match_any_capability(
            providers, ["vision", "reasoning"]
        )
        assert len(result) == 2

    def test_has_required_resources(self, matcher):
        p = Provider(name="test", required_resources={"gpu": True, "ram": "16gb"})
        assert matcher.has_required_resources(p, {"gpu": True}) is True
        assert matcher.has_required_resources(p, {"gpu": True, "ram": "16gb"}) is True
        assert matcher.has_required_resources(p, {"gpu": True, "ram": "32gb"}) is False


# =============================================================================
# Ranker Tests
# =============================================================================


class TestProviderRanker:
    """Tests for ProviderRanker."""

    @pytest.fixture
    def ranker(self):
        return ProviderRanker()

    @pytest.fixture
    def providers(self):
        return [
            Provider(
                name="slow-cheap",
                priority=3,
                cost=0.1,
                latency=500.0,
                health=ProviderHealth.HEALTHY,
            ),
            Provider(
                name="fast-expensive",
                priority=1,
                cost=5.0,
                latency=10.0,
                health=ProviderHealth.HEALTHY,
            ),
            Provider(
                name="medium",
                priority=2,
                cost=1.0,
                latency=100.0,
                health=ProviderHealth.DEGRADED,
            ),
        ]

    def test_rank_priority(self, ranker, providers):
        result = ranker.rank(providers, RankingStrategy.HIGHEST_PRIORITY)
        assert result[0].get_name() == "fast-expensive"

    def test_rank_cost(self, ranker, providers):
        result = ranker.rank(providers, RankingStrategy.LOWEST_COST)
        assert result[0].get_name() == "slow-cheap"

    def test_rank_latency(self, ranker, providers):
        result = ranker.rank(providers, RankingStrategy.FASTEST)
        assert result[0].get_name() == "fast-expensive"

    def test_rank_local_first(self, ranker):
        local = Provider(name="local", workspace_scope="ws1", priority=2)
        global_p = Provider(name="global", priority=1)
        result = ranker.rank([global_p, local], RankingStrategy.LOCAL_FIRST)
        assert result[0].get_name() == "local"

    def test_rank_health(self, ranker, providers):
        result = ranker.rank(providers, RankingStrategy.HEALTHY_FIRST)
        assert result[0].get_health() == ProviderHealth.HEALTHY

    def test_rank_composite(self, ranker, providers):
        result = ranker.rank(providers, RankingStrategy.WEIGHTED_COMPOSITE)
        assert len(result) == 3

    def test_rank_empty(self, ranker):
        result = ranker.rank([], RankingStrategy.HIGHEST_PRIORITY)
        assert len(result) == 0


# =============================================================================
# HealthTracker Tests
# =============================================================================


class TestHealthTracker:
    """Tests for HealthTracker."""

    @pytest.fixture
    def tracker(self):
        return HealthTracker()

    def test_get_unknown(self, tracker):
        assert tracker.get_health("p1") == ProviderHealth.UNKNOWN

    def test_set_health(self, tracker):
        old = tracker.set_health("p1", ProviderHealth.HEALTHY)
        assert old is None
        assert tracker.get_health("p1") == ProviderHealth.HEALTHY

    def test_set_health_changed(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        old = tracker.set_health("p1", ProviderHealth.DEGRADED)
        assert old == ProviderHealth.HEALTHY

    def test_set_health_same(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        old = tracker.set_health("p1", ProviderHealth.HEALTHY)
        assert old is None

    def test_history(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        tracker.set_health("p1", ProviderHealth.DEGRADED)
        history = tracker.get_history("p1")
        assert len(history) == 2
        assert history[0]["new"] == "healthy"
        assert history[1]["new"] == "degraded"

    def test_is_healthy(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        assert tracker.is_healthy("p1") is True

        tracker.set_health("p1", ProviderHealth.DEGRADED)
        assert tracker.is_healthy("p1") is True

        tracker.set_health("p1", ProviderHealth.UNAVAILABLE)
        assert tracker.is_healthy("p1") is False

    def test_get_all_health(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        tracker.set_health("p2", ProviderHealth.DEGRADED)
        all_health = tracker.get_all_health()
        assert all_health["p1"] == "healthy"
        assert all_health["p2"] == "degraded"

    def test_remove(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        tracker.remove("p1")
        assert tracker.get_health("p1") == ProviderHealth.UNKNOWN

    def test_clear(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        tracker.clear()
        assert tracker.get_health("p1") == ProviderHealth.UNKNOWN

    def test_summary(self, tracker):
        tracker.set_health("p1", ProviderHealth.HEALTHY)
        tracker.set_health("p2", ProviderHealth.HEALTHY)
        tracker.set_health("p3", ProviderHealth.DEGRADED)
        summary = tracker.get_summary()
        assert summary["total"] == 3
        assert summary["by_status"]["healthy"] == 2
        assert summary["by_status"]["degraded"] == 1


# =============================================================================
# Resolver Tests
# =============================================================================


class TestCapabilityResolver:
    """Tests for CapabilityResolver."""

    @pytest.fixture
    def resolver(self):
        return CapabilityResolver()

    @pytest.fixture
    def providers(self):
        return [
            Provider(
                name="fast-gpu",
                capabilities=["transcription"],
                tags=["gpu"],
                priority=1,
                cost=5.0,
                latency=10.0,
                health=ProviderHealth.HEALTHY,
            ),
            Provider(
                name="slow-cpu",
                capabilities=["transcription"],
                tags=["cpu"],
                priority=3,
                cost=0.1,
                latency=500.0,
                health=ProviderHealth.HEALTHY,
            ),
        ]

    def test_resolve_basic(self, resolver, providers):
        result = resolver.resolve(providers, capability="transcription")
        assert len(result) == 2

    def test_resolve_with_tags(self, resolver, providers):
        result = resolver.resolve(
            providers, capability="transcription", tags=["gpu"]
        )
        assert len(result) == 1
        assert result[0].get_name() == "fast-gpu"

    def test_resolve_with_cost_limit(self, resolver, providers):
        result = resolver.resolve(
            providers, capability="transcription", max_cost=1.0
        )
        assert len(result) == 1
        assert result[0].get_name() == "slow-cpu"

    def test_resolve_no_match(self, resolver, providers):
        result = resolver.resolve(providers, capability="vision")
        assert len(result) == 0

    def test_resolve_any(self, resolver, providers):
        result = resolver.resolve_any(
            providers, ["transcription", "vision"]
        )
        assert len(result) == 2


# =============================================================================
# Registry Integration Tests
# =============================================================================


class TestCapabilityRegistry:
    """Integration tests for the full capability registry."""

    @pytest.fixture
    def registry(self):
        return CapabilityRegistry()

    @pytest.mark.asyncio
    async def test_register_provider(self, registry):
        p = Provider(
            name="test-agent",
            capabilities=["transcription"],
            priority=1,
        )
        await registry.register_provider(p)

        providers = await registry.list_providers()
        assert len(providers) == 1
        assert providers[0].get_name() == "test-agent"

    @pytest.mark.asyncio
    async def test_register_duplicate_provider(self, registry):
        p = Provider(name="test-agent", provider_id="dup1", capabilities=["test"])
        await registry.register_provider(p)
        with pytest.raises(ProviderAlreadyExistsError):
            await registry.register_provider(p)

    @pytest.mark.asyncio
    async def test_unregister_provider(self, registry):
        p = Provider(name="test-agent", provider_id="del1", capabilities=["test"])
        await registry.register_provider(p)
        await registry.unregister_provider("del1")
        assert await registry.get_provider("del1") is None

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self, registry):
        with pytest.raises(ProviderNotFoundError):
            await registry.unregister_provider("nonexistent")

    @pytest.mark.asyncio
    async def test_resolve_capability(self, registry):
        p1 = Provider(
            name="agent-1",
            capabilities=["transcription"],
            priority=1,
            health=ProviderHealth.HEALTHY,
        )
        p2 = Provider(
            name="agent-2",
            capabilities=["transcription"],
            priority=2,
            health=ProviderHealth.HEALTHY,
        )
        await registry.register_provider(p1)
        await registry.register_provider(p2)

        result = await registry.resolve("transcription")
        assert len(result) == 2
        assert result[0].get_priority() <= result[1].get_priority()

    @pytest.mark.asyncio
    async def test_resolve_no_providers(self, registry):
        with pytest.raises(NoProviderAvailableError):
            await registry.resolve("nonexistent")

    @pytest.mark.asyncio
    async def test_resolve_with_health_filter(self, registry):
        p1 = Provider(
            name="healthy",
            capabilities=["test"],
            health=ProviderHealth.HEALTHY,
        )
        p2 = Provider(
            name="unavailable",
            capabilities=["test"],
            health=ProviderHealth.UNAVAILABLE,
            available=False,
        )
        await registry.register_provider(p1)
        await registry.register_provider(p2)

        result = await registry.resolve("test", require_healthy=True)
        assert len(result) == 1
        assert result[0].get_name() == "healthy"

    @pytest.mark.asyncio
    async def test_update_health(self, registry):
        p = Provider(
            name="test-agent",
            provider_id="hp1",
            capabilities=["test"],
            health=ProviderHealth.HEALTHY,
        )
        await registry.register_provider(p)
        await registry.update_provider_health("hp1", ProviderHealth.DEGRADED)

        assert registry.get_provider_health("hp1") == ProviderHealth.DEGRADED

    @pytest.mark.asyncio
    async def test_update_health_nonexistent(self, registry):
        with pytest.raises(ProviderNotFoundError):
            await registry.update_provider_health("nonexistent", ProviderHealth.HEALTHY)

    @pytest.mark.asyncio
    async def test_list_capabilities(self, registry):
        p = Provider(name="agent", capabilities=["cap1", "cap2"])
        await registry.register_provider(p)

        caps = await registry.list_capabilities()
        assert "cap1" in caps
        assert "cap2" in caps

    @pytest.mark.asyncio
    async def test_register_capability(self, registry):
        cap = Capability(name="custom_cap", description="Custom capability")
        await registry.register_capability(cap)

        info = await registry.get_capability_info("custom_cap")
        assert info is not None
        assert info.get_name() == "custom_cap"

    @pytest.mark.asyncio
    async def test_events(self, registry):
        p = Provider(name="agent", capabilities=["cap1"])
        await registry.register_provider(p)

        events = registry.get_events()
        assert len(events) >= 1

        provider_events = registry.get_events("provider_registered")
        assert len(provider_events) == 1

    @pytest.mark.asyncio
    async def test_shutdown(self, registry):
        p = Provider(name="agent", capabilities=["cap1"])
        await registry.register_provider(p)
        await registry.shutdown()

        providers = await registry.list_providers()
        assert len(providers) == 0

    @pytest.mark.asyncio
    async def test_summary(self, registry):
        p1 = Provider(name="a", capabilities=["c1"])
        p2 = Provider(name="b", capabilities=["c2"])
        await registry.register_provider(p1)
        await registry.register_provider(p2)

        summary = registry.get_summary()
        assert summary["total_providers"] == 2
        assert summary["total_capabilities"] == 2

    @pytest.mark.asyncio
    async def test_to_dict(self, registry):
        p = Provider(name="agent", capabilities=["cap1"])
        await registry.register_provider(p)

        d = registry.to_dict()
        assert "providers" in d
        assert "capabilities" in d
        assert "summary" in d

    @pytest.mark.asyncio
    async def test_providers_for_capability(self, registry):
        p1 = Provider(name="a", capabilities=["cap1", "cap2"])
        p2 = Provider(name="b", capabilities=["cap2", "cap3"])
        await registry.register_provider(p1)
        await registry.register_provider(p2)

        providers = await registry.list_providers(capability="cap2")
        assert len(providers) == 2

        providers = await registry.list_providers(capability="cap1")
        assert len(providers) == 1
