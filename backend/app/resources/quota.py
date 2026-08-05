"""ARKON Resource Manager - Quota.

Quota management for resource consumption tracking.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.resources.interfaces import LimitScope, ResourceType
from app.resources.limits import ResourceQuota
from app.resources.exceptions import QuotaExceededError

logger = structlog.get_logger(__name__)


class QuotaManager:
    """Manages resource quotas across scopes.

    Quotas track aggregate consumption against limits.
    Unlike limits (which are per-allocation), quotas track total usage.
    """

    def __init__(self) -> None:
        self._quotas: dict[str, ResourceQuota] = {}

    def _key(self, scope: LimitScope, scope_id: str, resource_type: ResourceType) -> str:
        """Generate a unique key for a quota."""
        return f"{scope.value}:{scope_id}:{resource_type.value}"

    def register(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        quota: float,
        reset_interval: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResourceQuota:
        """Register a new quota."""
        key = self._key(scope, scope_id, resource_type)
        q = ResourceQuota(
            scope=scope,
            scope_id=scope_id,
            resource_type=resource_type,
            quota=quota,
            reset_interval=reset_interval,
            metadata=metadata or {},
        )
        self._quotas[key] = q
        logger.debug("quota_registered", key=key, quota=quota)
        return q

    def get(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
    ) -> ResourceQuota | None:
        """Get a quota."""
        key = self._key(scope, scope_id, resource_type)
        return self._quotas.get(key)

    def check(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        amount: float,
    ) -> bool:
        """Check if consuming `amount` would exceed the quota.

        Returns True if consumption is allowed.
        """
        q = self.get(scope, scope_id, resource_type)
        if q is None:
            return True  # No quota = unlimited
        q.reset_if_needed()
        return (q.used + amount) <= q.quota

    def consume(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        amount: float,
    ) -> None:
        """Consume quota. Raises if quota exceeded."""
        q = self.get(scope, scope_id, resource_type)
        if q is None:
            return  # No quota = unlimited

        q.reset_if_needed()

        if (q.used + amount) > q.quota:
            raise QuotaExceededError(
                scope=f"{scope.value}:{scope_id}",
                resource_type=resource_type.value,
                used=q.used + amount,
                limit=q.quota,
            )

        q.consume(amount)
        logger.debug(
            "quota_consumed",
            key=self._key(scope, scope_id, resource_type),
            amount=amount,
            used=q.used,
            quota=q.quota,
        )

    def release(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        amount: float,
    ) -> None:
        """Release consumed quota."""
        q = self.get(scope, scope_id, resource_type)
        if q is not None:
            q.used = max(0.0, q.used - amount)

    def reset(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
    ) -> None:
        """Reset a specific quota."""
        q = self.get(scope, scope_id, resource_type)
        if q is not None:
            q.reset()

    def list_all(self) -> list[ResourceQuota]:
        """List all quotas."""
        return list(self._quotas.values())

    def remove(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
    ) -> bool:
        """Remove a quota. Returns True if removed."""
        key = self._key(scope, scope_id, resource_type)
        if key in self._quotas:
            del self._quotas[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all quotas."""
        self._quotas.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            key: q.to_dict()
            for key, q in self._quotas.items()
        }
