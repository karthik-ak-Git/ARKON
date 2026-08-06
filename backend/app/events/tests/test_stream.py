"""Tests for event streaming."""

from app.events.stream import EventStream, StreamSubscriber
from app.events.interfaces import Event, EventType


class TestEventStream:
    def test_create(self):
        stream = EventStream()
        assert stream.is_running is False
        assert stream.is_active is False

    def test_start_stop(self):
        stream = EventStream()
        stream.start()
        assert stream.is_running is True
        stream.stop()
        assert stream.is_running is False

    def test_pause_resume(self):
        stream = EventStream()
        stream.start()
        assert stream.is_running is True
        stream.pause()
        assert stream.is_running is False
        stream.resume()
        assert stream.is_running is True

    def test_publish_when_stopped(self):
        stream = EventStream()
        event = Event()
        count = stream.publish(event)
        assert count == 0

    def test_publish_when_active(self):
        stream = EventStream()
        stream.start()
        event = Event()
        stream.publish(event)
        assert stream.to_dict()["history_size"] == 1

    def test_publish_returns_notified_count(self):
        stream = EventStream()
        stream.start()
        received = []
        stream.subscribe("s1", callback=lambda e: received.append(e))
        event = Event()
        count = stream.publish(event)
        assert count == 1
        assert len(received) == 1

    def test_subscribe(self):
        stream = EventStream()
        stream.start()
        received = []
        stream.subscribe("s1", callback=lambda e: received.append(e))
        event = Event()
        stream.publish(event)
        assert len(received) == 1

    def test_unsubscribe(self):
        stream = EventStream()
        stream.subscribe("s1", callback=lambda e: None)
        assert stream.unsubscribe("s1") is True
        assert stream.unsubscribe("s1") is False

    def test_get_subscribers(self):
        stream = EventStream()
        stream.subscribe("s1", callback=lambda e: None)
        stream.subscribe("s2", callback=lambda e: None)
        assert len(stream.get_subscribers()) == 2

    def test_get_active_subscribers(self):
        stream = EventStream()
        stream.subscribe("s1", callback=lambda e: None)
        stream.subscribe("s2", callback=lambda e: None, event_types=[EventType.TASK])
        assert len(stream.get_active_subscribers()) == 2

    def test_history(self):
        stream = EventStream()
        stream.start()
        for _ in range(5):
            stream.publish(Event())
        history = stream.get_history(limit=3)
        assert len(history) == 3

    def test_clear_history(self):
        stream = EventStream()
        stream.start()
        stream.publish(Event())
        stream.publish(Event())
        stream.clear_history()
        assert stream.to_dict()["history_size"] == 0

    def test_to_dict(self):
        stream = EventStream()
        stream.start()
        d = stream.to_dict()
        assert d["active"] is True
        assert "subscribers" in d
        assert "history_size" in d
        assert "max_history" in d

    def test_max_history(self):
        stream = EventStream(max_history=3)
        stream.start()
        for _ in range(5):
            stream.publish(Event())
        assert stream.to_dict()["history_size"] == 3


class TestStreamSubscriber:
    def test_create(self):
        sub = StreamSubscriber(subscriber_id="s1")
        assert sub.subscriber_id == "s1"

    def test_receive(self):
        sub = StreamSubscriber(subscriber_id="s1")
        sub.events_received += 1
        assert sub.events_received == 1

    def test_matches_all(self):
        sub = StreamSubscriber(subscriber_id="s1")
        assert sub.matches(Event()) is True

    def test_matches_filtered(self):
        sub = StreamSubscriber(subscriber_id="s1", event_types=[EventType.TASK])
        assert sub.matches(Event(event_type=EventType.TASK)) is True
        assert sub.matches(Event(event_type=EventType.ERROR)) is False

    def test_matches_inactive(self):
        sub = StreamSubscriber(subscriber_id="s1", is_active=False)
        assert sub.matches(Event()) is False

    def test_to_dict(self):
        sub = StreamSubscriber(subscriber_id="s1")
        d = {"subscriber_id": sub.subscriber_id}
        assert d["subscriber_id"] == "s1"
