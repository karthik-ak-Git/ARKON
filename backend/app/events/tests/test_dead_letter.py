"""Tests for dead letter queue."""

from app.events.dead_letter import DeadLetterQueue
from app.events.interfaces import Event, EventState


class TestDeadLetterQueue:
    def test_create(self):
        dlq = DeadLetterQueue()
        assert dlq.count() == 0

    def test_add(self):
        dlq = DeadLetterQueue()
        event = Event(event_type="test")
        dlq.add(event, error="failed")
        assert dlq.count() == 1

    def test_retry_success(self):
        dlq = DeadLetterQueue()
        event = Event(event_type="test")
        dlq.add(event, error="timeout")
        result = dlq.retry_entry(event.event_id)
        assert result is not None
        assert dlq.count() == 1

    def test_retry_nonexistent(self):
        dlq = DeadLetterQueue()
        assert dlq.retry_entry("nonexistent") is None

    def test_list_retriable(self):
        dlq = DeadLetterQueue()
        dlq.add(Event(event_type="a"), error="timeout", max_retries=3)
        dlq.add(Event(event_type="b"), error="permanent", max_retries=0)
        assert len(dlq.list_retriable()) == 1

    def test_list_permanent_failures(self):
        dlq = DeadLetterQueue()
        dlq.add(Event(event_type="a"), error="timeout", max_retries=3)
        dlq.add(Event(event_type="b"), error="permanent", max_retries=0)
        assert len(dlq.list_permanent_failures()) == 1

    def test_clear(self):
        dlq = DeadLetterQueue()
        dlq.add(Event(event_type="t"), error="r")
        dlq.clear()
        assert dlq.count() == 0

    def test_to_dict(self):
        dlq = DeadLetterQueue()
        dlq.add(Event(event_type="t"), error="r")
        d = dlq.to_dict()
        assert d["count"] == 1

    def test_remove(self):
        dlq = DeadLetterQueue()
        event = Event(event_type="test")
        dlq.add(event, error="r")
        assert dlq.remove(event.event_id) is True
        assert dlq.count() == 0

    def test_get(self):
        dlq = DeadLetterQueue()
        event = Event(event_type="test")
        dlq.add(event, error="r")
        entry = dlq.get(event.event_id)
        assert entry is not None
        assert entry.error == "r"

    def test_list_all(self):
        dlq = DeadLetterQueue()
        dlq.add(Event(event_type="a"), error="1")
        dlq.add(Event(event_type="b"), error="2")
        assert len(dlq.list_all()) == 2
