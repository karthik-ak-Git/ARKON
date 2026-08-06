"""Tests for SmartRouter."""

import pytest
from unittest.mock import AsyncMock, patch

from app.ai.exceptions import NoProviderAvailableError
from app.ai.interfaces import (
    AIProviderBase, ChatMessage, ChatRequest, MessageRole, ProviderConfig,
    ProviderHealth, ProviderStatus, ProviderType, RoutingPolicy,
)
from app.ai.manager import ProviderManager
from app.ai.router import SmartRouter


@pytest.fixture
def manager():
    return ProviderManager()


@pytest.fixture
def router(manager):
    return SmartRouter(manager)


@pytest.fixture
def openrouter_config():
    return ProviderConfig(
        provider_id="openrouter",
        provider_type=ProviderType.CLOUD,
        display_name="OpenRouter",
        api_key="test-key",
        enabled=True,
    )


@pytest.fixture
def ollama_config():
    return ProviderConfig(
        provider_id="ollama",
        provider_type=ProviderType.LOCAL,
        display_name="Ollama",
        enabled=True,
    )


@pytest.fixture
def sample_request():
    return ChatRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="hello")],
    )


def _mock_provider(pid: str, ptype: ProviderType, available: bool = True):
    """Return a mock provider whose health() returns AVAILABLE or ERROR."""
    mock = AsyncMock(spec=AIProviderBase)
    mock.provider_id = pid
    mock.config = ProviderConfig(
        provider_id=pid,
        provider_type=ptype,
        display_name=pid,
    )
    status = ProviderStatus.AVAILABLE if available else ProviderStatus.ERROR
    mock.health.return_value = ProviderHealth(
        provider_id=pid,
        status=status,
        latency_ms=100.0,
    )
    return mock


# ── Selection ────────────────────────────────────────────────────────────────

class TestSelectProvider:
    @pytest.mark.asyncio
    async def test_select_with_no_providers(self, router, sample_request):
        with pytest.raises(NoProviderAvailableError):
            await router.select_provider(sample_request)

    @pytest.mark.asyncio
    async def test_select_preferred_provider(self, manager, router, openrouter_config):
        manager.register(openrouter_config)
        provider = await router.select_provider(
            sample_request,
            preferred_provider="openrouter",
        )
        assert provider.provider_id == "openrouter"

    @pytest.mark.asyncio
    async def test_select_preferred_not_found(self, manager, router, openrouter_config):
        manager.register(openrouter_config)
        with pytest.raises(NoProviderAvailableError):
            await router.select_provider(
                sample_request,
                preferred_provider="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_select_local_first(self, manager, router):
        local = _mock_provider("ollama", ProviderType.LOCAL)
        cloud = _mock_provider("openrouter", ProviderType.CLOUD)

        with patch.object(
            ProviderManager, "get", side_effect=lambda pid: local if pid == "ollama" else cloud
        ):
            with patch.object(
                ProviderManager, "list_enabled", return_value=["ollama", "openrouter"]
            ):
                provider = await router.select_provider(
                    sample_request,
                    policy=RoutingPolicy.LOCAL_FIRST,
                )
                assert provider.provider_id == "ollama"

    @pytest.mark.asyncio
    async def test_select_cloud_first(self, manager, router):
        local = _mock_provider("ollama", ProviderType.LOCAL)
        cloud = _mock_provider("openrouter", ProviderType.CLOUD)

        with patch.object(
            ProviderManager, "get", side_effect=lambda pid: local if pid == "ollama" else cloud
        ):
            with patch.object(
                ProviderManager, "list_enabled", return_value=["ollama", "openrouter"]
            ):
                provider = await router.select_provider(
                    sample_request,
                    policy=RoutingPolicy.CLOUD_FIRST,
                )
                assert provider.provider_id == "openrouter"

    @pytest.mark.asyncio
    async def test_select_cheapest(self, manager, router):
        local = _mock_provider("ollama", ProviderType.LOCAL)
        with patch.object(ProviderManager, "get", return_value=local):
            with patch.object(ProviderManager, "list_enabled", return_value=["ollama"]):
                provider = await router.select_provider(
                    sample_request,
                    policy=RoutingPolicy.CHEAPEST,
                )
                assert provider.provider_id == "ollama"

    @pytest.mark.asyncio
    async def test_select_fastest(self, manager, router, openrouter_config):
        manager.register(openrouter_config)
        provider = await router.select_provider(
            sample_request,
            policy=RoutingPolicy.FASTEST,
        )
        assert provider is not None


# ── Routing ──────────────────────────────────────────────────────────────────

class TestRoute:
    @pytest.mark.asyncio
    async def test_route_no_providers(self, router, sample_request):
        with pytest.raises(NoProviderAvailableError):
            await router.route(sample_request)

    @pytest.mark.asyncio
    async def test_route_stream_no_providers(self, router, sample_request):
        with pytest.raises(NoProviderAvailableError):
            async for _ in router.route_stream(sample_request):
                pass
