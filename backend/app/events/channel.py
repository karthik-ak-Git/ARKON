"""Event channels."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from app.events.exceptions import ChannelError, ChannelNotFoundError
from app.events.interfaces import Channel, ChannelType


class ChannelManager:
    """Manages communication channels."""

    def __init__(self) -> None:
        self._channels: dict[str, Channel] = {}
        self._by_type: dict[ChannelType, list[str]] = {}
        self._lock = threading.Lock()
        self._initialize_default_channels()

    def _initialize_default_channels(self) -> None:
        """Create default channels."""
        defaults = [
            (ChannelType.WORKSPACE, "workspace", "Workspace events"),
            (ChannelType.AGENT, "agent", "Agent lifecycle events"),
            (ChannelType.SCHEDULER, "scheduler", "Scheduler events"),
            (ChannelType.EXECUTION, "execution", "Execution events"),
            (ChannelType.RUNTIME, "runtime", "Runtime events"),
            (ChannelType.RESOURCE, "resource", "Resource events"),
            (ChannelType.PLUGIN, "plugin", "Plugin events"),
            (ChannelType.WORKFLOW, "workflow", "Workflow events"),
            (ChannelType.MONITORING, "monitoring", "Monitoring events"),
            (ChannelType.SYSTEM, "system", "System events"),
        ]
        for ch_type, name, desc in defaults:
            channel = Channel(
                channel_type=ch_type,
                name=name,
                description=desc,
            )
            self._channels[channel.channel_id] = channel
            self._by_type.setdefault(ch_type, []).append(channel.channel_id)

    def create_channel(
        self,
        channel_type: ChannelType = ChannelType.CUSTOM,
        name: str = "",
        description: str = "",
        max_subscribers: int = 1000,
        max_events_per_second: float = 1000.0,
    ) -> Channel:
        """Create a new channel."""
        with self._lock:
            channel = Channel(
                channel_type=channel_type,
                name=name or f"{channel_type.value}_{len(self._channels)}",
                description=description,
                max_subscribers=max_subscribers,
                max_events_per_second=max_events_per_second,
            )
            self._channels[channel.channel_id] = channel
            self._by_type.setdefault(channel_type, []).append(channel.channel_id)
            return channel

    def get_channel(self, channel_id: str) -> Channel:
        """Get channel by ID."""
        channel = self._channels.get(channel_id)
        if not channel:
            raise ChannelNotFoundError(f"Channel not found: {channel_id}")
        return channel

    def get_channel_by_type(self, channel_type: ChannelType) -> Channel | None:
        """Get first channel of a type."""
        channel_ids = self._by_type.get(channel_type, [])
        if channel_ids:
            return self._channels.get(channel_ids[0])
        return None

    def remove_channel(self, channel_id: str) -> bool:
        """Remove a channel."""
        with self._lock:
            channel = self._channels.pop(channel_id, None)
            if channel:
                type_channels = self._by_type.get(channel.channel_type, [])
                if channel_id in type_channels:
                    type_channels.remove(channel_id)
                return True
            return False

    def list_channels(self) -> list[Channel]:
        return list(self._channels.values())

    def list_by_type(self, channel_type: ChannelType) -> list[Channel]:
        channel_ids = self._by_type.get(channel_type, [])
        return [self._channels[cid] for cid in channel_ids if cid in self._channels]

    def count(self) -> int:
        return len(self._channels)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_channels": len(self._channels),
            "by_type": {ct.value: len(ids) for ct, ids in self._by_type.items()},
        }
