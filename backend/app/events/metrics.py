"""Event bus metrics collection."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from app.events.interfaces import EventBusMetrics, EventPriority


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: dict[str, str] = field(default_factory=dict)


class EventBusMetricsCollector:
    """Collects and aggregates event bus metrics."""

    def __init__(self) -> None:
        self._metrics = EventBusMetrics()
        self._start_time = time.time()
        self._delivery_latencies: list[float] = []
        self._lock = threading.Lock()
        self._metric_history: list[MetricPoint] = []

    def record_published(self) -> None:
        with self._lock:
            self._metrics.events_published += 1

    def record_delivered(self, latency_ms: float = 0.0) -> None:
        with self._lock:
            self._metrics.events_delivered += 1
            self._delivery_latencies.append(latency_ms)
            self._update_latency_stats()

    def record_failed(self) -> None:
        with self._lock:
            self._metrics.events_failed += 1

    def record_dead_lettered(self) -> None:
        with self._lock:
            self._metrics.events_dead_lettered += 1

    def record_replayed(self) -> None:
        with self._lock:
            self._metrics.events_replayed += 1

    def record_filtered(self) -> None:
        with self._lock:
            self._metrics.events_filtered += 1

    def record_backpressure(self) -> None:
        with self._lock:
            self._metrics.backpressure_events += 1

    def set_active_subscriptions(self, count: int) -> None:
        with self._lock:
            self._metrics.active_subscriptions = count

    def set_active_channels(self, count: int) -> None:
        with self._lock:
            self._metrics.active_channels = count

    def set_active_topics(self, count: int) -> None:
        with self._lock:
            self._metrics.active_topics = count

    def _update_latency_stats(self) -> None:
        if self._delivery_latencies:
            self._metrics.avg_delivery_latency_ms = sum(self._delivery_latencies) / len(
                self._delivery_latencies
            )
            self._metrics.max_delivery_latency_ms = max(self._delivery_latencies)

    def get_metrics(self) -> EventBusMetrics:
        with self._lock:
            self._metrics.uptime_seconds = time.time() - self._start_time
            return EventBusMetrics(
                events_published=self._metrics.events_published,
                events_delivered=self._metrics.events_delivered,
                events_failed=self._metrics.events_failed,
                events_dead_lettered=self._metrics.events_dead_lettered,
                events_replayed=self._metrics.events_replayed,
                events_filtered=self._metrics.events_filtered,
                active_subscriptions=self._metrics.active_subscriptions,
                active_channels=self._metrics.active_channels,
                active_topics=self._metrics.active_topics,
                avg_delivery_latency_ms=self._metrics.avg_delivery_latency_ms,
                max_delivery_latency_ms=self._metrics.max_delivery_latency_ms,
                backpressure_events=self._metrics.backpressure_events,
                uptime_seconds=self._metrics.uptime_seconds,
            )

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a custom metric point."""
        point = MetricPoint(name=name, value=value, tags=tags or {})
        self._metric_history.append(point)

    def get_metric_history(self, name: str | None = None) -> list[MetricPoint]:
        if name:
            return [p for p in self._metric_history if p.name == name]
        return list(self._metric_history)

    def reset(self) -> None:
        with self._lock:
            self._metrics = EventBusMetrics()
            self._start_time = time.time()
            self._delivery_latencies.clear()
            self._metric_history.clear()

    def to_dict(self) -> dict[str, Any]:
        return self.get_metrics().to_dict()
