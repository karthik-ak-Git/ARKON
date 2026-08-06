"""Event serialization/deserialization."""

from __future__ import annotations

import json
import time
from typing import Any

from app.events.exceptions import SerializationError
from app.events.interfaces import (
    ChannelType,
    DeliveryMode,
    Event,
    EventMetadata,
    EventPriority,
    EventState,
    EventType,
)


class EventSerializer:
    """Serializes and deserializes events to/from bytes and dicts."""

    def serialize(self, event: Event) -> bytes:
        """Serialize event to JSON bytes."""
        try:
            data = event.to_dict()
            return json.dumps(data, default=str).encode("utf-8")
        except Exception as e:
            raise SerializationError(f"Failed to serialize event: {e}")

    def deserialize(self, data: bytes) -> Event:
        """Deserialize event from JSON bytes."""
        try:
            text = data.decode("utf-8")
            return self.from_dict(json.loads(text))
        except SerializationError:
            raise
        except Exception as e:
            raise SerializationError(f"Failed to deserialize event: {e}")

    def to_dict(self, event: Event) -> dict[str, Any]:
        """Convert event to dictionary."""
        return event.to_dict()

    def from_dict(self, data: dict[str, Any]) -> Event:
        """Create event from dictionary."""
        try:
            metadata_data = data.get("metadata", {})
            metadata = EventMetadata(
                source=metadata_data.get("source", ""),
                target=metadata_data.get("target", ""),
                workspace_id=metadata_data.get("workspace_id", ""),
                correlation_id=metadata_data.get("correlation_id", ""),
                causation_id=metadata_data.get("causation_id", ""),
                version=metadata_data.get("version", 1),
                channel=ChannelType(metadata_data.get("channel", "system")),
                topic=metadata_data.get("topic", ""),
                tags=metadata_data.get("tags", []),
            )

            return Event(
                event_id=data.get("event_id", ""),
                event_type=EventType(data.get("event_type", "custom")),
                timestamp=data.get("timestamp", time.time()),
                priority=EventPriority(data.get("priority", 5)),
                state=EventState(data.get("state", "pending")),
                payload=data.get("payload", {}),
                metadata=metadata,
                delivery_mode=DeliveryMode(data.get("delivery_mode", "fire_and_forget")),
                max_retries=data.get("max_retries", 3),
                retry_count=data.get("retry_count", 0),
                ttl=data.get("ttl"),
                scheduled_at=data.get("scheduled_at"),
            )
        except Exception as e:
            raise SerializationError(f"Failed to create event from dict: {e}")

    def to_json(self, event: Event) -> str:
        """Serialize event to JSON string."""
        return self.serialize(event).decode("utf-8")

    def from_json(self, json_str: str) -> Event:
        """Deserialize event from JSON string."""
        return self.deserialize(json_str.encode("utf-8"))
