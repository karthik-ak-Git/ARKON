"""Event broker."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any

from app.events.exceptions import BrokerError, BrokerNotReadyError
from app.events.interfaces import DeliveryMode, Event, EventState


@dataclass
class BrokerConfig:
    """Broker configuration."""

    max_queue_size: int = 10000
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    delivery_timeout_seconds: float = 30.0
    enable_persistence: bool = True
    enable_compression: bool = False


class EventBroker:
    """Message broker for event delivery."""

    def __init__(self, config: BrokerConfig | None = None) -> None:
        self._config = config or BrokerConfig()
        self._queues: dict[str, list[Event]] = {}
        self._retry_counts: dict[str, dict[str, int]] = {}
        self._dead_letter_queue: list[tuple[Event, str]] = []
        self._is_running = False
        self._lock = threading.Lock()
        self._metrics = {
            "published": 0,
            "delivered": 0,
            "failed": 0,
            "retried": 0,
            "dead_lettered": 0,
        }

    def start(self) -> None:
        with self._lock:
            self._is_running = True

    def stop(self) -> None:
        with self._lock:
            self._is_running = False

    def publish(self, event: Event, topic: str = "default") -> bool:
        """Publish an event to a topic queue."""
        if not self._is_running:
            raise BrokerNotReadyError("Broker is not running")

        with self._lock:
            if topic not in self._queues:
                self._queues[topic] = []
            queue = self._queues[topic]
            if len(queue) >= self._config.max_queue_size:
                queue.pop(0)

            event.state = EventState.PENDING
            queue.append(event)
            self._retry_counts.setdefault(event.event_id, {})
            self._metrics["published"] += 1
            return True

    def consume(self, topic: str = "default") -> Event | None:
        """Consume an event from a topic queue."""
        with self._lock:
            queue = self._queues.get(topic, [])
            if not queue:
                return None
            event = queue.pop(0)
            event.state = EventState.DELIVERING
            return event

    def peek(self, topic: str = "default", limit: int = 10) -> list[Event]:
        with self._lock:
            queue = self._queues.get(topic, [])
            return list(queue[:limit])

    def acknowledge(self, event_id: str, topic: str = "default") -> bool:
        """Acknowledge successful delivery."""
        with self._lock:
            self._metrics["delivered"] += 1
            self._retry_counts.pop(event_id, None)
            return True

    def retry(self, event: Event, topic: str = "default") -> bool:
        """Retry a failed event."""
        retries = self._retry_counts.get(event.event_id, {})
        count = retries.get(topic, 0)

        if count >= self._config.max_retries:
            self._dead_letter_queue.append((event, f"Max retries ({count}) exceeded"))
            self._metrics["dead_lettered"] += 1
            return False

        with self._lock:
            retries[topic] = count + 1
            self._retry_counts[event.event_id] = retries

            queue = self._queues.setdefault(topic, [])
            event.state = EventState.PENDING
            queue.append(event)
            self._metrics["retried"] += 1
            return True

    def send_to_dead_letter(self, event: Event, reason: str) -> None:
        with self._lock:
            self._dead_letter_queue.append((event, reason))
            self._metrics["dead_lettered"] += 1

    def get_dead_letters(self) -> list[tuple[Event, str]]:
        return list(self._dead_letter_queue)

    def get_queue_size(self, topic: str = "default") -> int:
        return len(self._queues.get(topic, []))

    def get_metrics(self) -> dict[str, Any]:
        return dict(self._metrics)

    def get_topics(self) -> list[str]:
        return list(self._queues.keys())

    def clear(self, topic: str | None = None) -> None:
        with self._lock:
            if topic:
                self._queues.pop(topic, None)
            else:
                self._queues.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_running": self._is_running,
            "topics": len(self._queues),
            "total_queued": sum(len(q) for q in self._queues.values()),
            "dead_letters": len(self._dead_letter_queue),
            "metrics": self._metrics,
        }
