"""Event Bus exceptions."""

from __future__ import annotations


class EventBusError(Exception):
    """Base event bus error."""


class PublishError(EventBusError):
    """Failed to publish event."""


class SubscribeError(EventBusError):
    """Failed to subscribe."""


class UnsubscribeError(EventBusError):
    """Failed to unsubscribe."""


class SerializationError(EventBusError):
    """Failed to serialize/deserialize event."""


class DeliveryError(EventBusError):
    """Failed to deliver event."""


class ChannelError(EventBusError):
    """Channel operation error."""


class TopicError(EventBusError):
    """Topic operation error."""


class FilterError(EventBusError):
    """Filter evaluation error."""


class PersistenceError(EventBusError):
    """Event persistence error."""


class ReplayError(EventBusError):
    """Event replay error."""


class DeadLetterError(EventBusError):
    """Dead letter queue error."""


class MiddlewareError(EventBusError):
    """Middleware execution error."""


class ValidationError(EventBusError):
    """Event validation error."""


class OrderingError(EventBusError):
    """Event ordering error."""


class BackpressureError(EventBusError):
    """Backpressure limit exceeded."""


class TimeoutError(EventBusError):
    """Operation timed out."""


class SubscriptionError(EventBusError):
    """Subscription operation error."""


class SubscriptionNotFoundError(SubscriptionError):
    """Subscription not found."""


class ChannelNotFoundError(ChannelError):
    """Channel not found."""


class TopicNotFoundError(TopicError):
    """Topic not found."""


class EventBusClosedError(EventBusError):
    """Event bus is closed."""


class EventBusNotReadyError(EventBusError):
    """Event bus is not ready."""


class EventSerializationError(EventBusError):
    """Failed to serialize/deserialize event."""


class EventValidationError(EventBusError):
    """Event validation error."""


class BrokerError(EventBusError):
    """Broker operation error."""


class BrokerNotReadyError(BrokerError):
    """Broker is not running."""


class StreamError(EventBusError):
    """Stream operation error."""


class RouterError(EventBusError):
    """Router operation error."""
