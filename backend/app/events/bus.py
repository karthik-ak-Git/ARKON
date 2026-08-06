"""Event bus — core orchestrator."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.broker import BrokerConfig, EventBroker
from app.events.channel import ChannelManager
from app.events.dead_letter import DeadLetterQueue
from app.events.dispatcher import DispatchResult, EventDispatcher
from app.events.exceptions import (
    EventBusError,
    EventBusNotReadyError,
    SubscriptionError,
)
from app.events.filter import EventFilter
from app.events.interfaces import (
    ChannelType,
    DeliveryMode,
    Event,
    EventBusMetrics,
    EventMetadata,
    EventPriority,
    EventState,
    IEventBus,
    Subscription,
    SubscriptionType,
)
from app.events.metrics import EventBusMetricsCollector
from app.events.middleware import MiddlewarePipeline
from app.events.persistence import EventPersistenceManager
from app.events.publisher import EventPublisher, PublisherConfig
from app.events.replay import EventReplayManager
from app.events.router import EventRouter, RoutingRule
from app.events.serializer import EventSerializer
from app.events.stream import EventStream
from app.events.subscriber import EventSubscriber, SubscriberConfig
from app.events.subscription import SubscriptionManager
from app.events.topic import TopicManager


@dataclass
class EventBusConfig:
    """EventBus configuration."""

    broker_config: BrokerConfig | None = None
    publisher_config: PublisherConfig | None = None
    subscriber_config: SubscriberConfig | None = None
    enable_metrics: bool = True
    enable_persistence: bool = True
    enable_replay: bool = True
    enable_dead_letter: bool = True
    enable_streaming: bool = True


class EventBus(IEventBus):
    """Central event bus orchestrating all subsystems."""

    def __init__(self, config: EventBusConfig | None = None) -> None:
        self._config = config or EventBusConfig()
        self._is_running = False
        self._lock = threading.Lock()

        self._broker = EventBroker(self._config.broker_config)
        self._publisher = EventPublisher(self._config.publisher_config)
        self._subscriber = EventSubscriber("main", self._config.subscriber_config)
        self._dispatcher = EventDispatcher()
        self._router = EventRouter()
        self._serializer = EventSerializer()
        self._pipeline = MiddlewarePipeline()
        self._filter = EventFilter()
        self._channel_manager = ChannelManager()
        self._topic_manager = TopicManager()
        self._subscription_manager = SubscriptionManager()
        self._persistence = EventPersistenceManager()
        self._replay = EventReplayManager()
        self._dead_letter = DeadLetterQueue()
        self._stream = EventStream()
        self._metrics = EventBusMetricsCollector() if self._config.enable_metrics else None

        self._event_handlers: dict[str, list[Callable[[Event], Any]]] = {}
        self._event_history: list[Event] = []
        self._publish_count = 0
        self._deliver_count = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        with self._lock:
            if self._is_running:
                return
            self._broker.start()
            self._stream.start()
            self._is_running = True

    def stop(self) -> None:
        with self._lock:
            if not self._is_running:
                return
            self._broker.stop()
            self._stream.stop()
            self._is_running = False

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
        """Publish an event."""
        if not self._is_running:
            raise EventBusNotReadyError("EventBus is not running")

        event = self._publisher.publish(
            event_type=event_type,
            source=source,
            target=target,
            channel=channel,
            topic=topic,
            workspace_id=workspace_id,
            priority=priority,
            delivery_mode=delivery_mode,
            payload=payload,
            metadata=metadata,
            correlation_id=correlation_id,
        )

        with self._lock:
            self._event_history.append(event)
            self._publish_count += 1

        if self._metrics:
            self._metrics.record_published()

        self._broker.publish(event, topic)
        self._stream.publish(event)
        self._deliver(event)

        return event

    def _deliver(self, event: Event) -> None:
        matching = self._subscription_manager.find_matching(event)
        if matching:
            self._dispatcher.dispatch_batch(event, matching)
            with self._lock:
                self._deliver_count += len(matching)

    def subscribe(
        self,
        topic: str,
        callback: Callable[[Event], Any] | None = None,
        subscription_type: SubscriptionType = SubscriptionType.EXACT,
        channel: ChannelType | None = None,
        priority: int = 0,
        workspace_id: str = "",
    ) -> Subscription:
        if not self._is_running:
            raise EventBusNotReadyError("EventBus is not running")

        sub = self._subscription_manager.create_subscription(
            subscriber_id="main",
            topic=topic,
            callback=callback,
            subscription_type=subscription_type,
            channel=channel,
            priority=priority,
            workspace_id=workspace_id,
        )
        self._router.subscribe(sub)
        return sub

    def unsubscribe(self, subscription_id: str) -> bool:
        return self._subscription_manager.remove_subscription(subscription_id)

    def add_event_handler(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        with self._lock:
            self._event_handlers.setdefault(event_type, []).append(handler)

    def remove_event_handler(self, event_type: str, handler: Callable[[Event], Any]) -> bool:
        with self._lock:
            handlers = self._event_handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)
                return True
            return False

    def get_event_handlers(self, event_type: str) -> list[Callable[[Event], Any]]:
        return list(self._event_handlers.get(event_type, []))

    def get_event_history(self, limit: int = 100) -> list[Event]:
        return list(self._event_history[-limit:])

    def get_metrics(self) -> dict[str, Any]:
        return {
            "publish_count": self._publish_count,
            "deliver_count": self._deliver_count,
            "subscriptions": self._subscription_manager.count(),
            "history_size": len(self._event_history),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_running": self._is_running,
            "publish_count": self._publish_count,
            "deliver_count": self._deliver_count,
            "subscriptions": self._subscription_manager.count(),
            "channels": self._channel_manager.count(),
            "topics": self._topic_manager.count(),
        }
