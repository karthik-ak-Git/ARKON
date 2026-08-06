"""Tests for AI events module."""

import pytest

from app.ai.events import (
    provider_enabled,
    provider_disabled,
    provider_registered,
    provider_authenticated,
    provider_error,
    chat_completed,
    chat_failed,
    stream_completed,
    routing_decided,
    models_listed,
)


class TestProviderEvents:
    def test_provider_enabled(self):
        event = provider_enabled("openrouter")
        assert event["event_type"] == "ai.provider.enabled"
        assert event["payload"]["provider_id"] == "openrouter"
        assert "event_id" in event
        assert "timestamp" in event

    def test_provider_disabled(self):
        event = provider_disabled("ollama")
        assert event["event_type"] == "ai.provider.disabled"
        assert event["payload"]["provider_id"] == "ollama"

    def test_provider_registered(self):
        event = provider_registered("gemini")
        assert event["event_type"] == "ai.provider.registered"
        assert event["payload"]["provider_id"] == "gemini"

    def test_provider_authenticated(self):
        event = provider_authenticated("nvidia_nim")
        assert event["event_type"] == "ai.provider.authenticated"
        assert event["payload"]["provider_id"] == "nvidia_nim"

    def test_provider_error(self):
        event = provider_error("openrouter", "auth failed")
        assert event["event_type"] == "ai.provider.error"
        assert event["payload"]["error"] == "auth failed"


class TestChatEvents:
    def test_chat_completed(self):
        event = chat_completed("openrouter", "gpt-4", 100)
        assert event["event_type"] == "ai.chat.completed"
        assert event["payload"]["tokens"] == 100

    def test_chat_failed(self):
        event = chat_failed("gemini", "timeout")
        assert event["event_type"] == "ai.chat.failed"
        assert event["payload"]["error"] == "timeout"


class TestStreamEvents:
    def test_stream_completed(self):
        event = stream_completed("openrouter", "gpt-4")
        assert event["event_type"] == "ai.stream.completed"


class TestRoutingEvents:
    def test_routing_decided(self):
        event = routing_decided("local_first", "ollama", "local provider available")
        assert event["event_type"] == "ai.routing.decided"
        assert event["payload"]["policy"] == "local_first"
        assert event["payload"]["reason"] == "local provider available"


class TestModelEvents:
    def test_models_listed(self):
        event = models_listed("openrouter", 10)
        assert event["event_type"] == "ai.models.listed"
        assert event["payload"]["count"] == 10
