"""Live event streaming."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.interfaces import Event, EventType


@dataclass
class StreamSubscriber:
    """A subscriber to a live event stream."""

    subscriber_id: str = ""
    callback: Callable[[Event], Any] | None = None
    event_types: list[EventType] | None = None
    is_active: bool = True
    events_received: int = 0
    created_at: float = field(default_factory=time.time)

    def matches(self, event: Event) -> bool:
        if not self.is_active:
            return False
        if self.event_types is None:
            return True
        return event.event_type in self.event_types


class EventStream:
    """Provides live event streaming to subscribers."""

    def __init__(self, max_history: int = 1000) -> None:
        self._subscribers: dict[str, StreamSubscriber] = {}
        self._history: list[Event] = []
        self._max_history = max_history
        self._lock = threading.Lock()
        self._is_active = False

    def subscribe(
        self,
        subscriber_id: str,
        callback: Callable[[Event], Any],
        event_types: list[EventType] | None = None,
    ) -> None:
        """Subscribe to the event stream."""
        with self._lock:
            self._subscribers[subscriber_id] = StreamSubscriber(
                subscriber_id=subscriber_id,
                callback=callback,
                event_types=event_types,
            )

    def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from the event stream."""
        with self._lock:
            if subscriber_id in self._subscribers:
                del self._subscribers[subscriber_id]
                return True
            return False

    def publish(self, event: Event) -> int:
        """Publish an event to all matching subscribers. Returns number of subscribers notified."""
        if not self._is_active:
            return 0

        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        notified = 0
        for subscriber in list(self._subscribers.values()):
            if subscriber.matches(event):
                try:
                    if subscriber.callback:
                        result = subscriber.callback(event)
                        if hasattr(result, "__await__"):
                            pass
                    subscriber.events_received += 1
                    notified += 1
                except Exception:
                    pass
        return notified

    def get_history(self, limit: int = 100) -> list[Event]:
        """Get recent event history."""
        return list(self._history[-limit:])

    def get_subscribers(self) -> list[StreamSubscriber]:
        return list(self._subscribers.values())

    def get_active_subscribers(self) -> list[StreamSubscriber]:
        return [s for s in self._subscribers.values() if s.is_active]

    def pause(self) -> None:
        self._is_active = False

    def resume(self) -> None:
        self._is_active = True

    def start(self) -> None:
        self._is_active = True

    def stop(self) -> None:
        self._is_active = False

    @property
    def is_running(self) -> bool:
        return self._is_active

    @property
    def is_active(self) -> bool:
        return self._is_active

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "subscribers": len(self._subscribers),
            "active": self._is_active,
            "history_size": len(self._history),
            "max_history": self._max_history,
        }
