"""Subscription management."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.interfaces import (
    ChannelType,
    Event,
    EventPriority,
    Subscription,
    SubscriptionType,
)


@dataclass
class SubscriptionConfig:
    """Subscription configuration."""

    max_subscriptions: int = 10000
    enable_wildcards: bool = True
    enable_pattern_matching: bool = True


class SubscriptionManager:
    """Manages event subscriptions."""

    def __init__(self, config: SubscriptionConfig | None = None) -> None:
        self._config = config or SubscriptionConfig()
        self._subscriptions: dict[str, Subscription] = {}
        self._by_topic: dict[str, list[str]] = {}
        self._by_channel: dict[ChannelType, list[str]] = {}
        self._by_subscriber: dict[str, list[str]] = {}
        self._lock = threading.Lock()
        self._subscription_count = 0

    def create_subscription(
        self,
        subscriber_id: str,
        topic: str = "",
        callback: Callable[[Event], Any] | None = None,
        subscription_type: SubscriptionType = SubscriptionType.EXACT,
        channel: ChannelType | None = None,
        priority: int = 0,
        workspace_id: str = "",
        predicate: Callable[[Event], bool] | None = None,
    ) -> Subscription:
        """Create a new subscription."""
        if len(self._subscriptions) >= self._config.max_subscriptions:
            raise RuntimeError("Max subscriptions reached")

        sub = Subscription(
            topic=topic,
            callback=callback,
            subscription_type=subscription_type,
            channel=channel,
            priority=priority,
            workspace_id=workspace_id,
            predicate=predicate,
        )

        with self._lock:
            self._subscriptions[sub.subscription_id] = sub
            self._subscription_count += 1

            if topic:
                self._by_topic.setdefault(topic, []).append(sub.subscription_id)
            if channel:
                self._by_channel.setdefault(channel, []).append(sub.subscription_id)
            self._by_subscriber.setdefault(subscriber_id, []).append(sub.subscription_id)

        return sub

    def remove_subscription(self, subscription_id: str) -> bool:
        with self._lock:
            sub = self._subscriptions.pop(subscription_id, None)
            if not sub:
                return False

            if sub.topic:
                topic_subs = self._by_topic.get(sub.topic, [])
                if subscription_id in topic_subs:
                    topic_subs.remove(subscription_id)
            if sub.channel:
                channel_subs = self._by_channel.get(sub.channel, [])
                if subscription_id in channel_subs:
                    channel_subs.remove(subscription_id)
            for sid, sub_ids in self._by_subscriber.items():
                if subscription_id in sub_ids:
                    sub_ids.remove(subscription_id)
                    break
            return True

    def get_subscription(self, subscription_id: str) -> Subscription | None:
        return self._subscriptions.get(subscription_id)

    def get_subscriptions_for_topic(self, topic: str) -> list[Subscription]:
        sub_ids = self._by_topic.get(topic, [])
        return [self._subscriptions[sid] for sid in sub_ids if sid in self._subscriptions]

    def get_subscriptions_for_channel(self, channel: ChannelType) -> list[Subscription]:
        sub_ids = self._by_channel.get(channel, [])
        return [self._subscriptions[sid] for sid in sub_ids if sid in self._subscriptions]

    def get_subscriptions_by_subscriber(self, subscriber_id: str) -> list[Subscription]:
        sub_ids = self._by_subscriber.get(subscriber_id, [])
        return [self._subscriptions[sid] for sid in sub_ids if sid in self._subscriptions]

    def find_matching(self, event: Event) -> list[Subscription]:
        """Find all subscriptions matching an event."""
        matches: list[Subscription] = []
        for sub in self._subscriptions.values():
            if sub.matches(event):
                matches.append(sub)
        matches.sort(key=lambda s: s.priority, reverse=True)
        return matches

    def count(self) -> int:
        return len(self._subscriptions)

    def clear(self) -> None:
        with self._lock:
            self._subscriptions.clear()
            self._by_topic.clear()
            self._by_channel.clear()
            self._by_subscriber.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": len(self._subscriptions),
            "by_topic": {t: len(ids) for t, ids in self._by_topic.items()},
            "by_channel": {ch.value: len(ids) for ch, ids in self._by_channel.items()},
        }
