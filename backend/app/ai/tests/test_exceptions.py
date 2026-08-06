"""Tests for AI exceptions module."""

import pytest

from app.ai.exceptions import (
    AIGatewayError,
    ChatError,
    ModelNotFoundError,
    NoProviderAvailableError,
    ProviderAuthError,
    ProviderDisabledError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    RequestValidationError,
    RoutingError,
    StreamError,
)


class TestExceptionHierarchy:
    """Verify all exceptions inherit from AIGatewayError."""

    def test_base_exception(self):
        with pytest.raises(AIGatewayError):
            raise AIGatewayError("test")

    @pytest.mark.parametrize("exc_class", [
        ProviderNotFoundError,
        ProviderDisabledError,
        ProviderAuthError,
        ProviderTimeoutError,
        ProviderRateLimitError,
        ModelNotFoundError,
        RoutingError,
        NoProviderAvailableError,
        ChatError,
        StreamError,
        RequestValidationError,
    ])
    def test_inherits_from_base(self, exc_class):
        assert issubclass(exc_class, AIGatewayError)

    def test_provider_not_found(self):
        with pytest.raises(ProviderNotFoundError, match="not found"):
            raise ProviderNotFoundError("not found")

    def test_provider_disabled(self):
        with pytest.raises(ProviderDisabledError, match="disabled"):
            raise ProviderDisabledError("disabled")

    def test_provider_auth_error(self):
        with pytest.raises(ProviderAuthError, match="unauthorized"):
            raise ProviderAuthError("unauthorized")

    def test_provider_timeout(self):
        with pytest.raises(ProviderTimeoutError, match="timed out"):
            raise ProviderTimeoutError("timed out")

    def test_provider_rate_limit(self):
        with pytest.raises(ProviderRateLimitError, match="rate limited"):
            raise ProviderRateLimitError("rate limited")

    def test_model_not_found(self):
        with pytest.raises(ModelNotFoundError, match="no model"):
            raise ModelNotFoundError("no model")

    def test_routing_error(self):
        with pytest.raises(RoutingError, match="routing failed"):
            raise RoutingError("routing failed")

    def test_no_provider_available(self):
        with pytest.raises(NoProviderAvailableError, match="no providers"):
            raise NoProviderAvailableError("no providers")

    def test_chat_error(self):
        with pytest.raises(ChatError, match="chat failed"):
            raise ChatError("chat failed")

    def test_stream_error(self):
        with pytest.raises(StreamError, match="stream failed"):
            raise StreamError("stream failed")

    def test_request_validation_error(self):
        with pytest.raises(RequestValidationError, match="invalid"):
            raise RequestValidationError("invalid")
