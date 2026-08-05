"""Backpressure - overload detection, throttling, and rejection."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.scheduler.interfaces import BackpressureMode, Task


@dataclass
class SystemLoad:
    """Current system load snapshot."""

    queue_size: int = 0
    running_count: int = 0
    pending_count: int = 0
    avg_completion_time: float = 0.0
    error_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)

    @property
    def total_in_flight(self) -> int:
        return self.queue_size + self.running_count + self.pending_count


@dataclass
class ThrottleConfig:
    """Backpressure thresholds."""

    warning_threshold: int = 50
    critical_threshold: int = 80
    max_queue_size: int = 1000
    max_concurrent: int = 100
    throttle_delay: float = 1.0
    rejection_rate_limit: float = 0.5


class BackpressureManager:
    """Detects overload and applies backpressure."""

    def __init__(
        self,
        mode: BackpressureMode = BackpressureMode.ADAPTIVE,
        config: ThrottleConfig | None = None,
    ) -> None:
        self._mode = mode
        self._config = config or ThrottleConfig()
        self._load_history: list[SystemLoad] = []
        self._throttle_until: float = 0.0
        self._rejected_count: int = 0
        self._throttled_count: int = 0

    @property
    def mode(self) -> BackpressureMode:
        return self._mode

    def set_mode(self, mode: BackpressureMode) -> None:
        self._mode = mode

    def update_load(self, load: SystemLoad) -> None:
        self._load_history.append(load)
        if len(self._load_history) > 100:
            self._load_history = self._load_history[-50:]

    def get_load(self) -> SystemLoad | None:
        return self._load_history[-1] if self._load_history else None

    def is_overloaded(self) -> bool:
        load = self.get_load()
        if not load:
            return False
        return load.total_in_flight >= self._config.critical_threshold

    def is_warning(self) -> bool:
        load = self.get_load()
        if not load:
            return False
        return load.total_in_flight >= self._config.warning_threshold

    def should_throttle(self) -> bool:
        if self._mode == BackpressureMode.NONE:
            return False
        if time.time() < self._throttle_until:
            return True
        if self._mode in (BackpressureMode.THROTTLE, BackpressureMode.ADAPTIVE):
            return self.is_overloaded()
        return False

    def should_reject(self) -> bool:
        if self._mode == BackpressureMode.NONE:
            return False
        if self._mode == BackpressureMode.REJECT:
            return self.is_overloaded()
        if self._mode == BackpressureMode.ADAPTIVE:
            load = self.get_load()
            if load and load.queue_size >= self._config.max_queue_size:
                return True
        return False

    def get_delay(self) -> float:
        if not self.should_throttle():
            return 0.0
        if self._mode == BackpressureMode.ADAPTIVE:
            load = self.get_load()
            if not load:
                return 0.0
            ratio = load.total_in_flight / self._config.critical_threshold
            return min(self._config.throttle_delay * ratio, 30.0)
        return self._config.throttle_delay

    def record_rejection(self) -> None:
        self._rejected_count += 1

    def record_throttle(self) -> None:
        self._throttled_count += 1

    def set_throttle(self, duration: float) -> None:
        self._throttle_until = time.time() + duration

    def get_stats(self) -> dict:
        return {
            "mode": self._mode.value,
            "is_overloaded": self.is_overloaded(),
            "is_warning": self.is_warning(),
            "should_throttle": self.should_throttle(),
            "should_reject": self.should_reject(),
            "rejected_count": self._rejected_count,
            "throttled_count": self._throttled_count,
            "load_history_size": len(self._load_history),
        }

    def to_dict(self) -> dict:
        return self.get_stats()
