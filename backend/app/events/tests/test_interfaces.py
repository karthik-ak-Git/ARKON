"""Tests for Event Bus interfaces."""

import time
from app.events.interfaces import (
    Event,
    EventMetadata,
    Subscription,
    SubscriptionType,
    ChannelType,
    DeliveryMode,
    EventPriority,
    EventState,
    EventType,
    ReplayStrategy,
)


class TestEvent:
    def test_create_event(self):
        event = Event(event_type=EventType.TASK)
        assert event.event_type == EventType.TASK
        assert event.event_id != ""
        assert event.state == EventState.PENDING

    def test_event_metadata(self):
        meta = EventMetadata(
            source="test",
            channel=ChannelType.SYSTEM,
            topic="test-topic",
        )
        event = Event(metadata=meta)
        assert event.metadata.source == "test"
        assert event.metadata.channel == ChannelType.SYSTEM

    def test_event_payload(self):
        event = Event(payload={"key": "value"})
        assert event.payload == {"key": "value"}

    def test_event_to_dict(self):
        event = Event(payload={"a": 1})
        d = event.to_dict()
        assert "event_id" in d
        assert d["payload"]["a"] == 1

    def test_event_timestamp(self):
        before = time.time()
        event = Event()
        after = time.time()
        assert before <= event.timestamp <= after

    def test_event_priority(self):
        event = Event(priority=EventPriority.HIGH)
        assert event.priority == EventPriority.HIGH

    def test_event_delivery_mode(self):
        event = Event(delivery_mode=DeliveryMode.AT_LEAST_ONCE)
        assert event.delivery_mode == DeliveryMode.AT_LEAST_ONCE

    def test_event_string_type(self):
        event = Event(event_type="custom.type")
        assert event.event_type == "custom.type"

    def test_event_default_type(self):
        event = Event()
        assert event.event_type == EventType.CUSTOM


class TestEventMetadata:
    def test_default_values(self):
        meta = EventMetadata()
        assert meta.source == ""
        assert meta.channel == ChannelType.SYSTEM

    def test_fields(self):
        meta = EventMetadata(
            source="src",
            target="tgt",
            workspace_id="ws-1",
            correlation_id="corr-1",
            causation_id="caus-1",
            version=2,
            channel=ChannelType.AGENT,
            topic="test-topic",
            tags=["tag1", "tag2"],
        )
        assert meta.source == "src"
        assert meta.target == "tgt"
        assert meta.workspace_id == "ws-1"
        assert meta.correlation_id == "corr-1"
        assert meta.causation_id == "caus-1"
        assert meta.version == 2
        assert meta.channel == ChannelType.AGENT
        assert meta.topic == "test-topic"
        assert meta.tags == ["tag1", "tag2"]


class TestSubscription:
    def test_create_subscription(self):
        sub = Subscription(topic="tasks")
        assert sub.topic == "tasks"
        assert sub.is_active is True

    def test_exact_match(self):
        sub = Subscription(topic="tasks", subscription_type=SubscriptionType.EXACT)
        event = Event(metadata=EventMetadata(topic="tasks"))
        assert sub.matches(event) is True

    def test_exact_no_match(self):
        sub = Subscription(topic="tasks")
        event = Event(metadata=EventMetadata(topic="other"))
        assert sub.matches(event) is False

    def test_wildcard_match(self):
        sub = Subscription(topic="*", subscription_type=SubscriptionType.WILDCARD)
        event = Event(metadata=EventMetadata(topic="anything"))
        assert sub.matches(event) is True

    def test_predicate_match(self):
        sub = Subscription(
            topic="tasks",
            subscription_type=SubscriptionType.PREDICATE,
            predicate=lambda e: e.payload.get("priority") == "high",
        )
        event = Event(metadata=EventMetadata(topic="tasks"), payload={"priority": "high"})
        assert sub.matches(event) is True

    def test_predicate_no_match(self):
        sub = Subscription(
            topic="tasks",
            subscription_type=SubscriptionType.PREDICATE,
            predicate=lambda e: e.payload.get("priority") == "high",
        )
        event = Event(metadata=EventMetadata(topic="tasks"), payload={"priority": "low"})
        assert sub.matches(event) is False

    def test_inactive_subscription(self):
        sub = Subscription(topic="tasks", is_active=False)
        event = Event(metadata=EventMetadata(topic="tasks"))
        assert sub.matches(event) is False


class TestEnums:
    def test_channel_types(self):
        assert ChannelType.SYSTEM.value == "system"
        assert ChannelType.AGENT.value == "agent"
        assert ChannelType.SCHEDULER.value == "scheduler"

    def test_event_states(self):
        assert EventState.PENDING.value == "pending"
        assert EventState.DELIVERED.value == "delivered"
        assert EventState.FAILED.value == "failed"

    def test_delivery_modes(self):
        assert DeliveryMode.FIRE_AND_FORGET.value == "fire_and_forget"
        assert DeliveryMode.AT_LEAST_ONCE.value == "at_least_once"
        assert DeliveryMode.EXACTLY_ONCE.value == "exactly_once"

    def test_priority_levels(self):
        assert EventPriority.CRITICAL.value == 0
        assert EventPriority.HIGH.value == 1
        assert EventPriority.LOW.value == 10

    def test_event_types(self):
        assert EventType.TASK.value == "task"
        assert EventType.RESOURCE.value == "resource"
        assert EventType.SYSTEM.value == "system"

    def test_replay_strategies(self):
        assert ReplayStrategy.ALL.value == "all"
        assert ReplayStrategy.SINCE_TIMESTAMP.value == "since_timestamp"
        assert ReplayStrategy.SINCE_EVENT_ID.value == "since_event_id"
        assert ReplayStrategy.FROM_LAST_CHECKPOINT.value == "from_last_checkpoint"
