"""Gemini API provider."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.ai.exceptions import ProviderAuthError, ProviderTimeoutError, ChatError, StreamError
from app.ai.interfaces import (
    AIModel, AIProviderBase, ChatRequest, ChatResponse, ProviderConfig,
    StreamEvent, StreamEventType,
)

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(AIProviderBase):
    """Google Gemini API provider."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        if not self._config.base_url:
            self._config.base_url = _BASE_URL

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _url(self, model: str, action: str = "generateContent") -> str:
        return f"{self._config.base_url}/models/{model}:{action}?key={self._config.api_key}"

    async def authenticate(self) -> bool:
        if not self._config.api_key:
            self._authenticated = False
            return False
        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.get(
                    f"{self._config.base_url}/models?key={self._config.api_key}",
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
        contents = []
        for m in request.messages:
            role = "user" if m.role.value in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(
                    self._url(model),
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                usage_meta = data.get("usageMetadata", {})
                return ChatResponse(
                    content=text,
                    model=model,
                    provider_id=self.provider_id,
                    finish_reason=data["candidates"][0].get("finishReason", "STOP"),
                    usage={
                        "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                        "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                        "total_tokens": usage_meta.get("totalTokenCount", 0),
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
        contents = []
        for m in request.messages:
            role = "user" if m.role.value in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                async with client.stream(
                    "POST",
                    self._url(model, "streamGenerateContent?alt=sse&key=" + self._config.api_key),
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        try:
                            chunk = json.loads(line[6:])
                            text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                            yield StreamEvent(event_type=StreamEventType.CONTENT, content=text)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                    yield StreamEvent(event_type=StreamEventType.DONE)
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
                    f"{self._config.base_url}/models?key={self._config.api_key}",
                )
                resp.raise_for_status()
                data = resp.json()
                models: list[AIModel] = []
                for m in data.get("models", []):
                    models.append(AIModel(
                        model_id=m["name"].split("/")[-1],
                        name=m.get("displayName", m["name"]),
                        provider_id=self.provider_id,
                        context_window=m.get("inputTokenLimit", 0),
                        max_output=m.get("outputTokenLimit", 0),
                        is_free=True,
                        capabilities=m.get("supportedGenerationMethods", []),
                    ))
                self._models = models
                return self._models
        except Exception:
            return []
