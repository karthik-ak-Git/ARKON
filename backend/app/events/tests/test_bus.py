"""Integration tests for EventBus."""

import threading
import time
from app.events.bus import EventBus, EventBusConfig
from app.events.interfaces import (
    ChannelType,
    DeliveryMode,
    Event,
    EventPriority,
    EventState,
    EventType,
    SubscriptionType,
)


class TestEventBusIntegration:
    def test_start_stop(self):
        bus = EventBus()
        bus.start()
        assert bus.is_running is True
        bus.stop()
        assert bus.is_running is False

    def test_publish_event(self):
        bus = EventBus()
        bus.start()
        event = bus.publish(
            event_type="test.event",
            source="test",
            channel=ChannelType.SYSTEM,
            topic="test-topic",
            payload={"key": "value"},
        )
        assert event.event_type == "test.event"
        assert event.payload == {"key": "value"}
        bus.stop()

    def test_subscribe_and_receive(self):
        bus = EventBus()
        bus.start()
        received = []
        bus.subscribe("tasks", callback=lambda e: received.append(e))
        bus.publish(event_type="task.created", topic="tasks")
        assert len(received) == 1
        bus.stop()

    def test_multiple_subscribers(self):
        bus = EventBus()
        bus.start()
        counts = {"a": 0, "b": 0}
        bus.subscribe("t", callback=lambda e: counts.update({"a": counts["a"] + 1}))
        bus.subscribe("t", callback=lambda e: counts.update({"b": counts["b"] + 1}))
        bus.publish(event_type="e", topic="t")
        assert counts["a"] == 1
        assert counts["b"] == 1
        bus.stop()

    def test_wildcard_subscription(self):
        bus = EventBus()
        bus.start()
        received = []
        bus.subscribe("*", callback=lambda e: received.append(e), subscription_type=SubscriptionType.WILDCARD)
        bus.publish(event_type="task.created", topic="tasks")
        bus.publish(event_type="resource.allocated", topic="resources")
        assert len(received) == 2
        bus.stop()

    def test_event_history(self):
        bus = EventBus()
        bus.start()
        bus.publish(event_type="e1")
        bus.publish(event_type="e2")
        history = bus.get_event_history()
        assert len(history) == 2
        bus.stop()

    def test_metrics(self):
        bus = EventBus()
        bus.start()
        bus.publish(event_type="e1", topic="t")
        m = bus.get_metrics()
        assert m["publish_count"] == 1
        bus.stop()

    def test_to_dict(self):
        bus = EventBus()
        bus.start()
        d = bus.to_dict()
        assert d["is_running"] is True
        bus.stop()

    def test_publish_before_start(self):
        bus = EventBus()
        try:
            bus.publish(event_type="test")
            assert False, "Should have raised"
        except Exception:
            pass

    def test_subscribe_before_start(self):
        bus = EventBus()
        try:
            bus.subscribe("t")
            assert False, "Should have raised"
        except Exception:
            pass

    def test_event_metadata_fields(self):
        bus = EventBus()
        bus.start()
        event = bus.publish(
            event_type="test",
            source="src",
            target="tgt",
            workspace_id="ws-1",
            correlation_id="corr-1",
            priority=EventPriority.HIGH,
            delivery_mode=DeliveryMode.AT_LEAST_ONCE,
        )
        assert event.metadata.source == "src"
        assert event.metadata.target == "tgt"
        assert event.metadata.workspace_id == "ws-1"
        assert event.metadata.correlation_id == "corr-1"
        assert event.priority == EventPriority.HIGH
        assert event.delivery_mode == DeliveryMode.AT_LEAST_ONCE
        bus.stop()

    def test_unsubscribe(self):
        bus = EventBus()
        bus.start()
        sub = bus.subscribe("t", callback=lambda e: None)
        assert bus.unsubscribe(sub.subscription_id) is True
        bus.stop()

    def test_event_handlers(self):
        bus = EventBus()
        bus.start()
        handled = []
        handler = lambda e: handled.append(e)
        bus.add_event_handler("test.event", handler)
        assert len(bus.get_event_handlers("test.event")) == 1
        bus.remove_event_handler("test.event", handler)
        assert len(bus.get_event_handlers("test.event")) == 0
        bus.stop()

    def test_concurrent_publish(self):
        bus = EventBus()
        bus.start()
        lock = threading.Lock()
        count = [0]

        def publish_events():
            for _ in range(10):
                bus.publish(event_type="concurrent")
                with lock:
                    count[0] += 1

        threads = [threading.Thread(target=publish_events) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert count[0] == 50
        assert bus.get_metrics()["publish_count"] == 50
        bus.stop()
