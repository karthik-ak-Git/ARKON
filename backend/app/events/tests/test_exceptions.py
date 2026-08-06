"""Tests for Event Bus exceptions."""

import pytest
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


class TestExceptionHierarchy:
    def test_base_exception(self):
        with pytest.raises(EventBusError):
            raise EventBusError("test")

    def test_not_ready(self):
        with pytest.raises(EventBusNotReadyError):
            raise EventBusNotReadyError("not ready")

    def test_serialization(self):
        with pytest.raises(EventSerializationError):
            raise EventSerializationError("bad data")

    def test_validation(self):
        with pytest.raises(EventValidationError):
            raise EventValidationError("invalid")

    def test_channel_not_found(self):
        with pytest.raises(ChannelNotFoundError):
            raise ChannelNotFoundError("missing")

    def test_topic_not_found(self):
        with pytest.raises(TopicNotFoundError):
            raise TopicNotFoundError("missing")

    def test_subscription_not_found(self):
        with pytest.raises(SubscriptionNotFoundError):
            raise SubscriptionNotFoundError("missing")

    def test_broker_not_ready(self):
        with pytest.raises(BrokerNotReadyError):
            raise BrokerNotReadyError("not ready")

    def test_inheritance(self):
        assert issubclass(EventBusNotReadyError, EventBusError)
        assert issubclass(ChannelNotFoundError, ChannelError)
        assert issubclass(TopicNotFoundError, TopicError)
        assert issubclass(SubscriptionNotFoundError, SubscriptionError)
        assert issubclass(BrokerNotReadyError, BrokerError)

    def test_all_imports(self):
        assert issubclass(ChannelError, EventBusError)
        assert issubclass(TopicError, EventBusError)
        assert issubclass(SubscriptionError, EventBusError)
        assert issubclass(FilterError, EventBusError)
        assert issubclass(MiddlewareError, EventBusError)
        assert issubclass(PersistenceError, EventBusError)
        assert issubclass(ReplayError, EventBusError)
        assert issubclass(DeadLetterError, EventBusError)
        assert issubclass(StreamError, EventBusError)
        assert issubclass(RouterError, EventBusError)
