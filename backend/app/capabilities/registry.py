"""ARKON Capability Registry - Main Registry.

Central orchestrator for capability discovery and provider management.
Registers with the Kernel as a service.
"""

from __future__ import annotations

import time
from typing import Any

import structlog

from app.capabilities.interfaces import (
    ICapabilityRegistry,
    ICapability,
    IProvider,
    ProviderHealth,
    RankingStrategy,
)
from app.capabilities.exceptions import (
    ProviderNotFoundError,
    ProviderAlreadyExistsError,
    CapabilityNotFoundError,
    NoProviderAvailableError,
)
from app.capabilities.capability import Capability
from app.capabilities.provider import Provider
from app.capabilities.resolver import CapabilityResolver
from app.capabilities.health import HealthTracker
from app.capabilities.events import (
    CapabilityRegistered,
    CapabilityRemoved,
    ProviderRegistered,
    ProviderRemoved,
    ProviderHealthChanged,
    CapabilityResolved,
)

logger = structlog.get_logger(__name__)


class CapabilityRegistry(ICapabilityRegistry):
    """Main capability registry.

    Orchestrates:
    - Provider registration/unregistration
    - Capability discovery
    - Provider resolution with matching and ranking
    - Health monitoring
    - Event emission
    """

    def __init__(self) -> None:
        self._providers: dict[str, IProvider] = {}
        self._capabilities: dict[str, Capability] = {}
        self._resolver = CapabilityResolver()
        self._health = HealthTracker()
        self._events: list[Any] = []
        self._running = False

    # -------------------------------------------------------------------------
    # Provider Management
    # -------------------------------------------------------------------------

    async def register_provider(self, provider: IProvider) -> None:
        """Register a capability provider."""
        provider_id = provider.get_id()

        if provider_id in self._providers:
            raise ProviderAlreadyExistsError(provider_id)

        self._providers[provider_id] = provider

        # Auto-register capabilities
        for cap_name in provider.get_capabilities():
            if cap_name not in self._capabilities:
                self._capabilities[cap_name] = Capability(
                    name=cap_name,
                    description=f"Auto-registered capability: {cap_name}",
                )
                event = CapabilityRegistered(capability_name=cap_name)
                self._events.append(event)

        # Track health
        self._health.set_health(provider_id, provider.get_health())

        event = ProviderRegistered(
            provider_id=provider_id,
            provider_name=provider.get_name(),
            capabilities=provider.get_capabilities(),
            provider_type=provider.get_type().value,
            priority=provider.get_priority(),
        )
        self._events.append(event)

        logger.info(
            "provider_registered",
            provider_id=provider_id,
            name=provider.get_name(),
            capabilities=provider.get_capabilities(),
        )

    async def unregister_provider(self, provider_id: str) -> None:
        """Unregister a capability provider."""
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderNotFoundError(provider_id)

        del self._providers[provider_id]
        self._health.remove(provider_id)

        event = ProviderRemoved(
            provider_id=provider_id,
            provider_name=provider.get_name(),
            capabilities=provider.get_capabilities(),
        )
        self._events.append(event)

        logger.info(
            "provider_unregistered",
            provider_id=provider_id,
            name=provider.get_name(),
        )

    async def get_provider(self, provider_id: str) -> IProvider | None:
        """Get a provider by ID."""
        return self._providers.get(provider_id)

    async def list_providers(self, capability: str | None = None) -> list[IProvider]:
        """List all providers, optionally filtered by capability."""
        if capability is None:
            return list(self._providers.values())
        return [
            p for p in self._providers.values()
            if capability in p.get_capabilities()
        ]

    # -------------------------------------------------------------------------
    # Capability Management
    # -------------------------------------------------------------------------

    async def register_capability(self, capability: Capability) -> None:
        """Register a capability definition."""
        name = capability.get_name()
        if name not in self._capabilities:
            self._capabilities[name] = capability
            event = CapabilityRegistered(
                capability_name=name,
                description=capability.get_description(),
                category=capability.get_category(),
                tags=capability.get_tags(),
            )
            self._events.append(event)

    async def list_capabilities(self) -> list[str]:
        """List all registered capability names."""
        return list(self._capabilities.keys())

    async def get_capability_info(self, name: str) -> ICapability | None:
        """Get capability definition."""
        return self._capabilities.get(name)

    # -------------------------------------------------------------------------
    # Resolution
    # -------------------------------------------------------------------------

    async def resolve(
        self,
        capability: str,
        tags: list[str] | None = None,
        workspace_id: str | None = None,
        required_resources: dict[str, Any] | None = None,
        max_priority: int | None = None,
        max_cost: float | None = None,
        max_latency: float | None = None,
        require_healthy: bool = True,
        ranking_strategy: RankingStrategy = RankingStrategy.WEIGHTED_COMPOSITE,
        ranking_weights: dict[str, float] | None = None,
    ) -> list[IProvider]:
        """Resolve providers for a capability.

        Args:
            capability: Capability name.
            tags: Required tags.
            workspace_id: Workspace scope.
            required_resources: Required resources.
            max_priority: Maximum priority.
            max_cost: Maximum cost.
            max_latency: Maximum latency.
            require_healthy: Only healthy providers.
            ranking_strategy: Ranking strategy.
            ranking_weights: Custom weights.

        Returns:
            Ranked list of matching providers.

        Raises:
            NoProviderAvailableError: If no providers match.
        """
        all_providers = list(self._providers.values())

        results = self._resolver.resolve(
            providers=all_providers,
            capability=capability,
            tags=tags,
            workspace_id=workspace_id,
            required_resources=required_resources,
            max_priority=max_priority,
            max_cost=max_cost,
            max_latency=max_latency,
            require_healthy=require_healthy,
            ranking_strategy=ranking_strategy,
            ranking_weights=ranking_weights,
        )

        if not results:
            filters = {}
            if tags:
                filters["tags"] = tags
            if workspace_id:
                filters["workspace_id"] = workspace_id
            raise NoProviderAvailableError(capability, filters=filters)

        event = CapabilityResolved(
            capability=capability,
            provider_count=len(results),
            provider_ids=[p.get_id() for p in results],
            filters={
                "tags": tags,
                "workspace_id": workspace_id,
                "require_healthy": require_healthy,
            },
            ranking_strategy=ranking_strategy.value,
        )
        self._events.append(event)

        return results

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def update_provider_health(
        self, provider_id: str, health: ProviderHealth
    ) -> None:
        """Update provider health status."""
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderNotFoundError(provider_id)

        old_health = self._health.get_health(provider_id)
        changed = self._health.set_health(provider_id, health)

        if changed is not None:
            # Update provider's internal health
            if isinstance(provider, Provider):
                provider.health = health
                provider.last_health_check = time.time()

            event = ProviderHealthChanged(
                provider_id=provider_id,
                provider_name=provider.get_name(),
                old_health=old_health.value,
                new_health=health.value,
            )
            self._events.append(event)

            logger.info(
                "provider_health_changed",
                provider_id=provider_id,
                old=old_health.value,
                new=health.value,
            )

    def get_provider_health(self, provider_id: str) -> ProviderHealth:
        """Get provider health from tracker."""
        return self._health.get_health(provider_id)

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------

    def get_events(self, event_type: str | None = None) -> list[Any]:
        """Get events, optionally filtered by type."""
        if event_type is None:
            return list(self._events)
        return [e for e in self._events if e.event_type == event_type]

    def clear_events(self) -> None:
        """Clear event history."""
        self._events.clear()

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Gracefully shut down the registry."""
        logger.info("registry_shutting_down")
        self._running = False
        self._providers.clear()
        self._capabilities.clear()
        self._health.clear()
        logger.info("registry_shutdown_complete")

    def get_summary(self) -> dict[str, Any]:
        """Get registry summary."""
        return {
            "total_providers": len(self._providers),
            "total_capabilities": len(self._capabilities),
            "health_summary": self._health.get_summary(),
            "capabilities": list(self._capabilities.keys()),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "providers": {pid: p.to_dict() for pid, p in self._providers.items()},
            "capabilities": {name: c.to_dict() for name, c in self._capabilities.items()},
            "summary": self.get_summary(),
        }
