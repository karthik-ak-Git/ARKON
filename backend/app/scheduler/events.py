"""Scheduler events."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any


class SchedulerEventType(enum.Enum):
    """Scheduler event types."""

    TASK_QUEUED = "task_queued"
    TASK_SCHEDULED = "task_scheduled"
    TASK_DEFERRED = "task_deferred"
    TASK_REJECTED = "task_rejected"
    TASK_DISPATCHED = "task_dispatched"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    PRIORITY_CHANGED = "priority_changed"
    SCHEDULER_PAUSED = "scheduler_paused"
    SCHEDULER_RESUMED = "scheduler_resumed"
    SCHEDULER_OVERLOADED = "scheduler_overloaded"
    SCHEDULER_RECOVERED = "scheduler_recovered"
    PREEMPTION_OCCURRED = "preemption_occurred"
    BACKPRESSURE_APPLIED = "backpressure_applied"
    BACKPRESSURE_RELEASED = "backpressure_released"


SCHEDULER_EVENT_TYPES = {e.value for e in SchedulerEventType}


@dataclass
class SchedulerEvent:
    """A scheduler event."""

    event_type: SchedulerEventType
    task_id: str | None = None
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventEmitter:
    """Collects scheduler events."""

    _events: list[SchedulerEvent] = field(default_factory=list)
    _listeners: dict[SchedulerEventType, list] = field(default_factory=dict)

    def emit(self, event_type: SchedulerEventType, task_id: str | None = None, **data: Any) -> SchedulerEvent:
        event = SchedulerEvent(event_type=event_type, task_id=task_id, data=data)
        self._events.append(event)
        for cb in self._listeners.get(event_type, []):
            cb(event)
        return event

    def on(self, event_type: SchedulerEventType, callback: Any) -> None:
        self._listeners.setdefault(event_type, []).append(callback)

    def get_events(self, event_type: SchedulerEventType | None = None) -> list[SchedulerEvent]:
        if event_type is None:
            return list(self._events)
        return [e for e in self._events if e.event_type == event_type]

    def clear(self) -> None:
        self._events.clear()
