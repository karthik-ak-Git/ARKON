"""OpenRouter provider — free models only."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import httpx

from app.ai.exceptions import ProviderAuthError, ProviderTimeoutError, ChatError, StreamError
from app.ai.interfaces import (
    AIModel, AIProviderBase, ChatRequest, ChatResponse, ProviderConfig,
    ProviderHealth, ProviderStatus, StreamEvent, StreamEventType,
)

_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(AIProviderBase):
    """OpenRouter cloud provider — configured for free models only."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        if not self._config.base_url:
            self._config.base_url = _BASE_URL

    async def authenticate(self) -> bool:
        if not self._config.api_key:
            self._authenticated = False
            return False
        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.get(
                    f"{self._config.base_url}/auth/key",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                )
                self._authenticated = resp.status_code == 200
                return self._authenticated
        except Exception:
            self._authenticated = False
            return False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self._authenticated:
            raise ProviderAuthError(f"{self.provider_id}: not authenticated")

        model = request.model or self._config.default_model
        payload = {
            "model": model,
            "messages": [m.to_dict() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(
                    f"{self._config.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                usage = data.get("usage", {})
                return ChatResponse(
                    content=choice["message"]["content"],
                    model=data.get("model", model),
                    provider_id=self.provider_id,
                    finish_reason=choice.get("finish_reason", "stop"),
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(f"{self.provider_id}: request timed out")
        except httpx.HTTPStatusError as exc:
            raise ChatError(f"{self.provider_id}: {exc.response.status_code}")
        except Exception as exc:
            raise ChatError(f"{self.provider_id}: {exc}")

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        if not self._authenticated:
            raise ProviderAuthError(f"{self.provider_id}: not authenticated")

        model = request.model or self._config.default_model
        payload = {
            "model": model,
            "messages": [m.to_dict() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self._config.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        chunk_str = line[6:]
                        if chunk_str.strip() == "[DONE]":
                            yield StreamEvent(event_type=StreamEventType.DONE)
                            return
                        try:
                            chunk = json.loads(chunk_str)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield StreamEvent(event_type=StreamEventType.CONTENT, content=content)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except httpx.TimeoutException:
            raise ProviderTimeoutError(f"{self.provider_id}: stream timed out")
        except Exception as exc:
            raise StreamError(f"{self.provider_id}: {exc}")

    async def list_models(self) -> list[AIModel]:
        if self._models:
            return self._models

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.get(
                    f"{self._config.base_url}/models",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
                models: list[AIModel] = []
                for m in data.get("data", []):
                    pricing = m.get("pricing", {})
                    prompt_cost = float(pricing.get("prompt", "0"))
                    completion_cost = float(pricing.get("completion", "0"))
                    is_free = prompt_cost == 0 and completion_cost == 0
                    models.append(AIModel(
                        model_id=m["id"],
                        name=m.get("name", m["id"]),
                        provider_id=self.provider_id,
                        context_window=m.get("context_length", 0),
                        is_free=is_free,
                        cost_per_1k_input=prompt_cost * 1000,
                        cost_per_1k_output=completion_cost * 1000,
                    ))
                self._models = [m for m in models if m.is_free]
                return self._models
        except Exception:
            return []
