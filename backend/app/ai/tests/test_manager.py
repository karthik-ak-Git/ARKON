"""Tests for ProviderManager."""

import pytest

from app.ai.exceptions import ProviderNotFoundError, ProviderDisabledError
from app.ai.interfaces import ProviderConfig, ProviderStatus, ProviderType
from app.ai.manager import ProviderManager


@pytest.fixture
def manager():
    return ProviderManager()


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
def gemini_config():
    return ProviderConfig(
        provider_id="gemini",
        provider_type=ProviderType.CLOUD,
        display_name="Gemini",
        api_key="test-key",
        enabled=True,
    )


@pytest.fixture
def disabled_config():
    return ProviderConfig(
        provider_id="nvidia_nim",
        provider_type=ProviderType.CLOUD,
        display_name="NVIDIA NIM",
        api_key="test-key",
        enabled=False,
    )


# ── Registration ─────────────────────────────────────────────────────────────

class TestRegistration:
    def test_register_provider(self, manager, openrouter_config):
        p = manager.register(openrouter_config)
        assert p is not None
        assert "openrouter" in manager.list_providers()

    def test_unregister_provider(self, manager, openrouter_config):
        manager.register(openrouter_config)
        manager.unregister("openrouter")
        assert "openrouter" not in manager.list_providers()

    def test_register_unknown_type(self, manager):
        config = ProviderConfig(
            provider_id="unknown",
            provider_type="unknown_provider",  # type: ignore
            display_name="Unknown",
        )
        with pytest.raises(ValueError, match="Unknown provider type"):
            manager.register(config)

    def test_register_multiple(self, manager, openrouter_config, ollama_config):
        manager.register(openrouter_config)
        manager.register(ollama_config)
        assert len(manager.list_providers()) == 2


# ── Get / Find ───────────────────────────────────────────────────────────────

class TestGetProvider:
    def test_get_existing(self, manager, openrouter_config):
        manager.register(openrouter_config)
        p = manager.get("openrouter")
        assert p is not None

    def test_get_nonexistent(self, manager):
        with pytest.raises(ProviderNotFoundError):
            manager.get("nonexistent")

    def test_get_disabled(self, manager, disabled_config):
        manager.register(disabled_config)
        with pytest.raises(ProviderDisabledError):
            manager.get("nvidia_nim")

    def test_get_or_none(self, manager, openrouter_config):
        manager.register(openrouter_config)
        assert manager.get_or_none("openrouter") is not None
        assert manager.get_or_none("nonexistent") is None


# ── Enable / Disable ────────────────────────────────────────────────────────

class TestEnableDisable:
    def test_disable(self, manager, openrouter_config):
        manager.register(openrouter_config)
        manager.disable("openrouter")
        assert not manager.is_enabled("openrouter")

    def test_enable(self, manager, disabled_config):
        manager.register(disabled_config)
        assert not manager.is_enabled("nvidia_nim")
        manager.enable("nvidia_nim")
        assert manager.is_enabled("nvidia_nim")

    def test_disable_nonexistent(self, manager):
        with pytest.raises(ProviderNotFoundError):
            manager.disable("nonexistent")

    def test_enable_nonexistent(self, manager):
        with pytest.raises(ProviderNotFoundError):
            manager.enable("nonexistent")

    def test_list_enabled(self, manager, openrouter_config, disabled_config):
        manager.register(openrouter_config)
        manager.register(disabled_config)
        assert "openrouter" in manager.list_enabled()
        assert "nvidia_nim" in manager.list_disabled()


# ── Config ───────────────────────────────────────────────────────────────────

class TestConfig:
    def test_get_config(self, manager, openrouter_config):
        manager.register(openrouter_config)
        cfg = manager.get_config("openrouter")
        assert cfg.api_key == "test-key"

    def test_get_config_nonexistent(self, manager):
        with pytest.raises(ProviderNotFoundError):
            manager.get_config("nonexistent")

    def test_update_config(self, manager, openrouter_config):
        manager.register(openrouter_config)
        provider = manager.update_config("openrouter", api_key="new-key")
        cfg = manager.get_config("openrouter")
        assert cfg.api_key == "new-key"


# ── Health ───────────────────────────────────────────────────────────────────

class TestHealth:
    @pytest.mark.asyncio
    async def test_check_all_health_empty(self, manager):
        results = await manager.check_all_health()
        assert results == {}

    @pytest.mark.asyncio
    async def test_check_all_health(self, manager, ollama_config):
        manager.register(ollama_config)
        results = await manager.check_all_health()
        assert "ollama" in results

    @pytest.mark.asyncio
    async def test_check_health_disabled(self, manager, disabled_config):
        manager.register(disabled_config)
        with pytest.raises(ProviderDisabledError):
            await manager.check_health("nvidia_nim")


# ── Local Detection ──────────────────────────────────────────────────────────

class TestLocalDetection:
    @pytest.mark.asyncio
    async def test_detect_local_providers(self, manager):
        detected = await manager.detect_local_providers()
        assert detected == []

    @pytest.mark.asyncio
    async def test_detect_local_with_ollama(self, manager, ollama_config):
        manager.register(ollama_config)
        detected = await manager.detect_local_providers()
        assert isinstance(detected, list)
