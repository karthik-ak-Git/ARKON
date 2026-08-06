"""Smart Router — selects the best provider given a request and routing policy."""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from app.ai.exceptions import NoProviderAvailableError
from app.ai.interfaces import (
    AIProviderBase, ChatRequest, ChatResponse, ProviderHealth,
    ProviderStatus, ProviderType, RoutingPolicy, StreamEvent,
)

if TYPE_CHECKING:
    from app.ai.manager import ProviderManager

_LOCAL_PROVIDER_IDS = {"ollama", "gemini_cli", "opencode"}


class SmartRouter:
    """Routes AI requests to the best available provider based on a routing policy."""

    def __init__(self, manager: ProviderManager) -> None:
        self._manager = manager

    def _is_local(self, provider: AIProviderBase) -> bool:
        if provider.provider_id in _LOCAL_PROVIDER_IDS:
            return True
        if isinstance(provider.config.provider_type, ProviderType):
            return provider.config.provider_type == ProviderType.LOCAL
        return provider.config.provider_type == "local"

    async def select_provider(
        self,
        request: ChatRequest,
        policy: RoutingPolicy | None = None,
        preferred_provider: str | None = None,
    ) -> AIProviderBase:
        if policy is None:
            policy = RoutingPolicy.LOCAL_FIRST

        enabled_ids = self._manager.list_enabled()
        if not enabled_ids:
            raise NoProviderAvailableError("No enabled providers")

        if preferred_provider:
            if preferred_provider not in enabled_ids:
                raise NoProviderAvailableError(
                    f"Preferred provider '{preferred_provider}' not enabled"
                )
            return self._manager.get(preferred_provider)

        candidates = await self._filter_candidates(enabled_ids)
        if not candidates:
            raise NoProviderAvailableError("No providers match the request")

        return self._rank(candidates, policy)

    async def _filter_candidates(
        self,
        provider_ids: list[str],
    ) -> list[tuple[AIProviderBase, ProviderHealth]]:
        candidates: list[tuple[AIProviderBase, ProviderHealth]] = []

        for pid in provider_ids:
            try:
                provider = self._manager.get(pid)
                health = await provider.health()
                if health.status in (ProviderStatus.AVAILABLE, ProviderStatus.UNAUTHENTICATED):
                    candidates.append((provider, health))
            except Exception:
                continue
        return candidates

    def _rank(
        self,
        candidates: list[tuple[AIProviderBase, ProviderHealth]],
        policy: RoutingPolicy,
    ) -> AIProviderBase:
        if policy == RoutingPolicy.LOCAL_FIRST:
            return self._rank_local_first(candidates)
        elif policy == RoutingPolicy.CLOUD_FIRST:
            return self._rank_cloud_first(candidates)
        elif policy == RoutingPolicy.CHEAPEST:
            return self._rank_cheapest(candidates)
        elif policy == RoutingPolicy.FASTEST:
            return self._rank_fastest(candidates)
        else:
            return candidates[0][0]

    def _rank_local_first(
        self,
        candidates: list[tuple[AIProviderBase, ProviderHealth]],
    ) -> AIProviderBase:
        local = [(p, h) for p, h in candidates if self._is_local(p)]
        if local:
            local.sort(key=lambda x: x[1].latency_ms or 9999)
            return local[0][0]
        if candidates:
            candidates.sort(key=lambda x: x[1].latency_ms or 9999)
            return candidates[0][0]
        raise NoProviderAvailableError("No providers available")

    def _rank_cloud_first(
        self,
        candidates: list[tuple[AIProviderBase, ProviderHealth]],
    ) -> AIProviderBase:
        cloud = [(p, h) for p, h in candidates if not self._is_local(p)]
        if cloud:
            cloud.sort(key=lambda x: x[1].latency_ms or 9999)
            return cloud[0][0]
        if candidates:
            candidates.sort(key=lambda x: x[1].latency_ms or 9999)
            return candidates[0][0]
        raise NoProviderAvailableError("No providers available")

    def _rank_cheapest(
        self,
        candidates: list[tuple[AIProviderBase, ProviderHealth]],
    ) -> AIProviderBase:
        # Prefer free models (local providers are always free)
        free = [(p, h) for p, h in candidates if self._is_local(p)]
        if free:
            free.sort(key=lambda x: x[1].latency_ms or 9999)
            return free[0][0]
        if candidates:
            candidates.sort(key=lambda x: x[1].latency_ms or 9999)
            return candidates[0][0]
        raise NoProviderAvailableError("No providers available")

    def _rank_fastest(
        self,
        candidates: list[tuple[AIProviderBase, ProviderHealth]],
    ) -> AIProviderBase:
        candidates.sort(key=lambda x: x[1].latency_ms or 9999)
        return candidates[0][0]

    async def route(
        self,
        request: ChatRequest,
        policy: RoutingPolicy | None = None,
    ) -> ChatResponse:
        provider = await self.select_provider(request, policy=policy)
        return await provider.chat(request)

    async def route_stream(
        self,
        request: ChatRequest,
        policy: RoutingPolicy | None = None,
    ) -> AsyncIterator[StreamEvent]:
        provider = await self.select_provider(request, policy=policy)
        async for event in provider.stream(request):
            yield event
