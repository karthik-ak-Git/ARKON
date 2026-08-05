"""ARKON Resource Manager - Monitor.

Continuous resource monitoring for health and usage.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import structlog

from app.resources.interfaces import ResourceHealth, ResourceType
from app.resources.resource import Resource
from app.resources.health import ResourceHealthTracker

logger = structlog.get_logger(__name__)


class ResourceMonitor:
    """Monitors resources for health and utilization.

    Runs periodic checks and detects resource exhaustion.
    """

    def __init__(self, health_tracker: ResourceHealthTracker | None = None) -> None:
        self._health_tracker = health_tracker or ResourceHealthTracker()
        self._thresholds: dict[str, float] = {
            "warning": 0.8,
            "critical": 0.95,
        }
        self._callbacks: list[Callable[[str, ResourceHealth, dict[str, Any]], None]] = []

    def set_threshold(self, name: str, value: float) -> None:
        """Set a monitoring threshold."""
        self._thresholds[name] = value

    def on_health_change(
        self,
        callback: Callable[[str, ResourceHealth, dict[str, Any]], None],
    ) -> None:
        """Register a callback for health changes."""
        self._callbacks.append(callback)

    def check_resource(self, resource: Resource) -> dict[str, Any]:
        """Check a single resource and update its health.

        Returns a status report.
        """
        report: dict[str, Any] = {
            "resource_id": resource.resource_id,
            "resource_type": resource.resource_type.value,
            "available": resource.available,
            "capacity": resource.capacity,
            "utilization": resource.utilization,
            "health": resource.health.value,
        }

        # Determine health based on utilization
        utilization = resource.utilization
        new_health = resource.health

        if utilization >= self._thresholds.get("critical", 0.95):
            new_health = ResourceHealth.DEGRADED
            report["status"] = "critical"
        elif utilization >= self._thresholds.get("warning", 0.8):
            new_health = ResourceHealth.BUSY
            report["status"] = "warning"
        elif resource.health == ResourceHealth.DEGRADED and utilization < 0.5:
            new_health = ResourceHealth.RECOVERED
            report["status"] = "recovered"
        else:
            report["status"] = "ok"

        if new_health != resource.health:
            self._health_tracker.record_health(resource, new_health)
            self._notify_callbacks(resource.resource_id, new_health, report)

        return report

    def check_all(self, resources: list[Resource]) -> list[dict[str, Any]]:
        """Check all resources."""
        return [self.check_resource(r) for r in resources]

    def get_utilization_report(self, resources: list[Resource]) -> dict[str, Any]:
        """Generate a utilization report across resources."""
        total_capacity = sum(r.capacity for r in resources)
        total_available = sum(r.available for r in resources)
        total_reserved = sum(r.reserved for r in resources)
        total_allocated = sum(r.allocated for r in resources)

        by_type: dict[str, dict[str, float]] = {}
        for r in resources:
            rt = r.resource_type.value
            if rt not in by_type:
                by_type[rt] = {"capacity": 0, "available": 0, "allocated": 0, "reserved": 0}
            by_type[rt]["capacity"] += r.capacity
            by_type[rt]["available"] += r.available
            by_type[rt]["allocated"] += r.allocated
            by_type[rt]["reserved"] += r.reserved

        return {
            "total_capacity": total_capacity,
            "total_available": total_available,
            "total_reserved": total_reserved,
            "total_allocated": total_allocated,
            "overall_utilization": (
                (total_capacity - total_available) / total_capacity
                if total_capacity > 0 else 0.0
            ),
            "by_type": by_type,
            "resource_count": len(resources),
        }

    def _notify_callbacks(
        self,
        resource_id: str,
        health: ResourceHealth,
        details: dict[str, Any],
    ) -> None:
        """Notify registered callbacks of health changes."""
        for callback in self._callbacks:
            try:
                callback(resource_id, health, details)
            except Exception as e:
                logger.error(
                    "monitor_callback_error",
                    resource_id=resource_id,
                    error=str(e),
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "thresholds": self._thresholds,
            "callback_count": len(self._callbacks),
        }
