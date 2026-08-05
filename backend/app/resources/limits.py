"""ARKON Resource Manager - Limits.

Defines resource limit and quota structures.
Limits prevent over-consumption of resources.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.resources.interfaces import LimitScope, LimitType, ResourceType


@dataclass
class ResourceLimit:
    """A resource limit for a specific scope.

    Can be HARD (cannot exceed) or SOFT (can exceed with warning).
    """

    scope: LimitScope
    scope_id: str
    resource_type: ResourceType
    limit: float
    limit_type: LimitType = LimitType.HARD
    used: float = 0.0
    limit_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> float:
        """Remaining capacity within this limit."""
        return max(0.0, self.limit - self.used)

    @property
    def utilization(self) -> float:
        """Utilization as a fraction (0.0 to 1.0+)."""
        if self.limit <= 0:
            return 0.0
        return self.used / self.limit

    @property
    def is_exceeded(self) -> bool:
        """Check if limit is exceeded."""
        return self.used > self.limit

    @property
    def is_soft_exceeded(self) -> bool:
        """Check if soft limit is exceeded (allows overage)."""
        return self.limit_type == LimitType.SOFT and self.is_exceeded

    def can_allocate(self, amount: float) -> bool:
        """Check if an allocation of `amount` would stay within the limit."""
        if self.limit_type == LimitType.HARD:
            return (self.used + amount) <= self.limit
        return True  # Soft limits always allow

    def allocate(self, amount: float) -> None:
        """Record an allocation against this limit."""
        self.used += amount

    def release(self, amount: float) -> None:
        """Record a release against this limit."""
        self.used = max(0.0, self.used - amount)

    def reset(self) -> None:
        """Reset usage to zero."""
        self.used = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "limit_id": self.limit_id,
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "resource_type": self.resource_type.value,
            "limit": self.limit,
            "limit_type": self.limit_type.value,
            "used": self.used,
            "available": self.available,
            "utilization": self.utilization,
            "is_exceeded": self.is_exceeded,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceLimit:
        return cls(
            limit_id=data.get("limit_id", uuid.uuid4().hex[:16]),
            scope=LimitScope(data.get("scope", "global")),
            scope_id=data.get("scope_id", ""),
            resource_type=ResourceType(data.get("resource_type", "cpu")),
            limit=data.get("limit", 0.0),
            limit_type=LimitType(data.get("limit_type", "hard")),
            used=data.get("used", 0.0),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ResourceQuota:
    """Aggregate quota tracking across scopes.

    Tracks total usage against a global or per-scope quota.
    """

    scope: LimitScope
    scope_id: str
    resource_type: ResourceType
    quota: float
    used: float = 0.0
    quota_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    created_at: float = field(default_factory=time.time)
    reset_interval: float | None = None  # seconds between resets
    last_reset: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> float:
        """Remaining quota."""
        return max(0.0, self.quota - self.used)

    @property
    def utilization(self) -> float:
        """Quota utilization as a fraction."""
        if self.quota <= 0:
            return 0.0
        return self.used / self.quota

    @property
    def is_exceeded(self) -> bool:
        """Check if quota is exceeded."""
        return self.used > self.quota

    def consume(self, amount: float) -> None:
        """Consume quota."""
        self.used += amount

    def reset_if_needed(self) -> bool:
        """Reset if interval has elapsed. Returns True if reset."""
        if self.reset_interval is None:
            return False
        now = time.time()
        if (now - self.last_reset) >= self.reset_interval:
            self.used = 0.0
            self.last_reset = now
            return True
        return False

    def reset(self) -> None:
        """Manually reset quota."""
        self.used = 0.0
        self.last_reset = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "quota_id": self.quota_id,
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "resource_type": self.resource_type.value,
            "quota": self.quota,
            "used": self.used,
            "available": self.available,
            "utilization": self.utilization,
            "is_exceeded": self.is_exceeded,
            "reset_interval": self.reset_interval,
            "last_reset": self.last_reset,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceQuota:
        return cls(
            quota_id=data.get("quota_id", uuid.uuid4().hex[:16]),
            scope=LimitScope(data.get("scope", "global")),
            scope_id=data.get("scope_id", ""),
            resource_type=ResourceType(data.get("resource_type", "cpu")),
            quota=data.get("quota", 0.0),
            used=data.get("used", 0.0),
            created_at=data.get("created_at", time.time()),
            reset_interval=data.get("reset_interval"),
            last_reset=data.get("last_reset", time.time()),
            metadata=data.get("metadata", {}),
        )
