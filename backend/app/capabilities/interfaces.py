"""ARKON Capability Registry - Interfaces.

Defines the contracts for all capability registry components.
The Capability Registry is the service discovery system.
It manages WHAT can perform work, not WHO performs it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


# =============================================================================
# Health States
# =============================================================================


class ProviderHealth(str, Enum):
    """Provider health states."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    UNHEALTHY = "unhealthy"


# =============================================================================
# Ranking Strategies
# =============================================================================


class RankingStrategy(str, Enum):
    """Provider ranking strategies."""

    HIGHEST_PRIORITY = "highest_priority"
    LOWEST_COST = "lowest_cost"
    FASTEST = "fastest"
    LOCAL_FIRST = "local_first"
    HEALTHY_FIRST = "healthy_first"
    WEIGHTED_COMPOSITE = "weighted_composite"


# =============================================================================
# Provider Type
# =============================================================================


class ProviderType(str, Enum):
    """Types of capability providers."""

    AGENT = "agent"
    PLUGIN = "plugin"
    BUILTIN = "builtin"
    EXTERNAL_API = "external_api"
    LOCAL_MODEL = "local_model"
    REMOTE_MODEL = "remote_model"


# =============================================================================
# ICapability
# =============================================================================


class ICapability(ABC):
    """Interface for a capability definition."""

    @abstractmethod
    def get_name(self) -> str:
        """Get capability name."""
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Get capability description."""
        ...

    @abstractmethod
    def get_category(self) -> str:
        """Get capability category."""
        ...

    @abstractmethod
    def get_tags(self) -> list[str]:
        """Get capability tags."""
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


# =============================================================================
# IProvider
# =============================================================================


class IProvider(ABC):
    """Interface for a capability provider."""

    @abstractmethod
    def get_id(self) -> str:
        """Get provider ID."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get provider name."""
        ...

    @abstractmethod
    def get_version(self) -> str:
        """Get provider version."""
        ...

    @abstractmethod
    def get_type(self) -> ProviderType:
        """Get provider type."""
        ...

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get list of capability names this provider implements."""
        ...

    @abstractmethod
    def get_priority(self) -> int:
        """Get provider priority (lower = higher priority)."""
        ...

    @abstractmethod
    def get_cost(self) -> float:
        """Get provider cost per invocation."""
        ...

    @abstractmethod
    def get_latency(self) -> float:
        """Get average latency in milliseconds."""
        ...

    @abstractmethod
    def get_health(self) -> ProviderHealth:
        """Get current health status."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is currently available."""
        ...

    @abstractmethod
    def get_required_resources(self) -> dict[str, Any]:
        """Get required resources (GPU, memory, etc.)."""
        ...

    @abstractmethod
    def get_workspace_scope(self) -> str | None:
        """Get workspace scope (None = global)."""
        ...

    @abstractmethod
    def get_tags(self) -> list[str]:
        """Get provider tags."""
        ...

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Get all provider metadata."""
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


# =============================================================================
# ICapabilityRegistry
# =============================================================================


class ICapabilityRegistry(ABC):
    """Interface for the capability registry.

    The registry is the service discovery system of ARKON.
    It allows the platform to discover WHAT can perform work
    rather than WHO performs it.
    """

    @abstractmethod
    async def register_provider(self, provider: IProvider) -> None:
        """Register a capability provider.

        Args:
            provider: Provider to register.
        """
        ...

    @abstractmethod
    async def unregister_provider(self, provider_id: str) -> None:
        """Unregister a capability provider.

        Args:
            provider_id: ID of provider to unregister.
        """
        ...

    @abstractmethod
    async def resolve(self, capability: str, **kwargs: Any) -> list[IProvider]:
        """Resolve providers for a capability.

        Args:
            capability: Capability name to resolve.
            **kwargs: Additional filters (tags, workspace, etc.).

        Returns:
            List of matching providers, ranked.
        """
        ...

    @abstractmethod
    async def get_provider(self, provider_id: str) -> IProvider | None:
        """Get a provider by ID.

        Args:
            provider_id: Provider ID.

        Returns:
            Provider or None.
        """
        ...

    @abstractmethod
    async def list_providers(self, capability: str | None = None) -> list[IProvider]:
        """List all providers, optionally filtered by capability.

        Args:
            capability: Optional capability filter.

        Returns:
            List of providers.
        """
        ...

    @abstractmethod
    async def list_capabilities(self) -> list[str]:
        """List all registered capability names.

        Returns:
            List of capability names.
        """
        ...

    @abstractmethod
    async def get_capability_info(self, name: str) -> ICapability | None:
        """Get capability definition.

        Args:
            name: Capability name.

        Returns:
            Capability definition or None.
        """
        ...

    @abstractmethod
    async def update_provider_health(
        self, provider_id: str, health: ProviderHealth
    ) -> None:
        """Update provider health status.

        Args:
            provider_id: Provider ID.
            health: New health status.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the registry."""
        ...
