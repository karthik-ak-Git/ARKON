"""ARKON Capability Registry - Exceptions.

All capability-registry-specific exceptions.
"""

from __future__ import annotations


class CapabilityRegistryError(Exception):
    """Base capability registry error."""
    pass


# Provider errors


class ProviderError(CapabilityRegistryError):
    """Base provider error."""
    pass


class ProviderNotFoundError(ProviderError):
    """Provider not found."""
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        super().__init__(f"Provider not found: '{provider_id}'")


class ProviderAlreadyExistsError(ProviderError):
    """Provider already registered."""
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        super().__init__(f"Provider already registered: '{provider_id}'")


class ProviderUnregisterError(ProviderError):
    """Failed to unregister provider."""
    def __init__(self, provider_id: str, reason: str = ""):
        self.provider_id = provider_id
        self.reason = reason
        super().__init__(f"Cannot unregister provider '{provider_id}': {reason}")


# Capability errors


class CapabilityError(CapabilityRegistryError):
    """Base capability error."""
    pass


class CapabilityNotFoundError(CapabilityError):
    """Capability not found."""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Capability not found: '{name}'")


class CapabilityAlreadyExistsError(CapabilityError):
    """Capability already registered."""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Capability already registered: '{name}'")


# Resolution errors


class ResolutionError(CapabilityRegistryError):
    """Base resolution error."""
    pass


class NoProviderAvailableError(ResolutionError):
    """No provider available for the requested capability."""
    def __init__(self, capability: str, filters: dict | None = None):
        self.capability = capability
        self.filters = filters or {}
        filter_str = ", ".join(f"{k}={v}" for k, v in self.filters.items())
        super().__init__(
            f"No provider available for capability '{capability}'"
            + (f" with filters: {filter_str}" if filter_str else "")
        )


class ResolutionTimeoutError(ResolutionError):
    """Resolution timed out."""
    def __init__(self, capability: str, timeout: float):
        self.capability = capability
        self.timeout = timeout
        super().__init__(
            f"Resolution timed out for '{capability}' after {timeout}s"
        )


# Health errors


class HealthError(CapabilityRegistryError):
    """Base health error."""
    pass


class HealthUpdateError(HealthError):
    """Failed to update health status."""
    def __init__(self, provider_id: str, reason: str = ""):
        self.provider_id = provider_id
        self.reason = reason
        super().__init__(f"Cannot update health for '{provider_id}': {reason}")


# Matching errors


class MatchError(CapabilityRegistryError):
    """Base matching error."""
    pass


class InvalidFilterError(MatchError):
    """Invalid filter criteria."""
    def __init__(self, filter_name: str, reason: str = ""):
        self.filter_name = filter_name
        self.reason = reason
        super().__init__(f"Invalid filter '{filter_name}': {reason}")


# Ranking errors


class RankingError(CapabilityRegistryError):
    """Base ranking error."""
    pass


class InvalidRankingStrategyError(RankingError):
    """Invalid ranking strategy."""
    def __init__(self, strategy: str):
        self.strategy = strategy
        super().__init__(f"Invalid ranking strategy: '{strategy}'")
