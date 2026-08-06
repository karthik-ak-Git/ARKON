"""Event subscriber."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.interfaces import (
    Event,
    EventState,
    Subscription,
    SubscriptionType,
)


@dataclass
class SubscriberConfig:
    """Subscriber configuration."""

    auto_ack: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    buffer_size: int = 1000


class EventSubscriber:
    """Subscribes to events from the event bus."""

    def __init__(self, subscriber_id: str, config: SubscriberConfig | None = None) -> None:
        self._subscriber_id = subscriber_id
        self._config = config or SubscriberConfig()
        self._subscriptions: dict[str, Subscription] = {}
        self._received_events: list[Event] = []
        self._processing_events: dict[str, Event] = {}
        self._lock = threading.Lock()
        self._receive_count = 0
        self._callback: Callable[[Event], Any] | None = None

    @property
    def subscriber_id(self) -> str:
        return self._subscriber_id

    def subscribe(
        self,
        topic: str,
        callback: Callable[[Event], Any] | None = None,
        subscription_type: SubscriptionType = SubscriptionType.EXACT,
    ) -> Subscription:
        """Subscribe to a topic."""
        subscription = Subscription(
            topic=topic,
            callback=callback or self._default_callback,
            subscription_type=subscription_type,
        )
        with self._lock:
            self._subscriptions[subscription.subscription_id] = subscription
            if callback:
                self._callback = callback
        return subscription

    def unsubscribe(self, subscription_id: str) -> bool:
        with self._lock:
            return self._subscriptions.pop(subscription_id, None) is not None

    def receive(self, event: Event) -> bool:
        """Receive an event."""
        if len(self._received_events) >= self._config.buffer_size:
            self._received_events.pop(0)

        event.state = EventState.DELIVERING
        with self._lock:
            self._received_events.append(event)
            self._processing_events[event.event_id] = event
            self._receive_count += 1

        if self._callback:
            self._callback(event)

        if self._config.auto_ack:
            self.acknowledge(event.event_id)

        return True

    def acknowledge(self, event_id: str) -> bool:
        with self._lock:
            event = self._processing_events.pop(event_id, None)
            if event:
                event.state = EventState.DELIVERED
                return True
            return False

    def nack(self, event_id: str, requeue: bool = True) -> bool:
        with self._lock:
            event = self._processing_events.pop(event_id, None)
            if event:
                event.state = EventState.FAILED
                if requeue:
                    self._received_events.append(event)
                    self._processing_events[event_id] = event
                return True
            return False

    def _default_callback(self, event: Event) -> None:
        pass

    def get_subscriptions(self) -> list[Subscription]:
        return list(self._subscriptions.values())

    def get_received_events(self) -> list[Event]:
        return list(self._received_events)

    def get_receive_count(self) -> int:
        return self._receive_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "subscriber_id": self._subscriber_id,
            "subscriptions": len(self._subscriptions),
            "received_count": self._receive_count,
            "buffer_size": self._config.buffer_size,
        }
