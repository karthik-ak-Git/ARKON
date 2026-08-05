"""Timeline tracking for task execution history."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TimelineEntry:
    """A single event in the task timeline."""

    task_id: str
    event: str
    timestamp: float = field(default_factory=time.time)
    data: dict = field(default_factory=dict)


@dataclass
class TaskTimeline:
    """Complete timeline for a single task."""

    task_id: str
    entries: list[TimelineEntry] = field(default_factory=list)

    @property
    def first_event(self) -> float | None:
        return self.entries[0].timestamp if self.entries else None

    @property
    def last_event(self) -> float | None:
        return self.entries[-1].timestamp if self.entries else None

    @property
    def total_duration(self) -> float | None:
        if len(self.entries) < 2:
            return None
        return self.entries[-1].timestamp - self.entries[0].timestamp

    def add_entry(self, event: str, data: dict | None = None) -> None:
        self.entries.append(TimelineEntry(task_id=self.task_id, event=event, data=data or {}))

    def get_entries_by_event(self, event: str) -> list[TimelineEntry]:
        return [e for e in self.entries if e.event == event]


class Timeline:
    """Global timeline tracking all task events."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._timelines: dict[str, TaskTimeline] = {}
        self._global_entries: list[TimelineEntry] = []

    def record(self, task_id: str, event: str, data: dict | None = None) -> None:
        entry = TimelineEntry(task_id=task_id, event=event, data=data or {})
        self._global_entries.append(entry)

        if task_id not in self._timelines:
            self._timelines[task_id] = TaskTimeline(task_id=task_id)
        self._timelines[task_id].add_entry(event, data)

        if len(self._global_entries) > self._max_entries:
            self._global_entries = self._global_entries[-self._max_entries:]

    def get_task_timeline(self, task_id: str) -> TaskTimeline | None:
        return self._timelines.get(task_id)

    def get_task_duration(self, task_id: str) -> float | None:
        timeline = self._timelines.get(task_id)
        return timeline.total_duration if timeline else None

    def get_recent_events(self, count: int = 10) -> list[TimelineEntry]:
        return self._global_entries[-count:]

    def get_events_by_task(self, task_id: str) -> list[TimelineEntry]:
        return [e for e in self._global_entries if e.task_id == task_id]

    def get_task_count(self) -> int:
        return len(self._timelines)

    def get_entry_count(self) -> int:
        return len(self._global_entries)

    def clear_task(self, task_id: str) -> None:
        self._timelines.pop(task_id, None)
        self._global_entries = [e for e in self._global_entries if e.task_id != task_id]

    def clear(self) -> None:
        self._timelines.clear()
        self._global_entries.clear()

    def to_dict(self) -> dict:
        return {
            "task_count": self.get_task_count(),
            "entry_count": self.get_entry_count(),
            "recent_events": [
                {"task_id": e.task_id, "event": e.event, "timestamp": e.timestamp}
                for e in self.get_recent_events(10)
            ],
        }
