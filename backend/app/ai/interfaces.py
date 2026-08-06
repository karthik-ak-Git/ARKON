"""AI Gateway interfaces, types, and data structures.

Source of truth for all AI provider types.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Protocol


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProviderType(str, Enum):
    """Classification of AI providers."""
    CLOUD = "cloud"
    LOCAL = "local"
    ADAPTER = "adapter"


class ProviderStatus(str, Enum):
    """Current status of a provider."""
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    ERROR = "error"
    DISABLED = "disabled"


class RoutingPolicy(str, Enum):
    """Smart routing strategies."""
    LOCAL_FIRST = "local_first"
    CLOUD_FIRST = "cloud_first"
    CHEAPEST = "cheapest"
    FASTEST = "fastest"
    MANUAL = "manual"


class MessageRole(str, Enum):
    """Roles in a chat conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StreamEventType(str, Enum):
    """Types of events in a streaming response."""
    CONTENT = "content"
    DONE = "done"
    ERROR = "error"
    METADATA = "metadata"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AIModel:
    """Metadata for a single model offered by a provider."""
    model_id: str
    name: str
    provider_id: str
    context_window: int = 0
    max_output: int = 0
    is_free: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider_id": self.provider_id,
            "context_window": self.context_window,
            "max_output": self.max_output,
            "is_free": self.is_free,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "capabilities": self.capabilities,
        }


@dataclass(frozen=True)
class ChatMessage:
    """A single message in a chat conversation."""
    role: MessageRole
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass(frozen=True)
class ChatRequest:
    """Unified chat completion request."""
    messages: list[ChatMessage]
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    provider_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "messages": [m.to_dict() for m in self.messages],
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            "provider_id": self.provider_id,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ChatResponse:
    """Unified chat completion response."""
    content: str
    model: str
    provider_id: str
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider_id": self.provider_id,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class StreamEvent:
    """A single event in a streaming response."""
    event_type: StreamEventType
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"event_type": self.event_type.value}
        if self.content:
            d["content"] = self.content
        if self.metadata:
            d["metadata"] = self.metadata
        return d


@dataclass
class ProviderConfig:
    """Configuration for a provider instance."""
    provider_id: str
    provider_type: ProviderType
    display_name: str
    enabled: bool = True
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    timeout: float = 30.0
    max_retries: int = 2
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type.value,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "has_api_key": bool(self.api_key),
            "base_url": self.base_url,
            "default_model": self.default_model,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "extra": self.extra,
        }


@dataclass
class ProviderHealth:
    """Health check result for a provider."""
    provider_id: str
    status: ProviderStatus
    latency_ms: float = 0.0
    last_check: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Protocol — every provider must satisfy this
# ---------------------------------------------------------------------------

class AIProviderProtocol(Protocol):
    """Protocol that all AI providers must implement."""

    @property
    def provider_id(self) -> str: ...

    @property
    def config(self) -> ProviderConfig: ...

    async def authenticate(self) -> bool: ...

    async def chat(self, request: ChatRequest) -> ChatResponse: ...

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]: ...

    async def list_models(self) -> list[AIModel]: ...

    async def health(self) -> ProviderHealth: ...


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class AIProviderBase(ABC):
    """Base class for all AI providers. Implements common logic."""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._authenticated = False
        self._models: list[AIModel] = []

    @property
    def provider_id(self) -> str:
        return self._config.provider_id

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    @abstractmethod
    async def authenticate(self) -> bool:
        ...

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        ...

    @abstractmethod
    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        ...

    @abstractmethod
    async def list_models(self) -> list[AIModel]:
        ...

    async def health(self) -> ProviderHealth:
        start = time.monotonic()
        try:
            models = await self.list_models()
            latency = (time.monotonic() - start) * 1000
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.AVAILABLE if self._authenticated else ProviderStatus.UNAUTHENTICATED,
                latency_ms=latency,
                last_check=time.time(),
            )
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.ERROR,
                latency_ms=latency,
                last_check=time.time(),
                error=str(exc),
            )
