"""Event middleware pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.exceptions import MiddlewareError
from app.events.interfaces import Event, IMiddleware


@dataclass
class LoggingMiddleware(IMiddleware):
    """Logs event processing."""

    name: str = "logging"
    _log_callback: Callable[[str, dict[str, Any]], None] | None = None

    def set_logger(self, callback: Callable[[str, dict[str, Any]], None]) -> None:
        self._log_callback = callback

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any:
        log_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "topic": event.metadata.topic,
            "source": event.metadata.source,
        }
        if self._log_callback:
            self._log_callback("event_processing", log_data)
        result = next_fn(event)
        if self._log_callback:
            self._log_callback("event_processed", log_data)
        return result

    def get_name(self) -> str:
        return self.name


@dataclass
class MetricsMiddleware(IMiddleware):
    """Collects event processing metrics."""

    name: str = "metrics"
    events_processed: int = 0
    total_processing_time_ms: float = 0.0
    errors: int = 0

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any:
        start = time.time()
        self.events_processed += 1
        try:
            result = next_fn(event)
            return result
        except Exception:
            self.errors += 1
            raise
        finally:
            elapsed = (time.time() - start) * 1000
            self.total_processing_time_ms += elapsed

    @property
    def avg_processing_time_ms(self) -> float:
        if self.events_processed == 0:
            return 0.0
        return self.total_processing_time_ms / self.events_processed

    def get_name(self) -> str:
        return self.name


@dataclass
class ValidationMiddleware(IMiddleware):
    """Validates events before processing."""

    name: str = "validation"
    required_fields: list[str] = field(default_factory=lambda: ["event_id", "event_type"])
    _validator: Callable[[Event], bool] | None = None

    def set_validator(self, validator: Callable[[Event], bool]) -> None:
        self._validator = validator

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any:
        for field_name in self.required_fields:
            if not getattr(event, field_name, None):
                raise MiddlewareError(f"Missing required field: {field_name}")
        if self._validator and not self._validator(event):
            raise MiddlewareError("Custom validation failed")
        return next_fn(event)

    def get_name(self) -> str:
        return self.name


@dataclass
class RetryMiddleware(IMiddleware):
    """Retries failed event processing."""

    name: str = "retry"
    max_retries: int = 3
    retry_delay_ms: float = 100.0
    _retry_callback: Callable[[Event, int], None] | None = None

    def set_retry_callback(self, callback: Callable[[Event, int], None]) -> None:
        self._retry_callback = callback

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return next_fn(event)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    if self._retry_callback:
                        self._retry_callback(event, attempt + 1)
                    event.retry_count = attempt + 1
        raise MiddlewareError(f"Failed after {self.max_retries} retries: {last_error}")

    def get_name(self) -> str:
        return self.name


@dataclass
class TracingMiddleware(IMiddleware):
    """Adds trace information to events."""

    name: str = "tracing"
    _trace_id_generator: Callable[[], str] | None = None

    def set_trace_generator(self, generator: Callable[[], str]) -> None:
        self._trace_id_generator = generator

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any:
        if self._trace_id_generator:
            trace_id = self._trace_id_generator()
            event.metadata.tags.append(f"trace:{trace_id}")
        return next_fn(event)

    def get_name(self) -> str:
        return self.name


@dataclass
class CompressionMiddleware(IMiddleware):
    """Compresses event payload (placeholder)."""

    name: str = "compression"
    enabled: bool = False

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any:
        if self.enabled and event.payload:
            event.metadata.tags.append("compressed")
        return next_fn(event)

    def get_name(self) -> str:
        return self.name


@dataclass
class AuthMiddleware(IMiddleware):
    """Authenticates event source (placeholder for future)."""

    name: str = "auth"
    _auth_checker: Callable[[Event], bool] | None = None

    def set_auth_checker(self, checker: Callable[[Event], bool]) -> None:
        self._auth_checker = checker

    def process(self, event: Event, next_fn: Callable[[Event], Any]) -> Any:
        if self._auth_checker and not self._auth_checker(event):
            raise MiddlewareError("Authentication failed")
        return next_fn(event)

    def get_name(self) -> str:
        return self.name


class MiddlewarePipeline:
    """Manages and executes middleware pipeline."""

    def __init__(self) -> None:
        self._middlewares: list[IMiddleware] = []

    def add(self, middleware: IMiddleware) -> None:
        """Add middleware to the pipeline."""
        self._middlewares.append(middleware)

    def remove(self, name: str) -> bool:
        """Remove middleware by name."""
        for i, m in enumerate(self._middlewares):
            if m.get_name() == name:
                self._middlewares.pop(i)
                return True
        return False

    def execute(self, event: Event, handler: Callable[[Event], Any]) -> Any:
        """Execute the middleware pipeline."""
        if not self._middlewares:
            return handler(event)

        def build_chain(index: int, current_event: Event) -> Any:
            if index >= len(self._middlewares):
                return handler(current_event)
            middleware = self._middlewares[index]
            return middleware.process(current_event, lambda e: build_chain(index + 1, e))

        return build_chain(0, event)

    def get_middlewares(self) -> list[IMiddleware]:
        return list(self._middlewares)

    def clear(self) -> None:
        self._middlewares.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self._middlewares),
            "middlewares": [m.get_name() for m in self._middlewares],
        }
