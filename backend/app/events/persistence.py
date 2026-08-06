"""Event persistence layer."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from app.events.exceptions import PersistenceError
from app.events.interfaces import Event, EventState, IEventPersistence


@dataclass
class InMemoryEventStore:
    """In-memory event store for persistence."""

    _events: dict[str, Event] = field(default_factory=dict)
    _timeline: list[str] = field(default_factory=list)
    _max_events: int = 10000
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def persist(self, event: Event) -> bool:
        """Persist an event."""
        with self._lock:
            try:
                event.state = EventState.PUBLISHED
                self._events[event.event_id] = event
                self._timeline.append(event.event_id)
                self._evict_old()
                return True
            except Exception as e:
                raise PersistenceError(f"Failed to persist event: {e}")

    def load(self, event_id: str) -> Event | None:
        """Load an event by ID."""
        return self._events.get(event_id)

    def load_range(self, start_time: float, end_time: float) -> list[Event]:
        """Load events within a time range."""
        result = []
        for event_id in self._timeline:
            event = self._events.get(event_id)
            if event and start_time <= event.timestamp <= end_time:
                result.append(event)
        return result

    def load_all(self) -> list[Event]:
        """Load all events in order."""
        result = []
        for event_id in self._timeline:
            event = self._events.get(event_id)
            if event:
                result.append(event)
        return result

    def load_since(self, timestamp: float) -> list[Event]:
        """Load events since a timestamp."""
        return self.load_range(timestamp, float("inf"))

    def load_since_event(self, event_id: str) -> list[Event]:
        """Load events since a specific event."""
        try:
            idx = self._timeline.index(event_id)
            result = []
            for eid in self._timeline[idx + 1:]:
                event = self._events.get(eid)
                if event:
                    result.append(event)
            return result
        except ValueError:
            return []

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        """Clear all persisted events."""
        with self._lock:
            self._events.clear()
            self._timeline.clear()

    def _evict_old(self) -> None:
        """Evict oldest events when over limit."""
        while len(self._events) > self._max_events:
            oldest_id = self._timeline.pop(0)
            self._events.pop(oldest_id, None)

    def to_dict(self) -> dict:
        return {
            "event_count": len(self._events),
            "timeline_length": len(self._timeline),
            "max_events": self._max_events,
        }


class EventPersistenceManager:
    """Manages event persistence with configurable backends."""

    def __init__(self, store: IEventPersistence | None = None) -> None:
        self._store = store or InMemoryEventStore()
        self._auto_persist: bool = True
        self._persist_filter: set[EventState] | None = None

    def persist(self, event: Event) -> bool:
        """Persist an event if conditions are met."""
        if not self._auto_persist:
            return True
        if self._persist_filter and event.state not in self._persist_filter:
            return True
        return self._store.persist(event)

    def load(self, event_id: str) -> Event | None:
        return self._store.load(event_id)

    def load_range(self, start_time: float, end_time: float) -> list[Event]:
        return self._store.load_range(start_time, end_time)

    def load_since(self, timestamp: float) -> list[Event]:
        if hasattr(self._store, "load_since"):
            return self._store.load_since(timestamp)
        return self._store.load_range(timestamp, float("inf"))

    def load_since_event(self, event_id: str) -> list[Event]:
        if hasattr(self._store, "load_since_event"):
            return self._store.load_since_event(event_id)
        return []

    def clear(self) -> None:
        self._store.clear()

    def set_auto_persist(self, enabled: bool) -> None:
        self._auto_persist = enabled

    def count(self) -> int:
        if hasattr(self._store, "count"):
            return self._store.count()
        return 0

    def to_dict(self) -> dict:
        return {
            "auto_persist": self._auto_persist,
            "store": self._store.to_dict() if hasattr(self._store, "to_dict") else {},
        }
