"""AI Gateway — provider abstraction layer for AI communication."""

from app.ai.interfaces import (
    AIModel, AIProviderBase, AIProviderProtocol, ChatMessage, ChatRequest,
    ChatResponse, MessageRole, ProviderConfig, ProviderHealth, ProviderStatus,
    RoutingPolicy, StreamEvent, StreamEventType,
)
from app.ai.manager import ProviderManager
from app.ai.router import SmartRouter

__all__ = [
    "AIModel",
    "AIProviderBase",
    "AIProviderProtocol",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "MessageRole",
    "ProviderConfig",
    "ProviderHealth",
    "ProviderStatus",
    "ProviderManager",
    "RoutingPolicy",
    "SmartRouter",
    "StreamEvent",
    "StreamEventType",
]
