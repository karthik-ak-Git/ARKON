"""Tests for AI interfaces — enums, dataclasses, protocol, base class."""

import pytest

from app.ai.interfaces import (
    AIModel, AIProviderBase, ChatMessage, ChatRequest, ChatResponse,
    MessageRole, ProviderConfig, ProviderHealth, ProviderStatus,
    ProviderType, RoutingPolicy, StreamEvent, StreamEventType,
)


# ── Enums ────────────────────────────────────────────────────────────────────

class TestEnums:
    def test_message_role_values(self):
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_provider_status_values(self):
        assert ProviderStatus.AVAILABLE.value == "available"
        assert ProviderStatus.ERROR.value == "error"
        assert ProviderStatus.DISABLED.value == "disabled"
        assert ProviderStatus.UNKNOWN.value == "unknown"

    def test_provider_type_values(self):
        assert ProviderType.CLOUD.value == "cloud"
        assert ProviderType.LOCAL.value == "local"
        assert ProviderType.ADAPTER.value == "adapter"

    def test_routing_policy_values(self):
        assert RoutingPolicy.LOCAL_FIRST.value == "local_first"
        assert RoutingPolicy.CLOUD_FIRST.value == "cloud_first"
        assert RoutingPolicy.CHEAPEST.value == "cheapest"
        assert RoutingPolicy.FASTEST.value == "fastest"
        assert RoutingPolicy.MANUAL.value == "manual"

    def test_stream_event_type_values(self):
        assert StreamEventType.CONTENT.value == "content"
        assert StreamEventType.DONE.value == "done"
        assert StreamEventType.ERROR.value == "error"
        assert StreamEventType.METADATA.value == "metadata"


# ── Dataclasses ──────────────────────────────────────────────────────────────

class TestChatMessage:
    def test_creation(self):
        msg = ChatMessage(role=MessageRole.USER, content="hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "hello"

    def test_to_dict(self):
        msg = ChatMessage(role=MessageRole.ASSISTANT, content="hi")
        d = msg.to_dict()
        assert d == {"role": "assistant", "content": "hi"}

    def test_system_message(self):
        msg = ChatMessage(role=MessageRole.SYSTEM, content="be helpful")
        assert msg.to_dict()["role"] == "system"


class TestChatRequest:
    def test_defaults(self):
        req = ChatRequest(messages=[])
        assert req.messages == []
        assert req.temperature == 0.7
        assert req.max_tokens == 2048
        assert req.model == ""
        assert req.stream is False
        assert req.provider_id == ""

    def test_custom(self):
        req = ChatRequest(
            messages=[ChatMessage(role=MessageRole.USER, content="test")],
            temperature=0.5,
            max_tokens=1024,
            model="gpt-4",
            stream=True,
            provider_id="openrouter",
        )
        assert req.temperature == 0.5
        assert req.max_tokens == 1024
        assert req.model == "gpt-4"
        assert req.stream is True
        assert req.provider_id == "openrouter"

    def test_to_dict(self):
        req = ChatRequest(
            messages=[ChatMessage(role=MessageRole.USER, content="hi")],
            model="test",
        )
        d = req.to_dict()
        assert d["model"] == "test"
        assert d["messages"][0]["role"] == "user"


class TestChatResponse:
    def test_creation(self):
        resp = ChatResponse(
            content="hello",
            model="test",
            provider_id="test_provider",
        )
        assert resp.content == "hello"
        assert resp.model == "test"
        assert resp.finish_reason == "stop"

    def test_usage(self):
        resp = ChatResponse(
            content="hi",
            model="test",
            provider_id="test_provider",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert resp.usage["total_tokens"] == 15

    def test_to_dict(self):
        resp = ChatResponse(content="ok", model="m", provider_id="p")
        d = resp.to_dict()
        assert d["content"] == "ok"


class TestAIModel:
    def test_creation(self):
        m = AIModel(
            model_id="model-1",
            name="Test Model",
            provider_id="test_provider",
        )
        assert m.model_id == "model-1"
        assert m.is_free is True  # default is True
        assert m.capabilities == []

    def test_free_model(self):
        m = AIModel(
            model_id="model-2",
            name="Free Model",
            provider_id="test_provider",
            is_free=True,
        )
        assert m.is_free is True

    def test_to_dict(self):
        m = AIModel(model_id="m", name="M", provider_id="p")
        d = m.to_dict()
        assert d["model_id"] == "m"


class TestStreamEvent:
    def test_content_event(self):
        evt = StreamEvent(event_type=StreamEventType.CONTENT, content="hello")
        assert evt.event_type == StreamEventType.CONTENT
        assert evt.content == "hello"

    def test_done_event(self):
        evt = StreamEvent(event_type=StreamEventType.DONE)
        assert evt.event_type == StreamEventType.DONE
        assert evt.content == ""

    def test_to_dict(self):
        evt = StreamEvent(event_type=StreamEventType.CONTENT, content="x")
        d = evt.to_dict()
        assert d["content"] == "x"


class TestProviderHealth:
    def test_creation(self):
        h = ProviderHealth(provider_id="p1", status=ProviderStatus.AVAILABLE)
        assert h.provider_id == "p1"
        assert h.status == ProviderStatus.AVAILABLE
        assert h.latency_ms == 0.0
        assert h.error == ""

    def test_to_dict(self):
        h = ProviderHealth(provider_id="p1", status=ProviderStatus.ERROR, error="fail")
        d = h.to_dict()
        assert d["status"] == "error"
        assert d["error"] == "fail"


class TestProviderConfig:
    def test_defaults(self):
        c = ProviderConfig(
            provider_id="p1",
            provider_type=ProviderType.CLOUD,
            display_name="Test",
        )
        assert c.provider_type == ProviderType.CLOUD
        assert c.api_key == ""
        assert c.enabled is True

    def test_custom(self):
        c = ProviderConfig(
            provider_id="p1",
            provider_type=ProviderType.CLOUD,
            display_name="Gemini",
            api_key="key123",
            base_url="https://custom.api",
            enabled=False,
        )
        assert c.api_key == "key123"
        assert c.base_url == "https://custom.api"
        assert c.enabled is False

    def test_to_dict(self):
        c = ProviderConfig(
            provider_id="p1",
            provider_type=ProviderType.LOCAL,
            display_name="Ollama",
        )
        d = c.to_dict()
        assert d["provider_type"] == "local"
        assert d["has_api_key"] is False
