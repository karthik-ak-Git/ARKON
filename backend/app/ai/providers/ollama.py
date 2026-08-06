"""Ollama local provider."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.ai.exceptions import ProviderTimeoutError, ChatError, StreamError
from app.ai.interfaces import (
    AIModel, AIProviderBase, ChatRequest, ChatResponse, ProviderConfig,
    ProviderHealth, ProviderStatus, StreamEvent, StreamEventType,
)

_DEFAULT_URL = "http://localhost:11434"


class OllamaProvider(AIProviderBase):
    """Ollama local inference provider."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        if not self._config.base_url:
            self._config.base_url = _DEFAULT_URL
        self._authenticated = True  # local, no auth needed

    async def authenticate(self) -> bool:
        self._authenticated = True
        return True

    async def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self._config.default_model or "llama3.2"
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(f"{self._config.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return ChatResponse(
                    content=data["message"]["content"],
                    model=model,
                    provider_id=self.provider_id,
                    finish_reason="stop",
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    },
                )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(f"{self.provider_id}: request timed out")
        except httpx.HTTPStatusError as exc:
            raise ChatError(f"{self.provider_id}: {exc.response.status_code}")
        except Exception as exc:
            raise ChatError(f"{self.provider_id}: {exc}")

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        model = request.model or self._config.default_model or "llama3.2"
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                async with client.stream("POST", f"{self._config.base_url}/api/chat", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            if chunk.get("done"):
                                yield StreamEvent(event_type=StreamEventType.DONE)
                                return
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield StreamEvent(event_type=StreamEventType.CONTENT, content=content)
                        except json.JSONDecodeError:
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
                resp = await client.get(f"{self._config.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models: list[AIModel] = []
                for m in data.get("models", []):
                    models.append(AIModel(
                        model_id=m["name"],
                        name=m.get("name", m["name"]),
                        provider_id=self.provider_id,
                        is_free=True,
                    ))
                self._models = models
                return self._models
        except Exception:
            return []

    async def health(self) -> ProviderHealth:
        start = __import__("time").monotonic()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._config.base_url}/api/tags")
                latency = (__import__("time").monotonic() - start) * 1000
                return ProviderHealth(
                    provider_id=self.provider_id,
                    status=ProviderStatus.AVAILABLE if resp.status_code == 200 else ProviderStatus.ERROR,
                    latency_ms=latency,
                    last_check=__import__("time").time(),
                )
        except Exception as exc:
            latency = (__import__("time").monotonic() - start) * 1000
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.ERROR,
                latency_ms=latency,
                last_check=__import__("time").time(),
                error=str(exc),
            )
