"""Priority levels and dynamic priority management."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field


class PriorityLevel(enum.IntEnum):
    """Priority levels (lower number = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 5
    LOW = 10
    BACKGROUND = 15


PRIORITY_NAMES = {p.name: p.value for p in PriorityLevel}
PRIORITY_VALUES = {p.value: p.name for p in PriorityLevel}


@dataclass
class PriorityConfig:
    """Configuration for priority management."""

    default_priority: int = PriorityLevel.NORMAL
    aging_enabled: bool = False
    aging_interval: float = 60.0
    aging_increment: float = 1.0
    max_priority: int = PriorityLevel.CRITICAL
    min_priority: int = PriorityLevel.BACKGROUND


class PriorityManager:
    """Manages task priorities with dynamic updates and aging."""

    def __init__(self, config: PriorityConfig | None = None) -> None:
        self._config = config or PriorityConfig()
        self._priorities: dict[str, int] = {}
        self._history: list[tuple[str, int, int, float]] = []

    def set_priority(self, task_id: str, priority: int) -> tuple[int, int]:
        """Set priority. Returns (old_priority, new_priority)."""
        clamped = max(self._config.max_priority, min(self._config.min_priority, priority))
        old = self._priorities.get(task_id, self._config.default_priority)
        self._priorities[task_id] = clamped
        self._history.append((task_id, old, clamped, time.time()))
        return old, clamped

    def get_priority(self, task_id: str) -> int:
        return self._priorities.get(task_id, self._config.default_priority)

    def remove(self, task_id: str) -> None:
        self._priorities.pop(task_id, None)

    def apply_aging(self, task_ids: list[str], current_time: float | None = None) -> dict[str, tuple[int, int]]:
        """Apply priority aging to tasks. Returns {task_id: (old, new)}."""
        if not self._config.aging_enabled:
            return {}
        now = current_time or time.time()
        changes: dict[str, tuple[int, int]] = {}
        for tid in task_ids:
            old = self.get_priority(tid)
            new = max(self._config.max_priority, old - int(self._config.aging_increment))
            if new != old:
                self.set_priority(tid, new)
                changes[tid] = (old, new)
        return changes

    def get_history(self, task_id: str | None = None) -> list[tuple[str, int, int, float]]:
        if task_id is None:
            return list(self._history)
        return [h for h in self._history if h[0] == task_id]

    def to_dict(self) -> dict:
        return {
            "priorities": dict(self._priorities),
            "config": {
                "default_priority": self._config.default_priority,
                "aging_enabled": self._config.aging_enabled,
                "aging_interval": self._config.aging_interval,
                "aging_increment": self._config.aging_increment,
            },
        }
