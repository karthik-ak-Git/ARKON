"""ARKON Capability Registry - Events.

All capability registry event types.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RegistryEvent:
    """Base registry event."""
    timestamp: float = field(default_factory=time.time)
    event_type: str = ""


@dataclass
class CapabilityRegistered(RegistryEvent):
    """A new capability was registered."""
    event_type: str = "capability_registered"
    capability_name: str = ""
    description: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class CapabilityRemoved(RegistryEvent):
    """A capability was removed."""
    event_type: str = "capability_removed"
    capability_name: str = ""


@dataclass
class ProviderRegistered(RegistryEvent):
    """A new provider was registered."""
    event_type: str = "provider_registered"
    provider_id: str = ""
    provider_name: str = ""
    capabilities: list[str] = field(default_factory=list)
    provider_type: str = ""
    priority: int = 0


@dataclass
class ProviderRemoved(RegistryEvent):
    """A provider was removed."""
    event_type: str = "provider_removed"
    provider_id: str = ""
    provider_name: str = ""
    capabilities: list[str] = field(default_factory=list)


@dataclass
class ProviderHealthChanged(RegistryEvent):
    """Provider health status changed."""
    event_type: str = "provider_health_changed"
    provider_id: str = ""
    provider_name: str = ""
    old_health: str = ""
    new_health: str = ""


@dataclass
class CapabilityResolved(RegistryEvent):
    """A capability was resolved to providers."""
    event_type: str = "capability_resolved"
    capability: str = ""
    provider_count: int = 0
    provider_ids: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    ranking_strategy: str = ""


# Event type registry
CAPABILITY_EVENT_TYPES: dict[str, type[RegistryEvent]] = {
    "capability_registered": CapabilityRegistered,
    "capability_removed": CapabilityRemoved,
    "provider_registered": ProviderRegistered,
    "provider_removed": ProviderRemoved,
    "provider_health_changed": ProviderHealthChanged,
    "capability_resolved": CapabilityResolved,
}
