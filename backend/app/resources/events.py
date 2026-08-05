"""ARKON Resource Manager - Events.

All resource manager event types.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResourceEvent:
    """Base resource event."""
    timestamp: float = field(default_factory=time.time)
    event_type: str = ""


@dataclass
class ResourceDiscovered(ResourceEvent):
    """A resource was discovered."""
    event_type: str = "resource_discovered"
    resource_id: str = ""
    resource_name: str = ""
    resource_type: str = ""
    capacity: float = 0.0


@dataclass
class ResourceReserved(ResourceEvent):
    """Resources were reserved."""
    event_type: str = "resource_reserved"
    reservation_id: str = ""
    resource_id: str = ""
    amount: float = 0.0
    owner: str = ""
    ttl: float | None = None


@dataclass
class ResourceAllocated(ResourceEvent):
    """Resources were allocated."""
    event_type: str = "resource_allocated"
    reservation_id: str = ""
    resource_id: str = ""
    amount: float = 0.0
    owner: str = ""
    strategy: str = ""


@dataclass
class ResourceReleased(ResourceEvent):
    """Resources were released."""
    event_type: str = "resource_released"
    reservation_id: str = ""
    resource_id: str = ""
    amount: float = 0.0
    owner: str = ""


@dataclass
class ResourceExhausted(ResourceEvent):
    """A resource was exhausted."""
    event_type: str = "resource_exhausted"
    resource_id: str = ""
    resource_type: str = ""
    requested: float = 0.0
    available: float = 0.0


@dataclass
class ResourceRecovered(ResourceEvent):
    """A resource recovered from exhaustion/degradation."""
    event_type: str = "resource_recovered"
    resource_id: str = ""
    resource_type: str = ""
    previous_health: str = ""
    new_health: str = ""


@dataclass
class ResourceHealthChanged(ResourceEvent):
    """Resource health status changed."""
    event_type: str = "resource_health_changed"
    resource_id: str = ""
    resource_name: str = ""
    old_health: str = ""
    new_health: str = ""


@dataclass
class ReservationExpired(ResourceEvent):
    """A reservation expired."""
    event_type: str = "reservation_expired"
    reservation_id: str = ""
    resource_id: str = ""
    amount: float = 0.0
    owner: str = ""


@dataclass
class QuotaExceeded(ResourceEvent):
    """A quota was exceeded."""
    event_type: str = "quota_exceeded"
    scope: str = ""
    resource_type: str = ""
    used: float = 0.0
    limit: float = 0.0


# Event type registry
RESOURCE_EVENT_TYPES: dict[str, type[ResourceEvent]] = {
    "resource_discovered": ResourceDiscovered,
    "resource_reserved": ResourceReserved,
    "resource_allocated": ResourceAllocated,
    "resource_released": ResourceReleased,
    "resource_exhausted": ResourceExhausted,
    "resource_recovered": ResourceRecovered,
    "resource_health_changed": ResourceHealthChanged,
    "reservation_expired": ReservationExpired,
    "quota_exceeded": QuotaExceeded,
}
