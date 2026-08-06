"""Event topics."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from app.events.exceptions import TopicError, TopicNotFoundError
from app.events.interfaces import ChannelType, Topic


class TopicManager:
    """Manages event topics."""

    def __init__(self) -> None:
        self._topics: dict[str, Topic] = {}
        self._by_name: dict[str, str] = {}
        self._by_channel: dict[ChannelType, list[str]] = {}
        self._lock = threading.Lock()
        self._initialize_default_topics()

    def _initialize_default_topics(self) -> None:
        """Create default topics."""
        defaults = [
            ("tasks", ChannelType.SCHEDULER, "Task lifecycle events"),
            ("resources", ChannelType.RESOURCE, "Resource management events"),
            ("capabilities", ChannelType.EXECUTION, "Capability events"),
            ("heartbeats", ChannelType.MONITORING, "Heartbeat events"),
            ("logs", ChannelType.SYSTEM, "Log events"),
            ("metrics", ChannelType.MONITORING, "Metric events"),
            ("progress", ChannelType.EXECUTION, "Progress events"),
            ("errors", ChannelType.SYSTEM, "Error events"),
            ("lifecycle", ChannelType.RUNTIME, "Lifecycle events"),
        ]
        for name, channel, desc in defaults:
            topic = Topic(name=name, channel=channel, description=desc)
            self._topics[topic.topic_id] = topic
            self._by_name[name] = topic.topic_id
            self._by_channel.setdefault(channel, []).append(topic.topic_id)

    def create_topic(
        self,
        name: str,
        channel: ChannelType = ChannelType.SYSTEM,
        description: str = "",
        retention_seconds: float = 3600.0,
        max_subscribers: int = 100,
    ) -> Topic:
        """Create a new topic."""
        with self._lock:
            if name in self._by_name:
                raise TopicError(f"Topic already exists: {name}")
            topic = Topic(
                name=name,
                channel=channel,
                description=description,
                retention_seconds=retention_seconds,
                max_subscribers=max_subscribers,
            )
            self._topics[topic.topic_id] = topic
            self._by_name[name] = topic.topic_id
            self._by_channel.setdefault(channel, []).append(topic.topic_id)
            return topic

    def get_topic(self, topic_id: str) -> Topic:
        topic = self._topics.get(topic_id)
        if not topic:
            raise TopicNotFoundError(f"Topic not found: {topic_id}")
        return topic

    def get_topic_by_name(self, name: str) -> Topic | None:
        topic_id = self._by_name.get(name)
        if topic_id:
            return self._topics.get(topic_id)
        return None

    def remove_topic(self, topic_id: str) -> bool:
        with self._lock:
            topic = self._topics.pop(topic_id, None)
            if topic:
                self._by_name.pop(topic.name, None)
                channel_topics = self._by_channel.get(topic.channel, [])
                if topic_id in channel_topics:
                    channel_topics.remove(topic_id)
                return True
            return False

    def list_topics(self) -> list[Topic]:
        return list(self._topics.values())

    def list_by_channel(self, channel: ChannelType) -> list[Topic]:
        topic_ids = self._by_channel.get(channel, [])
        return [self._topics[tid] for tid in topic_ids if tid in self._topics]

    def count(self) -> int:
        return len(self._topics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_topics": len(self._topics),
            "by_channel": {ch.value: len(ids) for ch, ids in self._by_channel.items()},
        }
