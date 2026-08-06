"""Tests for AI provider classes."""

import pytest

from app.ai.interfaces import ProviderConfig, ProviderType
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.gemini_cli import GeminiCLIProvider
from app.ai.providers.github_copilot import GitHubCopilotProvider
from app.ai.providers.nvidia_nim import NVIDIANIMProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.providers.opencode import OpenCodeProvider


@pytest.fixture
def openrouter_config():
    return ProviderConfig(
        provider_id="openrouter",
        provider_type=ProviderType.CLOUD,
        display_name="OpenRouter",
        api_key="test-key",
    )


@pytest.fixture
def gemini_config():
    return ProviderConfig(
        provider_id="gemini",
        provider_type=ProviderType.CLOUD,
        display_name="Gemini",
        api_key="test-key",
    )


@pytest.fixture
def nvidia_config():
    return ProviderConfig(
        provider_id="nvidia_nim",
        provider_type=ProviderType.CLOUD,
        display_name="NVIDIA NIM",
        api_key="test-key",
    )


@pytest.fixture
def ollama_config():
    return ProviderConfig(
        provider_id="ollama",
        provider_type=ProviderType.LOCAL,
        display_name="Ollama",
    )


@pytest.fixture
def copilot_config():
    return ProviderConfig(
        provider_id="github_copilot",
        provider_type=ProviderType.ADAPTER,
        display_name="GitHub Copilot",
        api_key="test-token",
    )


@pytest.fixture
def gemini_cli_config():
    return ProviderConfig(
        provider_id="gemini_cli",
        provider_type=ProviderType.ADAPTER,
        display_name="Gemini CLI",
    )


@pytest.fixture
def opencode_config():
    return ProviderConfig(
        provider_id="opencode",
        provider_type=ProviderType.ADAPTER,
        display_name="OpenCode",
    )


# ── Instantiation ────────────────────────────────────────────────────────────

class TestProviderInstantiation:
    def test_openrouter(self, openrouter_config):
        p = OpenRouterProvider(openrouter_config)
        assert p is not None

    def test_gemini(self, gemini_config):
        p = GeminiProvider(gemini_config)
        assert p is not None

    def test_nvidia_nim(self, nvidia_config):
        p = NVIDIANIMProvider(nvidia_config)
        assert p is not None

    def test_ollama(self, ollama_config):
        p = OllamaProvider(ollama_config)
        assert p is not None

    def test_copilot(self, copilot_config):
        p = GitHubCopilotProvider(copilot_config)
        assert p is not None

    def test_gemini_cli(self, gemini_cli_config):
        p = GeminiCLIProvider(gemini_cli_config)
        assert p is not None

    def test_opencode(self, opencode_config):
        p = OpenCodeProvider(opencode_config)
        assert p is not None


# ── Authentication ───────────────────────────────────────────────────────────

class TestProviderAuth:
    @pytest.mark.asyncio
    async def test_ollama_auth(self, ollama_config):
        p = OllamaProvider(ollama_config)
        result = await p.authenticate()
        assert result is True

    @pytest.mark.asyncio
    async def test_opencode_auth(self, opencode_config):
        p = OpenCodeProvider(opencode_config)
        result = await p.authenticate()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_gemini_cli_auth(self, gemini_cli_config):
        p = GeminiCLIProvider(gemini_cli_config)
        result = await p.authenticate()
        assert isinstance(result, bool)


# ── List Models ──────────────────────────────────────────────────────────────

class TestProviderModels:
    @pytest.mark.asyncio
    async def test_ollama_list_models(self, ollama_config):
        p = OllamaProvider(ollama_config)
        models = await p.list_models()
        assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_gemini_cli_list_models(self, gemini_cli_config):
        p = GeminiCLIProvider(gemini_cli_config)
        models = await p.list_models()
        assert len(models) >= 1
        assert models[0].provider_id == "gemini_cli"

    @pytest.mark.asyncio
    async def test_opencode_list_models(self, opencode_config):
        p = OpenCodeProvider(opencode_config)
        models = await p.list_models()
        assert len(models) >= 1
        assert models[0].provider_id == "opencode"

    @pytest.mark.asyncio
    async def test_copilot_list_models(self, copilot_config):
        p = GitHubCopilotProvider(copilot_config)
        models = await p.list_models()
        assert len(models) >= 1


# ── Health ───────────────────────────────────────────────────────────────────

class TestProviderHealth:
    @pytest.mark.asyncio
    async def test_ollama_health(self, ollama_config):
        p = OllamaProvider(ollama_config)
        health = await p.health()
        assert health.provider_id == "ollama"
        assert health.status in ("available", "error")

    @pytest.mark.asyncio
    async def test_gemini_cli_health(self, gemini_cli_config):
        p = GeminiCLIProvider(gemini_cli_config)
        health = await p.health()
        assert health.provider_id == "gemini_cli"

    @pytest.mark.asyncio
    async def test_opencode_health(self, opencode_config):
        p = OpenCodeProvider(opencode_config)
        health = await p.health()
        assert health.provider_id == "opencode"


# ── Lazy Import ──────────────────────────────────────────────────────────────

class TestLazyImport:
    def test_import_providers_package(self):
        from app.ai.providers import (
            GeminiProvider, GeminiCLIProvider, GitHubCopilotProvider,
            NVIDIANIMProvider, OllamaProvider, OpenRouterProvider, OpenCodeProvider,
        )
        assert all([
            GeminiProvider, GeminiCLIProvider, GitHubCopilotProvider,
            NVIDIANIMProvider, OllamaProvider, OpenRouterProvider, OpenCodeProvider,
        ])
