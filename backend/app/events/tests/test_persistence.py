"""Tests for persistence."""

import time
from app.events.persistence import InMemoryEventStore, EventPersistenceManager
from app.events.interfaces import Event, EventState


class TestInMemoryEventStore:
    def test_create_store(self):
        store = InMemoryEventStore()
        assert store.count() == 0

    def test_persist_event(self):
        store = InMemoryEventStore()
        event = Event()
        assert store.persist(event) is True
        assert store.count() == 1

    def test_persist_sets_state(self):
        store = InMemoryEventStore()
        event = Event()
        store.persist(event)
        assert event.state == EventState.PUBLISHED

    def test_load_event(self):
        store = InMemoryEventStore()
        event = Event()
        store.persist(event)
        retrieved = store.load(event.event_id)
        assert retrieved is not None
        assert retrieved.event_id == event.event_id

    def test_load_nonexistent(self):
        store = InMemoryEventStore()
        assert store.load("nonexistent") is None

    def test_load_range(self):
        store = InMemoryEventStore()
        events = [Event(timestamp=100 + i) for i in range(5)]
        for e in events:
            store.persist(e)
        result = store.load_range(101.0, 103.0)
        assert len(result) == 3

    def test_load_all(self):
        store = InMemoryEventStore()
        for _ in range(5):
            store.persist(Event())
        result = store.load_all()
        assert len(result) == 5

    def test_load_since(self):
        store = InMemoryEventStore()
        now = time.time()
        e1 = Event(timestamp=now - 100)
        e2 = Event(timestamp=now)
        store.persist(e1)
        store.persist(e2)
        result = store.load_since(now - 10)
        assert len(result) == 1

    def test_load_since_event(self):
        store = InMemoryEventStore()
        e1 = Event()
        e2 = Event()
        store.persist(e1)
        store.persist(e2)
        result = store.load_since_event(e1.event_id)
        assert len(result) == 1
        assert result[0].event_id == e2.event_id

    def test_load_since_event_not_found(self):
        store = InMemoryEventStore()
        store.persist(Event())
        result = store.load_since_event("nonexistent")
        assert len(result) == 0

    def test_clear(self):
        store = InMemoryEventStore()
        store.persist(Event())
        store.persist(Event())
        store.clear()
        assert store.count() == 0

    def test_to_dict(self):
        store = InMemoryEventStore()
        store.persist(Event())
        d = store.to_dict()
        assert d["event_count"] == 1


class TestEventPersistenceManager:
    def test_create_manager(self):
        mgr = EventPersistenceManager()
        assert mgr._store is not None

    def test_persist_event(self):
        mgr = EventPersistenceManager()
        event = Event()
        mgr.persist(event)
        assert mgr.count() == 1

    def test_load_event(self):
        mgr = EventPersistenceManager()
        event = Event()
        mgr.persist(event)
        loaded = mgr.load(event.event_id)
        assert loaded is not None

    def test_load_range(self):
        mgr = EventPersistenceManager()
        for i in range(5):
            mgr.persist(Event(timestamp=100 + i))
        result = mgr.load_range(101.0, 103.0)
        assert len(result) == 3

    def test_load_since(self):
        mgr = EventPersistenceManager()
        now = time.time()
        mgr.persist(Event(timestamp=now - 100))
        mgr.persist(Event(timestamp=now))
        result = mgr.load_since(now - 10)
        assert len(result) == 1

    def test_load_since_event(self):
        mgr = EventPersistenceManager()
        e1 = Event()
        e2 = Event()
        mgr.persist(e1)
        mgr.persist(e2)
        result = mgr.load_since_event(e1.event_id)
        assert len(result) == 1

    def test_auto_persist_disabled(self):
        mgr = EventPersistenceManager()
        mgr.set_auto_persist(False)
        event = Event()
        result = mgr.persist(event)
        assert result is True
        assert mgr.count() == 0

    def test_clear(self):
        mgr = EventPersistenceManager()
        mgr.persist(Event())
        mgr.persist(Event())
        mgr.clear()
        assert mgr.count() == 0

    def test_to_dict(self):
        mgr = EventPersistenceManager()
        d = mgr.to_dict()
        assert "auto_persist" in d
        assert "store" in d
