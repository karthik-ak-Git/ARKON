"""Tests for metrics."""

from app.events.metrics import EventBusMetricsCollector


class TestEventBusMetricsCollector:
    def test_create(self):
        m = EventBusMetricsCollector()
        metrics = m.get_metrics()
        assert metrics.events_published == 0

    def test_record_published(self):
        m = EventBusMetricsCollector()
        m.record_published()
        assert m.get_metrics().events_published == 1

    def test_record_published_multiple(self):
        m = EventBusMetricsCollector()
        for _ in range(5):
            m.record_published()
        assert m.get_metrics().events_published == 5

    def test_record_delivered(self):
        m = EventBusMetricsCollector()
        m.record_delivered(10.5)
        assert m.get_metrics().events_delivered == 1
        assert m.get_metrics().avg_delivery_latency_ms == 10.5

    def test_record_delivered_multiple(self):
        m = EventBusMetricsCollector()
        m.record_delivered(10.0)
        m.record_delivered(20.0)
        assert m.get_metrics().events_delivered == 2
        assert m.get_metrics().avg_delivery_latency_ms == 15.0
        assert m.get_metrics().max_delivery_latency_ms == 20.0

    def test_record_failed(self):
        m = EventBusMetricsCollector()
        m.record_failed()
        assert m.get_metrics().events_failed == 1

    def test_record_dead_lettered(self):
        m = EventBusMetricsCollector()
        m.record_dead_lettered()
        assert m.get_metrics().events_dead_lettered == 1

    def test_record_replayed(self):
        m = EventBusMetricsCollector()
        m.record_replayed()
        assert m.get_metrics().events_replayed == 1

    def test_record_filtered(self):
        m = EventBusMetricsCollector()
        m.record_filtered()
        assert m.get_metrics().events_filtered == 1

    def test_record_backpressure(self):
        m = EventBusMetricsCollector()
        m.record_backpressure()
        assert m.get_metrics().backpressure_events == 1

    def test_set_active_subscriptions(self):
        m = EventBusMetricsCollector()
        m.set_active_subscriptions(42)
        assert m.get_metrics().active_subscriptions == 42

    def test_set_active_channels(self):
        m = EventBusMetricsCollector()
        m.set_active_channels(10)
        assert m.get_metrics().active_channels == 10

    def test_set_active_topics(self):
        m = EventBusMetricsCollector()
        m.set_active_topics(7)
        assert m.get_metrics().active_topics == 7

    def test_custom_metric(self):
        m = EventBusMetricsCollector()
        m.record_metric("custom_count", 42)
        history = m.get_metric_history("custom_count")
        assert len(history) == 1
        assert history[0].value == 42

    def test_custom_metric_with_tags(self):
        m = EventBusMetricsCollector()
        m.record_metric("custom_count", 42, tags={"env": "test"})
        history = m.get_metric_history("custom_count")
        assert len(history) == 1
        assert history[0].tags == {"env": "test"}

    def test_metric_history_filtered(self):
        m = EventBusMetricsCollector()
        m.record_metric("a", 1)
        m.record_metric("b", 2)
        m.record_metric("a", 3)
        assert len(m.get_metric_history("a")) == 2
        assert len(m.get_metric_history("b")) == 1
        assert len(m.get_metric_history()) == 3

    def test_to_dict(self):
        m = EventBusMetricsCollector()
        m.record_published()
        d = m.to_dict()
        assert d["events_published"] == 1

    def test_reset(self):
        m = EventBusMetricsCollector()
        m.record_published()
        m.record_delivered(10.0)
        m.record_metric("x", 1)
        m.reset()
        assert m.get_metrics().events_published == 0
        assert m.get_metrics().events_delivered == 0
        assert len(m.get_metric_history()) == 0

    def test_latency_empty(self):
        m = EventBusMetricsCollector()
        metrics = m.get_metrics()
        assert metrics.avg_delivery_latency_ms == 0.0
        assert metrics.max_delivery_latency_ms == 0.0
