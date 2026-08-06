"""AI Gateway exception hierarchy."""

from __future__ import annotations


class AIGatewayError(Exception):
    """Base exception for all AI Gateway errors."""


# --- Provider errors ---

class ProviderError(AIGatewayError):
    """Base for provider-specific errors."""


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider does not exist."""


class ProviderDisabledError(ProviderError):
    """Raised when trying to use a disabled provider."""


class ProviderAuthError(ProviderError):
    """Raised when authentication with a provider fails."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider rate-limits the request."""


# --- Model errors ---

class ModelNotFoundError(AIGatewayError):
    """Raised when a requested model is not available."""


# --- Routing errors ---

class RoutingError(AIGatewayError):
    """Raised when the smart router cannot satisfy a request."""


class NoProviderAvailableError(RoutingError):
    """Raised when no provider matches the routing policy."""


# --- Request errors ---

class ChatError(AIGatewayError):
    """Raised when a chat request fails."""


class StreamError(AIGatewayError):
    """Raised when a streaming response fails."""


class RequestValidationError(AIGatewayError):
    """Raised when a request fails validation."""
