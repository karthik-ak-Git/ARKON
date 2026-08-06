"""Tests for event filtering."""

import time
from app.events.filter import EventFilter
from app.events.interfaces import Event, EventMetadata, ChannelType, EventPriority, EventState, EventType


class TestEventFilter:
    def test_event_type_filter(self):
        f = EventFilter(event_types=["task.created", "task.completed"])
        e1 = Event(event_type="task.created", metadata=EventMetadata(topic="tasks"))
        e2 = Event(event_type="resource.allocated", metadata=EventMetadata(topic="resources"))
        assert f.matches(e1) is True
        assert f.matches(e2) is False

    def test_topic_filter(self):
        f = EventFilter(topics=["tasks"])
        e1 = Event(metadata=EventMetadata(topic="tasks"))
        e2 = Event(metadata=EventMetadata(topic="resources"))
        assert f.matches(e1) is True
        assert f.matches(e2) is False

    def test_channel_filter(self):
        f = EventFilter(channels=[ChannelType.SYSTEM, ChannelType.AGENT])
        e1 = Event(metadata=EventMetadata(channel=ChannelType.SYSTEM))
        e2 = Event(metadata=EventMetadata(channel=ChannelType.SCHEDULER))
        assert f.matches(e1) is True
        assert f.matches(e2) is False

    def test_source_filter(self):
        f = EventFilter(sources=["scheduler"])
        e1 = Event(metadata=EventMetadata(source="scheduler"))
        e2 = Event(metadata=EventMetadata(source="runtime"))
        assert f.matches(e1) is True
        assert f.matches(e2) is False

    def test_regex_filter(self):
        f = EventFilter(event_type_regex=r"^task\.")
        e1 = Event(event_type="task.created", metadata=EventMetadata(topic="t"))
        e2 = Event(event_type="resource.allocated", metadata=EventMetadata(topic="t"))
        assert f.matches(e1) is True
        assert f.matches(e2) is False

    def test_time_range_filter(self):
        now = time.time()
        f = EventFilter(min_timestamp=now - 10, max_timestamp=now + 10)
        e1 = Event(timestamp=now)
        e2 = Event(timestamp=now - 100)
        assert f.matches(e1) is True
        assert f.matches(e2) is False

    def test_combined_filters(self):
        f = EventFilter(
            event_types=["task.created"],
            topics=["tasks"],
            channels=[ChannelType.SYSTEM],
        )
        e1 = Event(event_type="task.created", metadata=EventMetadata(topic="tasks", channel=ChannelType.SYSTEM))
        e2 = Event(event_type="task.created", metadata=EventMetadata(topic="other", channel=ChannelType.SYSTEM))
        assert f.matches(e1) is True
        assert f.matches(e2) is False

    def test_empty_filter_matches_all(self):
        f = EventFilter()
        e1 = Event(event_type="anything")
        assert f.matches(e1) is True
