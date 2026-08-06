"""Dead letter queue for failed events."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.exceptions import DeadLetterError
from app.events.interfaces import Event, EventState


@dataclass
class DeadLetterEntry:
    """An entry in the dead letter queue."""

    event: Event
    error: str = ""
    failed_at: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    last_retry_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event.event_id,
            "event_type": self.event.event_type.value,
            "error": self.error,
            "failed_at": self.failed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry,
        }


class DeadLetterQueue:
    """Manages failed events for retry or inspection."""

    def __init__(self, max_size: int = 1000) -> None:
        self._entries: dict[str, DeadLetterEntry] = {}
        self._order: list[str] = []
        self._max_size = max_size
        self._lock = threading.Lock()
        self._retry_callback: Callable[[Event], Any] | None = None

    def add(self, event: Event, error: str = "", max_retries: int = 3) -> DeadLetterEntry:
        """Add a failed event to the dead letter queue."""
        with self._lock:
            if event.event_id in self._entries:
                entry = self._entries[event.event_id]
                entry.retry_count += 1
                entry.last_retry_at = time.time()
                entry.error = error
                return entry

            if len(self._entries) >= self._max_size:
                self._evict_oldest()

            event.state = EventState.DEAD_LETTER
            entry = DeadLetterEntry(
                event=event,
                error=error,
                max_retries=max_retries,
            )
            self._entries[event.event_id] = entry
            self._order.append(event.event_id)
            return entry

    def get(self, event_id: str) -> DeadLetterEntry | None:
        return self._entries.get(event_id)

    def remove(self, event_id: str) -> bool:
        """Remove an entry from the dead letter queue."""
        with self._lock:
            if event_id in self._entries:
                del self._entries[event_id]
                self._order.remove(event_id)
                return True
            return False

    def retry_entry(self, event_id: str) -> Event | None:
        """Retry a dead lettered event."""
        entry = self._entries.get(event_id)
        if not entry or not entry.can_retry:
            return None
        entry.retry_count += 1
        entry.last_retry_at = time.time()
        event = entry.event
        if self._retry_callback:
            try:
                self._retry_callback(event)
            except Exception:
                pass
        return event

    def set_retry_callback(self, callback: Callable[[Event], Any]) -> None:
        self._retry_callback = callback

    def list_all(self) -> list[DeadLetterEntry]:
        """List all entries in order."""
        return [self._entries[eid] for eid in self._order if eid in self._entries]

    def list_retriable(self) -> list[DeadLetterEntry]:
        """List entries that can be retried."""
        return [e for e in self.list_all() if e.can_retry]

    def list_permanent_failures(self) -> list[DeadLetterEntry]:
        """List entries that have exceeded max retries."""
        return [e for e in self.list_all() if not e.can_retry]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        """Clear all dead letter entries."""
        with self._lock:
            self._entries.clear()
            self._order.clear()

    def _evict_oldest(self) -> None:
        """Evict the oldest entry."""
        if self._order:
            oldest_id = self._order.pop(0)
            self._entries.pop(oldest_id, None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self._entries),
            "max_size": self._max_size,
            "retriable": len(self.list_retriable()),
            "permanent_failures": len(self.list_permanent_failures()),
        }
