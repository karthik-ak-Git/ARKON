"""ARKON Resource Manager - Health.

Resource health tracking and history management.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.resources.interfaces import ResourceHealth
from app.resources.resource import Resource

logger = structlog.get_logger(__name__)


@dataclass
class HealthRecord:
    """A single health check record."""

    resource_id: str
    health: ResourceHealth
    timestamp: float = field(default_factory=time.time)
    details: dict[str, Any] = field(default_factory=dict)


class ResourceHealthTracker:
    """Tracks resource health over time.

    Maintains history of health changes and provides queries.
    """

    def __init__(self, max_history_per_resource: int = 100) -> None:
        self._history: dict[str, list[HealthRecord]] = {}
        self._max_history = max_history_per_resource

    def record_health(
        self,
        resource: Resource,
        new_health: ResourceHealth,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a health change for a resource."""
        rid = resource.resource_id
        old_health = resource.health

        # Update resource
        resource.health = new_health
        resource.last_health_check = time.time()
        resource.update_status()

        # Store record
        if rid not in self._history:
            self._history[rid] = []

        self._history[rid].append(HealthRecord(
            resource_id=rid,
            health=new_health,
            details=details or {"old_health": old_health.value if old_health else None},
        ))

        # Trim old records
        if len(self._history[rid]) > self._max_history:
            self._history[rid] = self._history[rid][-self._max_history:]

        if old_health != new_health:
            logger.info(
                "resource_health_changed",
                resource_id=rid,
                old=old_health.value if old_health else "unknown",
                new=new_health.value,
            )

    def get_history(self, resource_id: str) -> list[HealthRecord]:
        """Get health history for a resource."""
        return list(self._history.get(resource_id, []))

    def get_latest(self, resource_id: str) -> HealthRecord | None:
        """Get the latest health record for a resource."""
        records = self._history.get(resource_id, [])
        return records[-1] if records else None

    def get_healthy_resources(self, resources: list[Resource]) -> list[Resource]:
        """Filter resources that are healthy."""
        return [
            r for r in resources
            if r.health == ResourceHealth.HEALTHY
        ]

    def get_degraded_resources(self, resources: list[Resource]) -> list[Resource]:
        """Filter resources that are degraded."""
        return [
            r for r in resources
            if r.health == ResourceHealth.DEGRADED
        ]

    def get_unhealthy_resources(self, resources: list[Resource]) -> list[Resource]:
        """Filter resources that are unavailable or in maintenance."""
        return [
            r for r in resources
            if r.health in (ResourceHealth.UNAVAILABLE, ResourceHealth.MAINTENANCE)
        ]

    def clear_history(self, resource_id: str | None = None) -> None:
        """Clear history for a resource or all resources."""
        if resource_id:
            self._history.pop(resource_id, None)
        else:
            self._history.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            rid: [r.__dict__ for r in records]
            for rid, records in self._history.items()
        }
