"""ARKON Capability Registry - Health Tracker.

Tracks provider health status with history.
"""

from __future__ import annotations

import time
from typing import Any

from app.capabilities.interfaces import ProviderHealth


class HealthTracker:
    """Tracks provider health status with history."""

    def __init__(self) -> None:
        self._health: dict[str, ProviderHealth] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._last_check: dict[str, float] = {}

    def get_health(self, provider_id: str) -> ProviderHealth:
        """Get current health of a provider."""
        return self._health.get(provider_id, ProviderHealth.UNKNOWN)

    def set_health(self, provider_id: str, health: ProviderHealth) -> ProviderHealth | None:
        """Set health for a provider.

        Returns:
            Previous health if changed, None if same.
        """
        old_health = self._health.get(provider_id)
        self._health[provider_id] = health
        self._last_check[provider_id] = time.time()

        if old_health is None or old_health != health:
            if provider_id not in self._history:
                self._history[provider_id] = []
            self._history[provider_id].append({
                "old": old_health.value if old_health else "unknown",
                "new": health.value,
                "timestamp": time.time(),
            })
            return old_health

        return None

    def get_history(self, provider_id: str) -> list[dict[str, Any]]:
        """Get health change history for a provider."""
        return list(self._history.get(provider_id, []))

    def get_last_check(self, provider_id: str) -> float | None:
        """Get timestamp of last health check."""
        return self._last_check.get(provider_id)

    def is_healthy(self, provider_id: str) -> bool:
        """Check if provider is healthy or degraded (usable)."""
        health = self.get_health(provider_id)
        return health in {ProviderHealth.HEALTHY, ProviderHealth.DEGRADED}

    def get_all_health(self) -> dict[str, str]:
        """Get health status for all tracked providers."""
        return {pid: h.value for pid, h in self._health.items()}

    def remove(self, provider_id: str) -> None:
        """Remove health tracking for a provider."""
        self._health.pop(provider_id, None)
        self._history.pop(provider_id, None)
        self._last_check.pop(provider_id, None)

    def clear(self) -> None:
        """Clear all health tracking data."""
        self._health.clear()
        self._history.clear()
        self._last_check.clear()

    def get_summary(self) -> dict[str, Any]:
        """Get health summary across all providers."""
        counts: dict[str, int] = {}
        for health in self._health.values():
            counts[health.value] = counts.get(health.value, 0) + 1
        return {
            "total": len(self._health),
            "by_status": counts,
        }
