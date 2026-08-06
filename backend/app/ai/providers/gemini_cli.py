"""Gemini CLI adapter — wraps the Gemini CLI tool."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.ai.exceptions import ProviderTimeoutError, ChatError, StreamError
from app.ai.interfaces import (
    AIModel, AIProviderBase, ChatRequest, ChatResponse, ProviderConfig,
    StreamEvent, StreamEventType,
)


class GeminiCLIProvider(AIProviderBase):
    """Gemini CLI adapter.

    Wraps the `gemini` CLI tool for local execution.
    Requires the Gemini CLI to be installed and available on PATH.
    """

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._authenticated = True  # CLI handles auth via gcloud

    async def authenticate(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "gemini", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            self._authenticated = proc.returncode == 0
            return self._authenticated
        except Exception:
            self._authenticated = False
            return False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        prompt = "\n".join(m.content for m in request.messages)
        model = request.model or ""

        args = ["gemini", "-p", prompt]
        if model:
            args.extend(["-m", model])

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self._config.timeout)

            if proc.returncode != 0:
                raise ChatError(f"{self.provider_id}: {stderr.decode().strip()}")

            return ChatResponse(
                content=stdout.decode().strip(),
                model=model or "gemini-cli",
                provider_id=self.provider_id,
                finish_reason="stop",
            )
        except asyncio.TimeoutError:
            raise ProviderTimeoutError(f"{self.provider_id}: request timed out")
        except ChatError:
            raise
        except Exception as exc:
            raise ChatError(f"{self.provider_id}: {exc}")

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        prompt = "\n".join(m.content for m in request.messages)
        model = request.model or ""

        args = ["gemini", "-p", prompt]
        if model:
            args.extend(["-m", model])

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            assert proc.stdout is not None
            while True:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=self._config.timeout)
                if not line:
                    break
                text = line.decode().strip()
                if text:
                    yield StreamEvent(event_type=StreamEventType.CONTENT, content=text)

            await proc.wait()
            yield StreamEvent(event_type=StreamEventType.DONE)
        except asyncio.TimeoutError:
            raise ProviderTimeoutError(f"{self.provider_id}: stream timed out")
        except Exception as exc:
            raise StreamError(f"{self.provider_id}: {exc}")

    async def list_models(self) -> list[AIModel]:
        return [
            AIModel(
                model_id="gemini-cli",
                name="Gemini CLI",
                provider_id=self.provider_id,
                is_free=True,
                capabilities=["chat", "code"],
            ),
        ]
