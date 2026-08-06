"""Event Bus subsystem."""

from app.events.bus import EventBus, EventBusConfig
from app.events.broker import EventBroker, BrokerConfig
from app.events.channel import ChannelManager
from app.events.dead_letter import DeadLetterQueue, DeadLetterEntry
from app.events.dispatcher import EventDispatcher, DispatchResult
from app.events.exceptions import (
    EventBusError,
    EventBusNotReadyError,
    EventSerializationError,
    EventValidationError,
    ChannelError,
    ChannelNotFoundError,
    TopicError,
    TopicNotFoundError,
    SubscriptionError,
    SubscriptionNotFoundError,
    BrokerError,
    BrokerNotReadyError,
    FilterError,
    MiddlewareError,
    PersistenceError,
    ReplayError,
    DeadLetterError,
    StreamError,
    RouterError,
)
from app.events.filter import EventFilter
from app.events.interfaces import (
    Event,
    EventMetadata,
    EventBusMetrics,
    Subscription,
    SubscriptionType,
    ChannelType,
    DeliveryMode,
    EventPriority,
    EventState,
    ReplayStrategy,
    IEventBus,
    IEventPublisher,
    IEventSubscriber,
    IEventFilter,
    IMiddleware,
    IEventPersistence,
)
from app.events.metrics import EventBusMetricsCollector
from app.events.middleware import MiddlewarePipeline
from app.events.persistence import InMemoryEventStore, EventPersistenceManager
from app.events.publisher import EventPublisher, PublisherConfig
from app.events.replay import EventReplayManager, ReplayCheckpoint
from app.events.router import EventRouter, RoutingRule
from app.events.serializer import EventSerializer
from app.events.stream import EventStream, StreamSubscriber
from app.events.subscriber import EventSubscriber, SubscriberConfig
from app.events.subscription import SubscriptionManager, SubscriptionConfig
from app.events.topic import TopicManager

__all__ = [
    "EventBus",
    "EventBusConfig",
    "EventBroker",
    "BrokerConfig",
    "ChannelManager",
    "DeadLetterQueue",
    "DeadLetterEntry",
    "EventDispatcher",
    "DispatchResult",
    "EventFilter",
    "Event",
    "EventMetadata",
    "EventBusMetrics",
    "Subscription",
    "SubscriptionType",
    "ChannelType",
    "DeliveryMode",
    "EventPriority",
    "EventState",
    "ReplayStrategy",
    "IEventBus",
    "IEventPublisher",
    "IEventSubscriber",
    "IEventFilter",
    "IMiddleware",
    "IEventPersistence",
    "EventBusMetricsCollector",
    "MiddlewarePipeline",
    "InMemoryEventStore",
    "EventPersistenceManager",
    "EventPublisher",
    "PublisherConfig",
    "EventReplayManager",
    "ReplayCheckpoint",
    "EventRouter",
    "RoutingRule",
    "EventSerializer",
    "EventStream",
    "StreamSubscriber",
    "EventSubscriber",
    "SubscriberConfig",
    "SubscriptionManager",
    "SubscriptionConfig",
    "TopicManager",
]

__version__ = "0.1.0"
