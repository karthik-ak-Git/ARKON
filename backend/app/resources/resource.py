"""ARKON Resource Manager - Resource Model.

Defines the Resource data structure.
A resource is a computational unit that can be reserved, allocated, and released.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.resources.interfaces import (
    IResource,
    ResourceHealth,
    ResourceType,
    ResourceStatus,
)


@dataclass
class Resource(IResource):
    """A computational resource.

    Resources are discovered, tracked, reserved, allocated,
    and released by the Resource Manager.
    """

    name: str
    resource_type: ResourceType
    capacity: float = 1.0
    available: float | None = None
    reserved: float = 0.0
    allocated: float = 0.0
    health: ResourceHealth = ResourceHealth.UNKNOWN
    status: ResourceStatus = ResourceStatus.FREE
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    priority: int = 0
    resource_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    registered_at: float = field(default_factory=time.time)
    last_health_check: float | None = None

    def __post_init__(self) -> None:
        """Set available to capacity if not explicitly provided."""
        if self.available is None:
            self.available = self.capacity

    def get_id(self) -> str:
        return self.resource_id

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> ResourceType:
        return self.resource_type

    def get_capacity(self) -> float:
        return self.capacity

    def get_available(self) -> float:
        return self.available

    def get_reserved(self) -> float:
        return self.reserved

    def get_allocated(self) -> float:
        return self.allocated

    def get_health(self) -> ResourceHealth:
        return self.health

    def get_status(self) -> ResourceStatus:
        return self.status

    def get_metadata(self) -> dict[str, Any]:
        return self.metadata.copy()

    def get_tags(self) -> list[str]:
        return self.tags.copy()

    def get_priority(self) -> int:
        return self.priority

    @property
    def utilization(self) -> float:
        """Utilization as a fraction (0.0 to 1.0+)."""
        if self.capacity <= 0:
            return 0.0
        return (self.capacity - self.available) / self.capacity

    def update_status(self) -> None:
        """Recalculate status from current state."""
        if self.health in (ResourceHealth.UNAVAILABLE, ResourceHealth.MAINTENANCE):
            self.status = ResourceStatus.OFFLINE
        elif self.available <= 0:
            self.status = ResourceStatus.EXHAUSTED
        elif self.allocated > 0:
            self.status = ResourceStatus.ALLOCATED
        elif self.reserved > 0:
            self.status = ResourceStatus.RESERVED
        else:
            self.status = ResourceStatus.FREE

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "resource_type": self.resource_type.value,
            "capacity": self.capacity,
            "available": self.available,
            "reserved": self.reserved,
            "allocated": self.allocated,
            "health": self.health.value,
            "status": self.status.value,
            "metadata": self.metadata,
            "tags": self.tags,
            "priority": self.priority,
            "registered_at": self.registered_at,
            "last_health_check": self.last_health_check,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Resource:
        return cls(
            resource_id=data.get("resource_id", uuid.uuid4().hex[:16]),
            name=data["name"],
            resource_type=ResourceType(data.get("resource_type", "cpu")),
            capacity=data.get("capacity", 1.0),
            available=data.get("available"),
            reserved=data.get("reserved", 0.0),
            allocated=data.get("allocated", 0.0),
            health=ResourceHealth(data.get("health", "unknown")),
            status=ResourceStatus(data.get("status", "free")),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            priority=data.get("priority", 0),
            registered_at=data.get("registered_at", time.time()),
            last_health_check=data.get("last_health_check"),
        )
