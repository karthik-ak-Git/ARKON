"""Tests for router, dispatcher, broker, publisher, subscriber, subscription."""

from app.events.router import EventRouter, RoutingRule
from app.events.dispatcher import EventDispatcher
from app.events.broker import EventBroker, BrokerConfig
from app.events.publisher import EventPublisher, PublisherConfig
from app.events.subscriber import EventSubscriber, SubscriberConfig
from app.events.subscription import SubscriptionManager
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
)


class TestEventRouter:
    def test_create(self):
        router = EventRouter()
        assert router.to_dict()["rules"] == 0

    def test_add_rule(self):
        router = EventRouter()
        rule = RoutingRule(rule_id="r1", name="test")
        router.add_rule(rule)
        assert len(router.get_rules()) == 1

    def test_route_event(self):
        router = EventRouter()
        sub = Subscription(topic="tasks")
        router.subscribe(sub)
        event = Event(metadata=EventMetadata(topic="tasks"))
        matches = router.route_event(event)
        assert len(matches) == 1

    def test_unsubscribe(self):
        router = EventRouter()
        sub = Subscription(topic="t")
        router.subscribe(sub)
        assert router.unsubscribe(sub.subscription_id) is True

    def test_clear(self):
        router = EventRouter()
        router.add_rule(RoutingRule(rule_id="r1"))
        router.clear()
        assert len(router.get_rules()) == 0


class TestEventDispatcher:
    def test_create(self):
        d = EventDispatcher()
        assert d.get_success_rate() == 0.0

    def test_dispatch_success(self):
        d = EventDispatcher()
        event = Event()
        called = []
        sub = Subscription(topic="t", callback=lambda e: called.append(e))
        result = d.dispatch(event, sub)
        assert result.success is True
        assert len(called) == 1

    def test_dispatch_no_callback(self):
        d = EventDispatcher()
        event = Event()
        sub = Subscription(topic="t")
        result = d.dispatch(event, sub)
        assert result.success is False

    def test_dispatch_batch(self):
        d = EventDispatcher()
        event = Event()
        subs = [Subscription(topic="t", callback=lambda e: None) for _ in range(3)]
        results = d.dispatch_batch(event, subs)
        assert len(results) == 3

    def test_history(self):
        d = EventDispatcher()
        event = Event()
        sub = Subscription(topic="t", callback=lambda e: None)
        d.dispatch(event, sub)
        assert len(d.get_history()) == 1

    def test_success_rate(self):
        d = EventDispatcher()
        event = Event()
        sub = Subscription(topic="t", callback=lambda e: None)
        d.dispatch(event, sub)
        assert d.get_success_rate() == 1.0


class TestEventBroker:
    def test_create(self):
        broker = EventBroker()
        assert broker.to_dict()["is_running"] is False

    def test_start_stop(self):
        broker = EventBroker()
        broker.start()
        assert broker.to_dict()["is_running"] is True
        broker.stop()
        assert broker.to_dict()["is_running"] is False

    def test_publish_consume(self):
        broker = EventBroker()
        broker.start()
        event = Event()
        broker.publish(event, topic="t1")
        consumed = broker.consume("t1")
        assert consumed is not None

    def test_consume_empty(self):
        broker = EventBroker()
        broker.start()
        assert broker.consume("empty") is None

    def test_acknowledge(self):
        broker = EventBroker()
        broker.start()
        event = Event()
        broker.publish(event, topic="t")
        broker.consume("t")
        assert broker.acknowledge(event.event_id, "t") is True

    def test_retry(self):
        broker = EventBroker()
        broker.start()
        event = Event()
        broker.publish(event, topic="t")
        broker.consume("t")
        assert broker.retry(event, "t") is True

    def test_max_retries_dead_letter(self):
        broker = EventBroker(BrokerConfig(max_retries=2))
        broker.start()
        event = Event()
        broker.publish(event, topic="t")
        broker.consume("t")
        broker.retry(event, "t")
        broker.consume("t")
        broker.retry(event, "t")
        broker.consume("t")
        result = broker.retry(event, "t")
        assert result is False
        assert len(broker.get_dead_letters()) == 1

    def test_peek(self):
        broker = EventBroker()
        broker.start()
        broker.publish(Event(), topic="t")
        broker.publish(Event(), topic="t")
        peeked = broker.peek("t", limit=1)
        assert len(peeked) == 1

    def test_get_metrics(self):
        broker = EventBroker()
        broker.start()
        broker.publish(Event(), topic="t")
        m = broker.get_metrics()
        assert m["published"] == 1

    def test_clear(self):
        broker = EventBroker()
        broker.start()
        broker.publish(Event(), topic="t")
        broker.clear("t")
        assert broker.get_queue_size("t") == 0


class TestEventPublisher:
    def test_create(self):
        p = EventPublisher()
        assert p.get_publish_count() == 0

    def test_publish(self):
        p = EventPublisher()
        event = p.publish(event_type="test", source="src")
        assert event.metadata.source == "src"
        assert p.get_publish_count() == 1

    def test_publish_many(self):
        p = EventPublisher()
        events = [Event() for _ in range(3)]
        p.publish_many(events)
        assert p.get_publish_count() == 3

    def test_batching(self):
        p = EventPublisher(PublisherConfig(enable_batching=True, batch_size=3))
        p.publish(event_type="a")
        p.publish(event_type="b")
        assert len(p.get_pending_batch()) == 2
        p.publish(event_type="c")
        assert len(p.get_pending_batch()) == 0

    def test_flush(self):
        p = EventPublisher(PublisherConfig(enable_batching=True))
        p.publish(event_type="a")
        p.flush()
        assert p.get_publish_count() == 1

    def test_to_dict(self):
        p = EventPublisher()
        d = p.to_dict()
        assert d["published_count"] == 0


class TestEventSubscriber:
    def test_create(self):
        s = EventSubscriber("s1")
        assert s.subscriber_id == "s1"

    def test_subscribe(self):
        s = EventSubscriber("s1")
        sub = s.subscribe("tasks")
        assert sub.topic == "tasks"

    def test_receive(self):
        s = EventSubscriber("s1")
        s.subscribe("t")
        event = Event()
        assert s.receive(event) is True
        assert s.get_receive_count() == 1

    def test_acknowledge(self):
        s = EventSubscriber("s1", SubscriberConfig(auto_ack=False))
        s.subscribe("t")
        event = Event()
        s.receive(event)
        assert s.acknowledge(event.event_id) is True

    def test_nack(self):
        s = EventSubscriber("s1", SubscriberConfig(auto_ack=False))
        s.subscribe("t")
        event = Event()
        s.receive(event)
        assert s.nack(event.event_id) is True

    def test_to_dict(self):
        s = EventSubscriber("s1")
        d = s.to_dict()
        assert d["subscriber_id"] == "s1"


class TestSubscriptionManager:
    def test_create(self):
        mgr = SubscriptionManager()
        assert mgr.count() == 0

    def test_create_subscription(self):
        mgr = SubscriptionManager()
        sub = mgr.create_subscription("user1", topic="tasks")
        assert sub.topic == "tasks"
        assert mgr.count() == 1

    def test_remove(self):
        mgr = SubscriptionManager()
        sub = mgr.create_subscription("u", topic="t")
        assert mgr.remove_subscription(sub.subscription_id) is True
        assert mgr.count() == 0

    def test_get_by_topic(self):
        mgr = SubscriptionManager()
        mgr.create_subscription("u1", topic="tasks")
        mgr.create_subscription("u2", topic="tasks")
        subs = mgr.get_subscriptions_for_topic("tasks")
        assert len(subs) == 2

    def test_get_by_channel(self):
        mgr = SubscriptionManager()
        mgr.create_subscription("u1", topic="t", channel=ChannelType.SYSTEM)
        subs = mgr.get_subscriptions_for_channel(ChannelType.SYSTEM)
        assert len(subs) == 1

    def test_find_matching(self):
        mgr = SubscriptionManager()
        mgr.create_subscription("u1", topic="tasks")
        event = Event(metadata=EventMetadata(topic="tasks"))
        matches = mgr.find_matching(event)
        assert len(matches) == 1

    def test_clear(self):
        mgr = SubscriptionManager()
        mgr.create_subscription("u", topic="t")
        mgr.clear()
        assert mgr.count() == 0

    def test_to_dict(self):
        mgr = SubscriptionManager()
        d = mgr.to_dict()
        assert d["total"] == 0
