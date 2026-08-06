"""Event filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.interfaces import (
    ChannelType,
    Event,
    EventPriority,
    EventType,
    IEventFilter,
)


@dataclass
class EventTypeFilter(IEventFilter):
    """Filter by event type."""

    event_types: list[EventType] = field(default_factory=list)

    def matches(self, event: Event) -> bool:
        if not self.event_types:
            return True
        event_type_val = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
        for et in self.event_types:
            et_val = et.value if hasattr(et, 'value') else str(et)
            if event_type_val == et_val:
                return True
        return False

    def get_name(self) -> str:
        return "event_type_filter"


@dataclass
class TopicFilter(IEventFilter):
    """Filter by topic with pattern matching."""

    topic_pattern: str = ""

    def matches(self, event: Event) -> bool:
        if not self.topic_pattern:
            return True
        if self.topic_pattern == "**":
            return True
        return self._match(self.topic_pattern, event.metadata.topic)

    def _match(self, pattern: str, topic: str) -> bool:
        pattern_parts = pattern.split(".")
        topic_parts = topic.split(".")
        return self._match_parts(pattern_parts, topic_parts)

    def _match_parts(self, pattern_parts: list[str], topic_parts: list[str]) -> bool:
        pi = 0
        ti = 0
        while pi < len(pattern_parts) and ti < len(topic_parts):
            if pattern_parts[pi] == "**":
                return True
            if pattern_parts[pi] == "*":
                pi += 1
                ti += 1
            elif pattern_parts[pi] == topic_parts[ti]:
                pi += 1
                ti += 1
            else:
                return False
        return pi == len(pattern_parts) and ti == len(topic_parts)

    def get_name(self) -> str:
        return "topic_filter"


@dataclass
class ChannelFilter(IEventFilter):
    """Filter by channel type."""

    channels: list[ChannelType] = field(default_factory=list)

    def matches(self, event: Event) -> bool:
        if not self.channels:
            return True
        return event.metadata.channel in self.channels

    def get_name(self) -> str:
        return "channel_filter"


@dataclass
class PriorityFilter(IEventFilter):
    """Filter by minimum priority."""

    min_priority: EventPriority = EventPriority.NORMAL

    def matches(self, event: Event) -> bool:
        return event.priority.value <= self.min_priority.value

    def get_name(self) -> str:
        return "priority_filter"


@dataclass
class WorkspaceFilter(IEventFilter):
    """Filter by workspace ID."""

    workspace_ids: list[str] = field(default_factory=list)

    def matches(self, event: Event) -> bool:
        if not self.workspace_ids:
            return True
        return event.metadata.workspace_id in self.workspace_ids

    def get_name(self) -> str:
        return "workspace_filter"


@dataclass
class SourceFilter(IEventFilter):
    """Filter by event source."""

    sources: list[str] = field(default_factory=list)

    def matches(self, event: Event) -> bool:
        if not self.sources:
            return True
        return event.metadata.source in self.sources

    def get_name(self) -> str:
        return "source_filter"


@dataclass
class TagFilter(IEventFilter):
    """Filter by tags (all tags must match)."""

    required_tags: list[str] = field(default_factory=list)

    def matches(self, event: Event) -> bool:
        if not self.required_tags:
            return True
        return all(tag in event.metadata.tags for tag in self.required_tags)

    def get_name(self) -> str:
        return "tag_filter"


@dataclass
class PredicateFilter(IEventFilter):
    """Filter using a custom predicate function."""

    predicate: Callable[[Event], bool] = field(default_factory=lambda: lambda e: True)
    name: str = "predicate_filter"

    def matches(self, event: Event) -> bool:
        try:
            return self.predicate(event)
        except Exception:
            return False

    def get_name(self) -> str:
        return self.name


@dataclass
class CompositeFilter(IEventFilter):
    """Combine multiple filters with AND logic."""

    filters: list[IEventFilter] = field(default_factory=list)
    require_all: bool = True

    def matches(self, event: Event) -> bool:
        if not self.filters:
            return True
        if self.require_all:
            return all(f.matches(event) for f in self.filters)
        return any(f.matches(event) for f in self.filters)

    def get_name(self) -> str:
        return "composite_filter"


@dataclass
class RegexFilter(IEventFilter):
    """Filter by regex pattern on payload fields."""

    field_name: str = ""
    pattern: str = ""

    def matches(self, event: Event) -> bool:
        if not self.field_name or not self.pattern:
            return True
        if self.field_name == "event_type":
            value = str(event.event_type.value) if hasattr(event.event_type, 'value') else str(event.event_type)
        else:
            value = event.payload.get(self.field_name, "")
        if not isinstance(value, str):
            value = str(value)
        try:
            return bool(re.search(self.pattern, value))
        except re.error:
            return False

    def get_name(self) -> str:
        return "regex_filter"


@dataclass
class TimeRangeFilter(IEventFilter):
    """Filter by event timestamp range."""

    start_time: float = 0.0
    end_time: float = float("inf")

    def matches(self, event: Event) -> bool:
        return self.start_time <= event.timestamp <= self.end_time

    def get_name(self) -> str:
        return "time_range_filter"


class EventFilter:
    """Combined event filter."""

    def __init__(
        self,
        event_types: list[str] | None = None,
        topics: list[str] | None = None,
        channels: list[ChannelType] | None = None,
        min_priority: EventPriority | None = None,
        max_priority: EventPriority | None = None,
        sources: list[str] | None = None,
        states: list[Any] | None = None,
        event_type_regex: str = "",
        min_timestamp: float | None = None,
        max_timestamp: float | None = None,
    ) -> None:
        self._filters: list[IEventFilter] = []
        if event_types:
            self._filters.append(EventTypeFilter(event_types=event_types))
        if topics:
            for t in topics:
                self._filters.append(TopicFilter(topic_pattern=t))
        if channels:
            self._filters.append(ChannelFilter(channels=channels))
        if min_priority is not None:
            self._filters.append(PriorityFilter(min_priority=min_priority))
        if sources:
            self._filters.append(SourceFilter(sources=sources))
        if event_type_regex:
            self._filters.append(RegexFilter(field_name="event_type", pattern=event_type_regex))
        if min_timestamp is not None or max_timestamp is not None:
            self._filters.append(TimeRangeFilter(
                start_time=min_timestamp or 0.0,
                end_time=max_timestamp or float("inf"),
            ))

    def matches(self, event: Event) -> bool:
        return all(f.matches(event) for f in self._filters)

    def add_filter(self, f: IEventFilter) -> None:
        self._filters.append(f)

    def get_filters(self) -> list[IEventFilter]:
        return list(self._filters)


def create_filter(filter_type: str, **kwargs: Any) -> IEventFilter:
    """Factory for creating filters."""
    filters: dict[str, type[IEventFilter]] = {
        "event_type": EventTypeFilter,
        "topic": TopicFilter,
        "channel": ChannelFilter,
        "priority": PriorityFilter,
        "workspace": WorkspaceFilter,
        "source": SourceFilter,
        "tag": TagFilter,
        "predicate": PredicateFilter,
        "composite": CompositeFilter,
        "regex": RegexFilter,
        "time_range": TimeRangeFilter,
    }
    filter_class = filters.get(filter_type)
    if filter_class is None:
        raise ValueError(f"Unknown filter type: {filter_type}")
    return filter_class(**kwargs)
