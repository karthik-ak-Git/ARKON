"""Event dispatching."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.interfaces import (
    DeliveryMode,
    Event,
    EventState,
    Subscription,
)


@dataclass
class DispatchResult:
    """Result of event dispatch."""

    success: bool = True
    event_id: str = ""
    subscription_id: str = ""
    error: str | None = None
    delivered_at: float = field(default_factory=time.time)
    attempt: int = 1
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "event_id": self.event_id,
            "subscription_id": self.subscription_id,
            "error": self.error,
            "delivered_at": self.delivered_at,
            "attempt": self.attempt,
            "latency_ms": self.latency_ms,
        }


class EventDispatcher:
    """Dispatches events to subscribers."""

    def __init__(self) -> None:
        self._dispatch_history: list[DispatchResult] = []
        self._lock = threading.Lock()
        self._max_history = 10000

    def dispatch(
        self,
        event: Event,
        subscription: Subscription,
        middleware_chain: Callable[[Event, Callable], Any] | None = None,
    ) -> DispatchResult:
        """Dispatch an event to a subscription."""
        start = time.time()
        event.state = EventState.DELIVERING

        try:
            if subscription.callback is None:
                result = DispatchResult(
                    success=False,
                    event_id=event.event_id,
                    subscription_id=subscription.subscription_id,
                    error="No callback registered",
                )
                self._record(result)
                return result

            if middleware_chain:
                middleware_chain(event, subscription.callback)
            else:
                subscription.callback(event)

            event.state = EventState.DELIVERED
            latency_ms = (time.time() - start) * 1000
            result = DispatchResult(
                success=True,
                event_id=event.event_id,
                subscription_id=subscription.subscription_id,
                latency_ms=latency_ms,
            )
        except Exception as e:
            event.state = EventState.FAILED
            result = DispatchResult(
                success=False,
                event_id=event.event_id,
                subscription_id=subscription.subscription_id,
                error=str(e),
            )

        self._record(result)
        return result

    def dispatch_batch(
        self,
        event: Event,
        subscriptions: list[Subscription],
        middleware_chain: Callable[[Event, Callable], Any] | None = None,
    ) -> list[DispatchResult]:
        """Dispatch an event to multiple subscriptions."""
        results = []
        for sub in subscriptions:
            result = self.dispatch(event, sub, middleware_chain)
            results.append(result)
        return results

    def _record(self, result: DispatchResult) -> None:
        with self._lock:
            self._dispatch_history.append(result)
            if len(self._dispatch_history) > self._max_history:
                self._dispatch_history = self._dispatch_history[-self._max_history:]

    def get_history(self, limit: int = 100) -> list[DispatchResult]:
        return list(self._dispatch_history[-limit:])

    def get_success_rate(self) -> float:
        if not self._dispatch_history:
            return 0.0
        successes = sum(1 for r in self._dispatch_history if r.success)
        return successes / len(self._dispatch_history)

    def clear_history(self) -> None:
        with self._lock:
            self._dispatch_history.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dispatch_count": len(self._dispatch_history),
            "success_rate": self.get_success_rate(),
        }
