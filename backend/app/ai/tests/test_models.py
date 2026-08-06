"""Tests for AI Pydantic models."""

import pytest

from app.ai.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    MessageModel,
    ModelInfo,
    ModelListResponse,
    ProviderConfigRequest,
    ProviderInfo,
    ProviderListResponse,
    HealthResponse,
    RoutingPolicyRequest,
    RoutingDecision,
    StreamChunk,
    UsageModel,
)


class TestMessageModel:
    def test_creation(self):
        m = MessageModel(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"


class TestChatCompletionRequest:
    def test_defaults(self):
        m = ChatCompletionRequest(messages=[MessageModel(role="user", content="hi")])
        assert m.temperature == 0.7
        assert m.max_tokens == 2048
        assert m.stream is False
        assert m.provider_id == ""

    def test_custom(self):
        m = ChatCompletionRequest(
            messages=[MessageModel(role="user", content="test")],
            temperature=0.3,
            max_tokens=1024,
            model="gpt-4",
            provider_id="openrouter",
        )
        assert m.temperature == 0.3
        assert m.max_tokens == 1024
        assert m.model == "gpt-4"
        assert m.provider_id == "openrouter"


class TestChatCompletionResponse:
    def test_creation(self):
        m = ChatCompletionResponse(
            content="hello",
            model="test",
            provider_id="test_provider",
        )
        assert m.content == "hello"
        assert m.finish_reason == "stop"


class TestUsageModel:
    def test_defaults(self):
        m = UsageModel()
        assert m.prompt_tokens == 0
        assert m.total_tokens == 0


class TestModelInfo:
    def test_creation(self):
        m = ModelInfo(model_id="m1", name="Test", provider_id="p1")
        assert m.model_id == "m1"
        assert m.is_free is True


class TestStreamChunk:
    def test_content(self):
        m = StreamChunk(event_type="content", content="hello")
        assert m.content == "hello"

    def test_done(self):
        m = StreamChunk(event_type="done", done=True)
        assert m.done is True


class TestProviderConfigRequest:
    def test_creation(self):
        m = ProviderConfigRequest(provider_id="p1", provider_type="openrouter")
        assert m.enabled is True
        assert m.timeout == 30.0


class TestProviderInfo:
    def test_creation(self):
        m = ProviderInfo(
            provider_id="p1",
            provider_type="openrouter",
            display_name="OpenRouter",
            enabled=True,
            has_api_key=True,
        )
        assert m.status == "unknown"


class TestHealthResponse:
    def test_creation(self):
        m = HealthResponse(provider_id="p1", status="available")
        assert m.latency_ms == 0.0


class TestRoutingPolicyRequest:
    def test_defaults(self):
        m = RoutingPolicyRequest()
        assert m.policy == "local_first"
        assert m.manual_provider_id == ""


class TestRoutingDecision:
    def test_creation(self):
        m = RoutingDecision(
            provider_id="ollama",
            model="llama3",
            policy="local_first",
            reason="local available",
        )
        assert m.reason == "local available"
