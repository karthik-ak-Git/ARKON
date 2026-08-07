# AI Gateway

Unified interface to multiple AI providers.

## Supported Providers

| Provider | Type | Auth |
|----------|------|------|
| OpenRouter | Cloud | API Key |
| Google Gemini | Cloud | API Key |
| NVIDIA NIM | Cloud | API Key |
| Ollama | Local | None |
| GitHub Copilot | Adapter | Token |
| Gemini CLI | Adapter | None |
| OpenCode | Adapter | None |

## Usage

```python
from app.ai.manager import AIManager

manager = AIManager()
response = await manager.complete(
    provider="openrouter",
    model="meta-llama/llama-3-8b-instruct",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Adding Providers

Implement the `AIProvider` interface:

```python
class AIProvider(Protocol):
    async def complete(self, model, messages, **kwargs) -> str: ...
    async def stream(self, model, messages, **kwargs) -> AsyncIterator[str]: ...
```

Register in `app/ai/providers/` and add to the manager.
