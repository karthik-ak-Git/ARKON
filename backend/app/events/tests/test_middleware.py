"""Tests for middleware pipeline."""

import pytest
from app.events.middleware import (
    MiddlewarePipeline,
    LoggingMiddleware,
    MetricsMiddleware,
    ValidationMiddleware,
    RetryMiddleware,
    TracingMiddleware,
    CompressionMiddleware,
    AuthMiddleware,
)
from app.events.exceptions import MiddlewareError
from app.events.interfaces import Event, EventMetadata, EventType


def _event(event_type: EventType = EventType.TASK) -> Event:
    return Event(event_type=event_type)


class TestMiddlewarePipeline:
    def test_empty_pipeline(self):
        pipeline = MiddlewarePipeline()
        event = _event()
        called = []
        pipeline.execute(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_add_middleware(self):
        pipeline = MiddlewarePipeline()
        pipeline.add(LoggingMiddleware())
        pipeline.add(MetricsMiddleware())
        assert len(pipeline.get_middlewares()) == 2

    def test_remove_middleware(self):
        pipeline = MiddlewarePipeline()
        m = LoggingMiddleware()
        pipeline.add(m)
        pipeline.remove(m.get_name())
        assert len(pipeline.get_middlewares()) == 0

    def test_remove_nonexistent(self):
        pipeline = MiddlewarePipeline()
        assert pipeline.remove("nonexistent") is False

    def test_logging_middleware(self):
        m = LoggingMiddleware()
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_logging_with_callback(self):
        m = LoggingMiddleware()
        logs = []
        m.set_logger(lambda event, data: logs.append((event, data)))
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1
        assert len(logs) == 2
        assert logs[0][0] == "event_processing"

    def test_metrics_middleware(self):
        m = MetricsMiddleware()
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1
        assert m.events_processed == 1
        assert m.avg_processing_time_ms >= 0

    def test_metrics_middleware_error(self):
        m = MetricsMiddleware()
        event = _event()
        with pytest.raises(RuntimeError):
            m.process(event, lambda e: (_ for _ in ()).throw(RuntimeError("fail")))
        assert m.events_processed == 1
        assert m.errors == 1

    def test_validation_middleware(self):
        m = ValidationMiddleware()
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_validation_middleware_custom(self):
        m = ValidationMiddleware()
        m.set_validator(lambda e: e.event_type == EventType.TASK)
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_validation_middleware_custom_fails(self):
        m = ValidationMiddleware()
        m.set_validator(lambda e: e.event_type == EventType.ERROR)
        event = _event()
        with pytest.raises(MiddlewareError, match="Custom validation failed"):
            m.process(event, lambda e: None)

    def test_validation_middleware_missing_field(self):
        m = ValidationMiddleware(required_fields=["event_id", "nonexistent"])
        event = _event()
        with pytest.raises(MiddlewareError, match="Missing required field"):
            m.process(event, lambda e: None)

    def test_retry_middleware_success(self):
        m = RetryMiddleware(max_retries=2)
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_retry_middleware_exhausted(self):
        m = RetryMiddleware(max_retries=1)
        event = _event()
        with pytest.raises(MiddlewareError, match="Failed after 1 retries"):
            m.process(event, lambda e: (_ for _ in ()).throw(RuntimeError("fail")))

    def test_retry_middleware_with_callback(self):
        m = RetryMiddleware(max_retries=1)
        retries = []
        m.set_retry_callback(lambda e, n: retries.append(n))
        event = _event()
        with pytest.raises(MiddlewareError):
            m.process(event, lambda e: (_ for _ in ()).throw(RuntimeError("fail")))
        assert retries == [1]

    def test_tracing_middleware(self):
        m = TracingMiddleware()
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_tracing_middleware_with_generator(self):
        m = TracingMiddleware()
        m.set_trace_generator(lambda: "trace-abc-123")
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1
        assert "trace:trace-abc-123" in event.metadata.tags

    def test_compression_middleware(self):
        m = CompressionMiddleware()
        event = _event()
        event.payload = {"key": "x" * 1000}
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1
        assert "compressed" not in event.metadata.tags

    def test_compression_middleware_enabled(self):
        m = CompressionMiddleware(enabled=True)
        event = _event()
        event.payload = {"key": "x" * 1000}
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1
        assert "compressed" in event.metadata.tags

    def test_auth_middleware_no_checker(self):
        m = AuthMiddleware()
        event = _event()
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_auth_middleware_passes(self):
        m = AuthMiddleware()
        m.set_auth_checker(lambda e: e.metadata.source == "trusted")
        event = _event()
        event.metadata.source = "trusted"
        called = []
        m.process(event, lambda e: called.append(e))
        assert len(called) == 1

    def test_auth_middleware_rejects(self):
        m = AuthMiddleware()
        m.set_auth_checker(lambda e: e.metadata.source == "trusted")
        event = _event()
        event.metadata.source = "untrusted"
        with pytest.raises(MiddlewareError, match="Authentication failed"):
            m.process(event, lambda e: None)

    def test_pipeline_order(self):
        pipeline = MiddlewarePipeline()
        order = []
        pipeline.add(type("M1", (), {"process": lambda s, e, n: (order.append(1), n(e))})())
        pipeline.add(type("M2", (), {"process": lambda s, e, n: (order.append(2), n(e))})())
        pipeline.execute(_event(), lambda e: order.append("done"))
        assert order == [1, 2, "done"]

    def test_pipeline_to_dict(self):
        pipeline = MiddlewarePipeline()
        pipeline.add(LoggingMiddleware())
        d = pipeline.to_dict()
        assert d["count"] == 1
        assert "logging" in d["middlewares"]

    def test_pipeline_clear(self):
        pipeline = MiddlewarePipeline()
        pipeline.add(LoggingMiddleware())
        pipeline.add(MetricsMiddleware())
        pipeline.clear()
        assert len(pipeline.get_middlewares()) == 0

    def test_get_middlewares(self):
        pipeline = MiddlewarePipeline()
        m1 = LoggingMiddleware()
        m2 = MetricsMiddleware()
        pipeline.add(m1)
        pipeline.add(m2)
        result = pipeline.get_middlewares()
        assert len(result) == 2
        result.pop()  # mutate copy, not original
        assert len(pipeline.get_middlewares()) == 2
