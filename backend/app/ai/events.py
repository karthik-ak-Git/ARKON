"""AI Gateway event factory functions."""

from __future__ import annotations

import time
import uuid
from typing import Any


def _event(event_type: str, payload: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": time.time(),
        "payload": payload or {},
        **extra,
    }


def provider_registered(provider_id: str) -> dict[str, Any]:
    return _event("ai.provider.registered", {"provider_id": provider_id})


def provider_enabled(provider_id: str) -> dict[str, Any]:
    return _event("ai.provider.enabled", {"provider_id": provider_id})


def provider_disabled(provider_id: str) -> dict[str, Any]:
    return _event("ai.provider.disabled", {"provider_id": provider_id})


def provider_authenticated(provider_id: str) -> dict[str, Any]:
    return _event("ai.provider.authenticated", {"provider_id": provider_id})


def provider_error(provider_id: str, error: str) -> dict[str, Any]:
    return _event("ai.provider.error", {"provider_id": provider_id, "error": error})


def chat_completed(provider_id: str, model: str, tokens: int = 0) -> dict[str, Any]:
    return _event("ai.chat.completed", {
        "provider_id": provider_id,
        "model": model,
        "tokens": tokens,
    })


def chat_failed(provider_id: str, error: str) -> dict[str, Any]:
    return _event("ai.chat.failed", {"provider_id": provider_id, "error": error})


def stream_completed(provider_id: str, model: str) -> dict[str, Any]:
    return _event("ai.stream.completed", {"provider_id": provider_id, "model": model})


def routing_decided(policy: str, provider_id: str, reason: str = "") -> dict[str, Any]:
    return _event("ai.routing.decided", {
        "policy": policy,
        "provider_id": provider_id,
        "reason": reason,
    })


def models_listed(provider_id: str, count: int) -> dict[str, Any]:
    return _event("ai.models.listed", {"provider_id": provider_id, "count": count})
