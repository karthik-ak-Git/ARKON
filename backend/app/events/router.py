"""Event routing."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.interfaces import (
    ChannelType,
    Event,
    Subscription,
    SubscriptionType,
)


@dataclass
class RoutingRule:
    """A routing rule for event dispatch."""

    rule_id: str = ""
    name: str = ""
    source_channel: ChannelType | None = None
    target_channel: ChannelType | None = None
    event_type_filter: Any = None
    topic_filter: str = ""
    priority: int = 0
    is_active: bool = True
    transform: Callable[[Event], Event] | None = None

    def matches(self, event: Event) -> bool:
        if not self.is_active:
            return False
        if self.source_channel and event.metadata.channel != self.source_channel:
            return False
        if self.event_type_filter and event.event_type != self.event_type_filter:
            return False
        if self.topic_filter and event.metadata.topic != self.topic_filter:
            return False
        return True


class EventRouter:
    """Routes events based on rules and subscriptions."""

    def __init__(self) -> None:
        self._rules: list[RoutingRule] = []
        self._topic_subscriptions: dict[str, list[Subscription]] = {}
        self._channel_subscriptions: dict[ChannelType, list[Subscription]] = {}
        self._wildcard_subscriptions: list[Subscription] = []
        self._lock = threading.Lock()
        self._routing_history: list[dict[str, Any]] = []

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule."""
        with self._lock:
            self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        with self._lock:
            for i, rule in enumerate(self._rules):
                if rule.rule_id == rule_id:
                    self._rules.pop(i)
                    return True
            return False

    def route_event(self, event: Event) -> list[Subscription]:
        """Find all matching subscriptions for an event."""
        matches: list[Subscription] = []

        topic_subs = self._topic_subscriptions.get(event.metadata.topic, [])
        for sub in topic_subs:
            if sub.matches(event):
                matches.append(sub)

        channel_subs = self._channel_subscriptions.get(event.metadata.channel, [])
        for sub in channel_subs:
            if sub.matches(event) and sub not in matches:
                matches.append(sub)

        for sub in self._wildcard_subscriptions:
            if sub.matches(event) and sub not in matches:
                matches.append(sub)

        matches.sort(key=lambda s: s.priority, reverse=True)

        self._routing_history.append({
            "event_id": event.event_id,
            "topic": event.metadata.topic,
            "channel": event.metadata.channel.value,
            "matches": len(matches),
        })

        return matches

    def subscribe(self, subscription: Subscription) -> None:
        """Register a subscription for routing."""
        with self._lock:
            if subscription.subscription_type == SubscriptionType.WILDCARD:
                self._wildcard_subscriptions.append(subscription)
            elif subscription.topic:
                self._topic_subscriptions.setdefault(subscription.topic, []).append(subscription)
            if subscription.channel:
                self._channel_subscriptions.setdefault(subscription.channel, []).append(subscription)

    def unsubscribe(self, subscription_id: str) -> bool:
        with self._lock:
            for topic_subs in self._topic_subscriptions.values():
                for i, sub in enumerate(topic_subs):
                    if sub.subscription_id == subscription_id:
                        topic_subs.pop(i)
                        return True
            for channel_subs in self._channel_subscriptions.values():
                for i, sub in enumerate(channel_subs):
                    if sub.subscription_id == subscription_id:
                        channel_subs.pop(i)
                        return True
            for i, sub in enumerate(self._wildcard_subscriptions):
                if sub.subscription_id == subscription_id:
                    self._wildcard_subscriptions.pop(i)
                    return True
            return False

    def get_rules(self) -> list[RoutingRule]:
        return list(self._rules)

    def get_routing_history(self) -> list[dict[str, Any]]:
        return list(self._routing_history)

    def clear(self) -> None:
        with self._lock:
            self._rules.clear()
            self._topic_subscriptions.clear()
            self._channel_subscriptions.clear()
            self._wildcard_subscriptions.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rules": len(self._rules),
            "topic_subscriptions": sum(len(s) for s in self._topic_subscriptions.values()),
            "channel_subscriptions": sum(len(s) for s in self._channel_subscriptions.values()),
            "wildcard_subscriptions": len(self._wildcard_subscriptions),
        }
