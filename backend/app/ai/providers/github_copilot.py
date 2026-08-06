"""GitHub Copilot adapter — wraps Copilot's CLI HTTP interface."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import httpx

from app.ai.exceptions import ProviderAuthError, ProviderTimeoutError, ChatError, StreamError
from app.ai.interfaces import (
    AIModel, AIProviderBase, ChatRequest, ChatResponse, ProviderConfig,
    StreamEvent, StreamEventType,
)


class GitHubCopilotProvider(AIProviderBase):
    """GitHub Copilot adapter.

    Uses the Copilot Chat API via a token obtained from the GitHub CLI.
    """

    _TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
    _CHAT_URL = "https://api.githubcopilot.com/chat/completions"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._copilot_token: str = ""

    async def _get_copilot_token(self) -> str:
        """Exchange GitHub token for a short-lived Copilot token."""
        if self._copilot_token:
            return self._copilot_token
        github_token = self._config.api_key
        if not github_token:
            raise ProviderAuthError(f"{self.provider_id}: no GitHub token configured")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self._TOKEN_URL,
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/json",
                    "Editor-Version": "ARKON/1.0",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._copilot_token = data.get("token", "")
            return self._copilot_token

    async def authenticate(self) -> bool:
        if not self._config.api_key:
            self._authenticated = False
            return False
        try:
            await self._get_copilot_token()
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self._authenticated:
            raise ProviderAuthError(f"{self.provider_id}: not authenticated")

        token = await self._get_copilot_token()
        model = request.model or "copilot-chat"
        payload = {
            "model": model,
            "messages": [m.to_dict() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(
                    self._CHAT_URL,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Editor-Version": "ARKON/1.0",
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

        token = await self._get_copilot_token()
        model = request.model or "copilot-chat"
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
                    self._CHAT_URL,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Editor-Version": "ARKON/1.0",
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
        return [
            AIModel(
                model_id="copilot-chat",
                name="GitHub Copilot",
                provider_id=self.provider_id,
                is_free=False,
                capabilities=["chat", "code"],
            ),
            AIModel(
                model_id="copilot-edit",
                name="GitHub Copilot Edit",
                provider_id=self.provider_id,
                is_free=False,
                capabilities=["code"],
            ),
        ]
