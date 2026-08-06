"""Event publisher."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any

from app.events.interfaces import (
    ChannelType,
    DeliveryMode,
    Event,
    EventMetadata,
    EventPriority,
    EventState,
    EventType,
)


@dataclass
class PublisherConfig:
    """Publisher configuration."""

    default_delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    default_priority: EventPriority = EventPriority.NORMAL
    enable_batching: bool = False
    batch_size: int = 100
    batch_timeout_seconds: float = 1.0
    enable_async: bool = False


class EventPublisher:
    """Publishes events to the event bus."""

    def __init__(self, config: PublisherConfig | None = None) -> None:
        self._config = config or PublisherConfig()
        self._published_events: list[Event] = []
        self._pending_batch: list[Event] = []
        self._lock = threading.Lock()
        self._publish_count = 0
        self._on_publish: Any = None

    def set_on_publish(self, callback: Any) -> None:
        self._on_publish = callback

    def publish(
        self,
        event_type: str,
        source: str = "",
        target: str = "",
        channel: ChannelType = ChannelType.SYSTEM,
        topic: str = "",
        workspace_id: str = "",
        priority: EventPriority | None = None,
        delivery_mode: DeliveryMode | None = None,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> Event:
        """Publish a single event."""
        priority = priority or self._config.default_priority
        delivery_mode = delivery_mode or self._config.default_delivery_mode

        event_metadata = EventMetadata(
            source=source,
            target=target,
            channel=channel,
            topic=topic,
            workspace_id=workspace_id,
        )
        if correlation_id:
            event_metadata.correlation_id = correlation_id

        # Convert string to EventType if possible, otherwise keep as string
        if isinstance(event_type, str):
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                event_type_enum = event_type  # Keep as string for custom types
        else:
            event_type_enum = event_type

        event = Event(
            event_type=event_type_enum,
            metadata=event_metadata,
            payload=payload or {},
            priority=priority,
            delivery_mode=delivery_mode,
        )

        if self._config.enable_batching:
            self._pending_batch.append(event)
            if len(self._pending_batch) >= self._config.batch_size:
                self._flush_batch()
        else:
            self._record(event)
            if self._on_publish:
                self._on_publish(event)

        return event

    def publish_many(self, events: list[Event]) -> list[Event]:
        for event in events:
            self._record(event)
            if self._on_publish:
                self._on_publish(event)
        return events

    def _flush_batch(self) -> None:
        batch = list(self._pending_batch)
        self._pending_batch.clear()
        for event in batch:
            self._record(event)
            if self._on_publish:
                self._on_publish(event)

    def _record(self, event: Event) -> None:
        with self._lock:
            event.state = EventState.DELIVERING
            self._published_events.append(event)
            self._publish_count += 1

    def get_published_events(self) -> list[Event]:
        return list(self._published_events)

    def get_pending_batch(self) -> list[Event]:
        return list(self._pending_batch)

    def get_publish_count(self) -> int:
        return self._publish_count

    def flush(self) -> None:
        if self._config.enable_batching:
            self._flush_batch()

    def to_dict(self) -> dict[str, Any]:
        return {
            "published_count": self._publish_count,
            "pending_batch": len(self._pending_batch),
            "delivery_mode": self._config.default_delivery_mode.value,
            "priority": self._config.default_priority.value,
        }
