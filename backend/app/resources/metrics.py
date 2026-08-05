"""ARKON Resource Manager - Metrics.

Resource usage metrics collection and reporting.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.resources.interfaces import ResourceType
from app.resources.resource import Resource

logger = structlog.get_logger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""

    resource_id: str
    metric_name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceMetrics:
    """Aggregated metrics for a resource."""

    resource_id: str
    resource_type: str
    utilization_history: list[float] = field(default_factory=list)
    allocation_count: int = 0
    reservation_count: int = 0
    release_count: int = 0
    error_count: int = 0
    avg_allocation_time_ms: float = 0.0
    peak_utilization: float = 0.0
    last_updated: float = field(default_factory=time.time)


class MetricsCollector:
    """Collects and aggregates resource metrics."""

    def __init__(self, max_history: int = 1000) -> None:
        self._metrics: dict[str, ResourceMetrics] = {}
        self._points: list[MetricPoint] = []
        self._max_history = max_history

    def _ensure_metric(self, resource: Resource) -> ResourceMetrics:
        """Ensure a metric entry exists for a resource."""
        rid = resource.resource_id
        if rid not in self._metrics:
            self._metrics[rid] = ResourceMetrics(
                resource_id=rid,
                resource_type=resource.resource_type.value,
            )
        return self._metrics[rid]

    def record_allocation(self, resource: Resource, amount: float, duration_ms: float = 0.0) -> None:
        """Record an allocation event."""
        m = self._ensure_metric(resource)
        m.allocation_count += 1
        m.peak_utilization = max(m.peak_utilization, resource.utilization)

        # Update rolling average
        total = m.avg_allocation_time_ms * (m.allocation_count - 1)
        m.avg_allocation_time_ms = (total + duration_ms) / m.allocation_count

        self._record_point(resource, "allocation", amount)
        m.last_updated = time.time()

    def record_reservation(self, resource: Resource, amount: float) -> None:
        """Record a reservation event."""
        m = self._ensure_metric(resource)
        m.reservation_count += 1
        self._record_point(resource, "reservation", amount)
        m.last_updated = time.time()

    def record_release(self, resource: Resource, amount: float) -> None:
        """Record a release event."""
        m = self._ensure_metric(resource)
        m.release_count += 1
        m.peak_utilization = max(m.peak_utilization, resource.utilization)
        self._record_point(resource, "release", amount)
        m.last_updated = time.time()

    def record_error(self, resource: Resource, error_type: str = "unknown") -> None:
        """Record an error event."""
        m = self._ensure_metric(resource)
        m.error_count += 1
        self._record_point(resource, "error", 1.0, labels={"error_type": error_type})
        m.last_updated = time.time()

    def record_utilization(self, resource: Resource) -> None:
        """Record current utilization."""
        m = self._ensure_metric(resource)
        util = resource.utilization
        m.utilization_history.append(util)
        if len(m.utilization_history) > self._max_history:
            m.utilization_history = m.utilization_history[-self._max_history:]
        m.peak_utilization = max(m.peak_utilization, util)
        m.last_updated = time.time()

    def get_metrics(self, resource_id: str) -> ResourceMetrics | None:
        """Get metrics for a resource."""
        return self._metrics.get(resource_id)

    def get_all_metrics(self) -> dict[str, ResourceMetrics]:
        """Get all resource metrics."""
        return dict(self._metrics)

    def get_utilization_stats(self, resource_id: str) -> dict[str, Any]:
        """Get utilization statistics for a resource."""
        m = self._metrics.get(resource_id)
        if not m or not m.utilization_history:
            return {}

        history = m.utilization_history
        return {
            "current": history[-1] if history else 0.0,
            "average": sum(history) / len(history) if history else 0.0,
            "peak": m.peak_utilization,
            "min": min(history) if history else 0.0,
            "max": max(history) if history else 0.0,
            "sample_count": len(history),
        }

    def _record_point(
        self,
        resource: Resource,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a metric data point."""
        self._points.append(MetricPoint(
            resource_id=resource.resource_id,
            metric_name=name,
            value=value,
            labels=labels or {},
        ))
        if len(self._points) > self._max_history * 10:
            self._points = self._points[-self._max_history * 5:]

    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._points.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_count": len(self._metrics),
            "point_count": len(self._points),
        }
