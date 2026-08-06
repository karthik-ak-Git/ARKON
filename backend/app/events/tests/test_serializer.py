"""Tests for serializer."""

import json
from app.events.serializer import EventSerializer
from app.events.interfaces import Event, EventMetadata, ChannelType, EventType


class TestEventSerializer:
    def test_serialize_event(self):
        serializer = EventSerializer()
        event = Event(
            event_type=EventType.TASK,
            payload={"key": "value"},
            metadata=EventMetadata(source="test", channel=ChannelType.SYSTEM),
        )
        data = serializer.serialize(event)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_deserialize_event(self):
        serializer = EventSerializer()
        event = Event(
            event_type=EventType.TASK,
            payload={"key": "value"},
            metadata=EventMetadata(source="test"),
        )
        data = serializer.serialize(event)
        restored = serializer.deserialize(data)
        assert restored.event_type == event.event_type
        assert restored.payload == event.payload

    def test_roundtrip_preserves_metadata(self):
        serializer = EventSerializer()
        event = Event(
            event_type=EventType.TASK,
            metadata=EventMetadata(source="src", topic="t1"),
        )
        data = serializer.serialize(event)
        restored = serializer.deserialize(data)
        assert restored.metadata.source == "src"
        assert restored.metadata.topic == "t1"

    def test_to_dict_roundtrip(self):
        serializer = EventSerializer()
        event = Event(event_type=EventType.TASK, payload={"a": 1})
        d = serializer.to_dict(event)
        restored = serializer.from_dict(d)
        assert restored.event_type == event.event_type
        assert restored.payload == event.payload

    def test_to_json(self):
        serializer = EventSerializer()
        event = Event(event_type=EventType.TASK, payload={"x": 42})
        j = serializer.to_json(event)
        parsed = json.loads(j)
        assert "event_id" in parsed
        assert parsed["event_type"] == "task"

    def test_from_json(self):
        serializer = EventSerializer()
        event = Event(event_type=EventType.TASK)
        j = serializer.to_json(event)
        restored = serializer.from_json(j)
        assert restored.event_type == event.event_type

    def test_to_dict_has_all_fields(self):
        serializer = EventSerializer()
        event = Event(event_type=EventType.TASK)
        d = serializer.to_dict(event)
        assert "event_id" in d
        assert "event_type" in d
        assert "metadata" in d
        assert "payload" in d

    def test_from_dict_with_tags(self):
        serializer = EventSerializer()
        event = Event(
            event_type=EventType.TASK,
            metadata=EventMetadata(tags=["tag1", "tag2"]),
        )
        d = serializer.to_dict(event)
        restored = serializer.from_dict(d)
        assert restored.metadata.tags == ["tag1", "tag2"]

    def test_roundtrip_all_states(self):
        serializer = EventSerializer()
        for state in ["pending", "published", "failed"]:
            event = Event(event_type=EventType.TASK)
            from app.events.interfaces import EventState
            event.state = EventState(state)
            d = serializer.to_dict(event)
            restored = serializer.from_dict(d)
            assert restored.state.value == state
