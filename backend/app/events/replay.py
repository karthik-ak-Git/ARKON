"""Event replay functionality."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.exceptions import ReplayError
from app.events.interfaces import Event, ReplayStrategy


@dataclass
class ReplayCheckpoint:
    """Checkpoint for replay position."""

    checkpoint_id: str = ""
    last_event_id: str = ""
    last_timestamp: float = 0.0
    events_replayed: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "last_event_id": self.last_event_id,
            "last_timestamp": self.last_timestamp,
            "events_replayed": self.events_replayed,
            "created_at": self.created_at,
        }


class EventReplayManager:
    """Manages event replay operations."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, ReplayCheckpoint] = {}
        self._replay_history: list[dict[str, Any]] = []

    def replay(
        self,
        events: list[Event],
        strategy: ReplayStrategy = ReplayStrategy.ALL,
        since_timestamp: float | None = None,
        since_event_id: str | None = None,
        callback: Callable[[Event], Any] | None = None,
    ) -> list[Event]:
        """Replay events based on strategy."""
        filtered = self._filter_events(events, strategy, since_timestamp, since_event_id)
        replayed = []
        for event in filtered:
            if callback:
                try:
                    result = callback(event)
                    if hasattr(result, "__await__"):
                        pass
                except Exception as e:
                    raise ReplayError(f"Replay callback failed for {event.event_id}: {e}")
            replayed.append(event)

        self._replay_history.append({
            "strategy": strategy.value,
            "events_replayed": len(replayed),
            "timestamp": time.time(),
        })
        return replayed

    def _filter_events(
        self,
        events: list[Event],
        strategy: ReplayStrategy,
        since_timestamp: float | None,
        since_event_id: str | None,
    ) -> list[Event]:
        """Filter events based on replay strategy."""
        if strategy == ReplayStrategy.ALL:
            return list(events)

        if strategy == ReplayStrategy.SINCE_TIMESTAMP:
            if since_timestamp is None:
                raise ReplayError("since_timestamp required for SINCE_TIMESTAMP strategy")
            return [e for e in events if e.timestamp >= since_timestamp]

        if strategy == ReplayStrategy.SINCE_EVENT_ID:
            if since_event_id is None:
                raise ReplayError("since_event_id required for SINCE_EVENT_ID strategy")
            found = False
            result = []
            for e in events:
                if e.event_id == since_event_id:
                    found = True
                    continue
                if found:
                    result.append(e)
            return result

        if strategy == ReplayStrategy.FROM_LAST_CHECKPOINT:
            return events

        return list(events)

    def save_checkpoint(self, checkpoint: ReplayCheckpoint) -> None:
        """Save a replay checkpoint."""
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> ReplayCheckpoint | None:
        return self._checkpoints.get(checkpoint_id)

    def list_checkpoints(self) -> list[ReplayCheckpoint]:
        return list(self._checkpoints.values())

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            return True
        return False

    def get_replay_history(self) -> list[dict[str, Any]]:
        return list(self._replay_history)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoints": len(self._checkpoints),
            "replay_count": len(self._replay_history),
        }
