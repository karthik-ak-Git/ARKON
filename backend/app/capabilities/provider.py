"""ARKON Capability Registry - Provider Model.

Defines the Provider data structure.
A provider is a component that implements one or more capabilities.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.capabilities.interfaces import IProvider, ProviderHealth, ProviderType


@dataclass
class Provider(IProvider):
    """A component that implements one or more capabilities.

    Providers may be: Agents, Plugins, Built-in Services,
    External APIs, Local Models, Remote Models.
    """

    name: str
    version: str = "1.0.0"
    provider_type: ProviderType = ProviderType.BUILTIN
    capabilities: list[str] = field(default_factory=list)
    priority: int = 0
    cost: float = 0.0
    latency: float = 0.0
    health: ProviderHealth = ProviderHealth.UNKNOWN
    available: bool = True
    required_resources: dict[str, Any] = field(default_factory=dict)
    workspace_scope: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    provider_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    registered_at: float = field(default_factory=time.time)
    last_health_check: float | None = None

    def get_id(self) -> str:
        return self.provider_id

    def get_name(self) -> str:
        return self.name

    def get_version(self) -> str:
        return self.version

    def get_type(self) -> ProviderType:
        return self.provider_type

    def get_capabilities(self) -> list[str]:
        return self.capabilities.copy()

    def get_priority(self) -> int:
        return self.priority

    def get_cost(self) -> float:
        return self.cost

    def get_latency(self) -> float:
        return self.latency

    def get_health(self) -> ProviderHealth:
        return self.health

    def is_available(self) -> bool:
        return self.available and self.health != ProviderHealth.UNAVAILABLE

    def get_required_resources(self) -> dict[str, Any]:
        return self.required_resources.copy()

    def get_workspace_scope(self) -> str | None:
        return self.workspace_scope

    def get_tags(self) -> list[str]:
        return self.tags.copy()

    def get_metadata(self) -> dict[str, Any]:
        return self.metadata.copy()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "version": self.version,
            "provider_type": self.provider_type.value,
            "capabilities": self.capabilities,
            "priority": self.priority,
            "cost": self.cost,
            "latency": self.latency,
            "health": self.health.value,
            "available": self.available,
            "required_resources": self.required_resources,
            "workspace_scope": self.workspace_scope,
            "tags": self.tags,
            "metadata": self.metadata,
            "registered_at": self.registered_at,
            "last_health_check": self.last_health_check,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Provider:
        return cls(
            provider_id=data.get("provider_id", uuid.uuid4().hex[:16]),
            name=data["name"],
            version=data.get("version", "1.0.0"),
            provider_type=ProviderType(data.get("provider_type", "builtin")),
            capabilities=data.get("capabilities", []),
            priority=data.get("priority", 0),
            cost=data.get("cost", 0.0),
            latency=data.get("latency", 0.0),
            health=ProviderHealth(data.get("health", "unknown")),
            available=data.get("available", True),
            required_resources=data.get("required_resources", {}),
            workspace_scope=data.get("workspace_scope"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            registered_at=data.get("registered_at", time.time()),
            last_health_check=data.get("last_health_check"),
        )
