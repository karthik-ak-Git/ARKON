"""Event Bus interfaces and data models."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


# ─────────────────────────────────────
# ENUMS
# ─────────────────────────────────────


class EventType(enum.Enum):
    """Core event type categories."""

    TASK = "task"
    RESOURCE = "resource"
    CAPABILITY = "capability"
    HEARTBEAT = "heartbeat"
    LOG = "log"
    METRIC = "metric"
    PROGRESS = "progress"
    ERROR = "error"
    LIFECYCLE = "lifecycle"
    SYSTEM = "system"
    CUSTOM = "custom"


class DeliveryMode(enum.Enum):
    """Event delivery guarantees."""

    FIRE_AND_FORGET = "fire_and_forget"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class EventPriority(enum.Enum):
    """Event priority levels."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 5
    LOW = 10
    BACKGROUND = 15


class ChannelType(enum.Enum):
    """Communication channel types."""

    WORKSPACE = "workspace"
    AGENT = "agent"
    SCHEDULER = "scheduler"
    EXECUTION = "execution"
    RUNTIME = "runtime"
    RESOURCE = "resource"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"
    MONITORING = "monitoring"
    SYSTEM = "system"
    CUSTOM = "custom"


class SubscriptionType(enum.Enum):
    """Subscription matching types."""

    EXACT = "exact"
    WILDCARD = "wildcard"
    PATTERN = "pattern"
    PREDICATE = "predicate"


class EventState(enum.Enum):
    """Event lifecycle states."""

    PENDING = "pending"
    PUBLISHED = "published"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    REPLAYED = "replayed"


class ReplayStrategy(enum.Enum):
    """Event replay strategies."""

    ALL = "all"
    SINCE_TIMESTAMP = "since_timestamp"
    SINCE_EVENT_ID = "since_event_id"
    FROM_LAST_CHECKPOINT = "from_last_checkpoint"


# ─────────────────────────────────────
# CORE EVENT MODEL
# ─────────────────────────────────────


@dataclass
class EventMetadata:
    """Event metadata for routing and delivery."""

    source: str = ""
    target: str = ""
    workspace_id: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    version: int = 1
    channel: ChannelType = ChannelType.SYSTEM
    topic: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Event:
    """Core event data model."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM
    timestamp: float = field(default_factory=time.time)
    priority: EventPriority = EventPriority.NORMAL
    state: EventState = EventState.PENDING
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: EventMetadata = field(default_factory=EventMetadata)
    delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET
    max_retries: int = 3
    retry_count: int = 0
    ttl: float | None = None
    scheduled_at: float | None = None

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() > self.timestamp + self.ttl

    @property
    def is_scheduled(self) -> bool:
        if self.scheduled_at is None:
            return False
        return time.time() < self.scheduled_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "state": self.state.value,
            "payload": self.payload,
            "metadata": {
                "source": self.metadata.source,
                "target": self.metadata.target,
                "workspace_id": self.metadata.workspace_id,
                "correlation_id": self.metadata.correlation_id,
                "causation_id": self.metadata.causation_id,
                "version": self.metadata.version,
                "channel": self.metadata.channel.value,
                "topic": self.metadata.topic,
                "tags": self.metadata.tags,
            },
            "delivery_mode": self.delivery_mode.value,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "ttl": self.ttl,
            "scheduled_at": self.scheduled_at,
        }


@dataclass
class Subscription:
    """Event subscription definition."""

    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subscription_type: SubscriptionType = SubscriptionType.EXACT
    event_type: EventType | None = None
    topic: str = ""
    topic_pattern: str = ""
    callback: Callable[[Event], Any] | None = None
    channel: ChannelType | None = None
    workspace_id: str | None = None
    predicate: Callable[[Event], bool] | None = None
    priority: int = 0
    is_active: bool = True
    max_delivery_attempts: int = 3
    created_at: float = field(default_factory=time.time)

    def matches(self, event: Event) -> bool:
        """Check if this subscription matches an event."""
        if not self.is_active:
            return False

        if self.event_type is not None and event.event_type != self.event_type:
            return False

        if self.channel is not None and event.metadata.channel != self.channel:
            return False

        if self.workspace_id and event.metadata.workspace_id != self.workspace_id:
            return False

        if self.subscription_type == SubscriptionType.EXACT:
            return self.topic == event.metadata.topic

        if self.subscription_type == SubscriptionType.WILDCARD:
            return self._wildcard_match(self.topic, event.metadata.topic)

        if self.subscription_type == SubscriptionType.PATTERN:
            return self._pattern_match(self.topic_pattern, event.metadata.topic)

        if self.subscription_type == SubscriptionType.PREDICATE:
            if self.predicate is None:
                return False
            try:
                return self.predicate(event)
            except Exception:
                return False

        return False

    def _wildcard_match(self, pattern: str, topic: str) -> bool:
        """Simple wildcard matching with * and **."""
        if pattern == "**":
            return True
        pattern_parts = pattern.split(".")
        topic_parts = topic.split(".")
        return self._match_parts(pattern_parts, topic_parts)

    def _match_parts(self, pattern_parts: list[str], topic_parts: list[str]) -> bool:
        """Match pattern parts against topic parts."""
        pi = 0
        ti = 0
        while pi < len(pattern_parts) and ti < len(topic_parts):
            if pattern_parts[pi] == "**":
                return True
            if pattern_parts[pi] == "*":
                pi += 1
                ti += 1
            elif pattern_parts[pi] == topic_parts[ti]:
                pi += 1
                ti += 1
            else:
                return False
        return pi == len(pattern_parts) and ti == len(topic_parts)

    def _pattern_match(self, pattern: str, topic: str) -> bool:
        """Regex pattern matching."""
        import re
        try:
            return bool(re.match(pattern, topic))
        except re.error:
            return False


@dataclass
class Channel:
    """Communication channel."""

    channel_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channel_type: ChannelType = ChannelType.SYSTEM
    name: str = ""
    description: str = ""
    is_active: bool = True
    max_subscribers: int = 1000
    max_events_per_second: float = 1000.0
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "channel_type": self.channel_type.value,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "max_subscribers": self.max_subscribers,
            "max_events_per_second": self.max_events_per_second,
            "created_at": self.created_at,
        }


@dataclass
class Topic:
    """Event topic."""

    topic_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    channel: ChannelType = ChannelType.SYSTEM
    is_active: bool = True
    retention_seconds: float = 3600.0
    max_subscribers: int = 100
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "description": self.description,
            "channel": self.channel.value,
            "is_active": self.is_active,
            "retention_seconds": self.retention_seconds,
        }


@dataclass
class DeliveryResult:
    """Result of event delivery."""

    success: bool = True
    event_id: str = ""
    subscription_id: str = ""
    error: str | None = None
    delivered_at: float = field(default_factory=time.time)
    attempt: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "event_id": self.event_id,
            "subscription_id": self.subscription_id,
            "error": self.error,
            "delivered_at": self.delivered_at,
            "attempt": self.attempt,
        }


@dataclass
class EventBusMetrics:
    """Event bus metrics."""

    events_published: int = 0
    events_delivered: int = 0
    events_failed: int = 0
    events_dead_lettered: int = 0
    events_replayed: int = 0
    events_filtered: int = 0
    active_subscriptions: int = 0
    active_channels: int = 0
    active_topics: int = 0
    avg_delivery_latency_ms: float = 0.0
    max_delivery_latency_ms: float = 0.0
    backpressure_events: int = 0
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "events_published": self.events_published,
            "events_delivered": self.events_delivered,
            "events_failed": self.events_failed,
            "events_dead_lettered": self.events_dead_lettered,
            "events_replayed": self.events_replayed,
            "events_filtered": self.events_filtered,
            "active_subscriptions": self.active_subscriptions,
            "active_channels": self.active_channels,
            "active_topics": self.active_topics,
            "avg_delivery_latency_ms": self.avg_delivery_latency_ms,
            "max_delivery_latency_ms": self.max_delivery_latency_ms,
            "backpressure_events": self.backpressure_events,
            "uptime_seconds": self.uptime_seconds,
        }


# ─────────────────────────────────────
# PROTOCOLS
# ─────────────────────────────────────


class IEventBus(Protocol):
    """Event bus interface."""

    def publish(self, event: Event) -> bool: ...
    def subscribe(self, subscription: Subscription) -> str: ...
    def unsubscribe(self, subscription_id: str) -> bool: ...
    def get_metrics(self) -> EventBusMetrics: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...


class IEventPublisher(Protocol):
    """Event publisher interface."""

    def publish(self, event: Event) -> bool: ...
    def publish_batch(self, events: list[Event]) -> list[bool]: ...


class IEventSubscriber(Protocol):
    """Event subscriber interface."""

    def subscribe(self, subscription: Subscription) -> str: ...
    def unsubscribe(self, subscription_id: str) -> bool: ...
    def get_subscriptions(self) -> list[Subscription]: ...


class IEventFilter(Protocol):
    """Event filter interface."""

    def matches(self, event: Event) -> bool: ...
    def get_name(self) -> str: ...


class IMiddleware(Protocol):
    """Middleware interface."""

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any: ...
    def get_name(self) -> str: ...


class IEventPersistence(Protocol):
    """Event persistence interface."""

    def persist(self, event: Event) -> bool: ...
    def load(self, event_id: str) -> Event | None: ...
    def load_range(self, start_time: float, end_time: float) -> list[Event]: ...
    def clear(self) -> None: ...
