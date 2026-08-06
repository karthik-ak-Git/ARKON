"""Provider Manager — manages provider instances, configs, enable/disable, local detection."""

from __future__ import annotations

import asyncio
from typing import Any

from app.ai.exceptions import ProviderNotFoundError, ProviderDisabledError
from app.ai.interfaces import (
    AIProviderBase, AIProviderProtocol, ProviderConfig, ProviderHealth,
    ProviderStatus, ProviderType,
)

# Map of provider type strings to their classes
_PROVIDER_CLASSES: dict[str, type[AIProviderBase]] = {}


def _lazy_import() -> None:
    if _PROVIDER_CLASSES:
        return
    from app.ai.providers.gemini import GeminiProvider
    from app.ai.providers.gemini_cli import GeminiCLIProvider
    from app.ai.providers.github_copilot import GitHubCopilotProvider
    from app.ai.providers.nvidia_nim import NVIDIANIMProvider
    from app.ai.providers.ollama import OllamaProvider
    from app.ai.providers.openrouter import OpenRouterProvider
    from app.ai.providers.opencode import OpenCodeProvider

    _PROVIDER_CLASSES.update({
        "openrouter": OpenRouterProvider,
        "gemini": GeminiProvider,
        "nvidia_nim": NVIDIANIMProvider,
        "ollama": OllamaProvider,
        "github_copilot": GitHubCopilotProvider,
        "gemini_cli": GeminiCLIProvider,
        "opencode": OpenCodeProvider,
    })


class ProviderManager:
    """Manages AI provider registration, enable/disable, config, auth, and local detection."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProviderBase] = {}
        self._configs: dict[str, ProviderConfig] = {}
        self._enabled: dict[str, bool] = {}

    def register(self, config: ProviderConfig) -> AIProviderBase:
        """Register a provider with its config."""
        _lazy_import()
        provider_id = config.provider_id
        self._configs[provider_id] = config
        self._enabled[provider_id] = config.enabled

        # Look up by provider_id first (for string-based config.provider_type)
        provider_class = _PROVIDER_CLASSES.get(provider_id)
        # Then try provider_type string value
        if not provider_class:
            if isinstance(config.provider_type, ProviderType):
                provider_class = _PROVIDER_CLASSES.get(config.provider_type.value)
            else:
                provider_class = _PROVIDER_CLASSES.get(config.provider_type)

        if provider_class is None:
            raise ValueError(f"Unknown provider type: {config.provider_type}")

        provider = provider_class(config)
        self._providers[provider_id] = provider
        return provider

    def unregister(self, provider_id: str) -> None:
        """Remove a provider."""
        self._providers.pop(provider_id, None)
        self._configs.pop(provider_id, None)
        self._enabled.pop(provider_id, None)

    def get(self, provider_id: str) -> AIProviderBase:
        """Get a provider by ID, raises if not found or disabled."""
        if provider_id not in self._providers:
            raise ProviderNotFoundError(f"Provider '{provider_id}' not found")
        if not self._enabled.get(provider_id, False):
            raise ProviderDisabledError(f"Provider '{provider_id}' is disabled")
        return self._providers[provider_id]

    def get_or_none(self, provider_id: str) -> AIProviderBase | None:
        """Get a provider by ID or None."""
        return self._providers.get(provider_id)

    def enable(self, provider_id: str) -> None:
        """Enable a provider."""
        if provider_id not in self._providers:
            raise ProviderNotFoundError(f"Provider '{provider_id}' not found")
        self._enabled[provider_id] = True

    def disable(self, provider_id: str) -> None:
        """Disable a provider."""
        if provider_id not in self._providers:
            raise ProviderNotFoundError(f"Provider '{provider_id}' not found")
        self._enabled[provider_id] = False

    def is_enabled(self, provider_id: str) -> bool:
        return self._enabled.get(provider_id, False)

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def list_enabled(self) -> list[str]:
        return [pid for pid, enabled in self._enabled.items() if enabled]

    def list_disabled(self) -> list[str]:
        return [pid for pid, enabled in self._enabled.items() if not enabled]

    def get_config(self, provider_id: str) -> ProviderConfig:
        if provider_id not in self._configs:
            raise ProviderNotFoundError(f"Provider '{provider_id}' not found")
        return self._configs[provider_id]

    async def check_health(self, provider_id: str) -> ProviderHealth:
        """Check health of a specific provider."""
        provider = self.get(provider_id)
        return await provider.health()

    async def check_all_health(self) -> dict[str, ProviderHealth]:
        """Check health of all enabled providers."""
        results: dict[str, ProviderHealth] = {}
        for pid in self.list_enabled():
            try:
                provider = self._providers[pid]
                results[pid] = await provider.health()
            except Exception as exc:
                results[pid] = ProviderHealth(
                    provider_id=pid,
                    status=ProviderStatus.ERROR,
                    last_check=0,
                    error=str(exc),
                )
        return results

    async def detect_local_providers(self) -> list[str]:
        """Auto-detect available local providers."""
        detected: list[str] = []
        local_types = {"ollama", "gemini_cli", "opencode"}

        for pid, config in self._configs.items():
            if config.provider_type.value not in local_types:
                continue
            try:
                provider = self._providers[pid]
                health = await provider.health()
                if health.status == ProviderStatus.AVAILABLE:
                    detected.append(pid)
            except Exception:
                continue
        return detected

    def update_config(self, provider_id: str, **kwargs: Any) -> AIProviderBase:
        """Update a provider's config and re-instantiate it."""
        if provider_id not in self._configs:
            raise ProviderNotFoundError(f"Provider '{provider_id}' not found")

        old_config = self._configs[provider_id]
        new_config = ProviderConfig(
            provider_id=provider_id,
            provider_type=old_config.provider_type,
            display_name=old_config.display_name,
            api_key=kwargs.get("api_key", old_config.api_key),
            base_url=kwargs.get("base_url", old_config.base_url),
            default_model=kwargs.get("default_model", old_config.default_model),
            timeout=kwargs.get("timeout", old_config.timeout),
            enabled=kwargs.get("enabled", old_config.enabled),
        )

        # Unregister old, register new
        self.unregister(provider_id)
        return self.register(new_config)
