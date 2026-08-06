# AI Gateway

Lightweight provider abstraction layer for ARKON's AI communication.

## Responsibilities

- Provider abstraction: all AI communication goes through the Gateway
- Authentication management
- Model listing per provider
- Smart routing (LOCAL_FIRST, CLOUD_FIRST, CHEAPEST, FASTEST, MANUAL)
- Unified chat and streaming interface

## Non-Responsibilities

- No prompt engineering, memory, caching, or workflow logic
- No business logic, video editing, coding, research, or automation
- No benchmark, telemetry, or prompt optimization

## Architecture

```
┌─────────────────────────────────────────┐
│              ARKON Kernel                │
├─────────────────────────────────────────┤
│              AI Gateway                  │
│  ┌───────────┐  ┌─────────────────────┐ │
│  │  Router   │  │  ProviderManager    │ │
│  │  (smart   │  │  (register, health, │ │
│  │  routing) │  │   enable/disable)   │ │
│  └─────┬─────┘  └─────────┬───────────┘ │
│        │                  │              │
│  ┌─────┴──────────────────┴───────────┐ │
│  │         Provider Registry          │ │
│  │  OpenRouter | Gemini | NVIDIA NIM  │ │
│  │  Ollama | Copilot | Gemini CLI    │ │
│  │  OpenCode                          │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Providers

| Provider | Type | Auth | Notes |
|----------|------|------|-------|
| OpenRouter | Cloud | API Key | Free models only |
| Gemini API | Cloud | API Key | Google's Gemini |
| NVIDIA NIM | Cloud | API Key | Cloud inference |
| Ollama | Local | None | Local inference |
| GitHub Copilot | Adapter | Token | Uses local CLI |
| Gemini CLI | Adapter | None | Uses local CLI |
| OpenCode | Adapter | None | Uses local CLI |

## Key Components

- **ProviderManager** — register/enable/disable providers, health checks, local detection
- **SmartRouter** — auto-select best provider given request + routing policy
- **ProviderConfig** — configuration per provider (API key, base URL, timeout, etc.)
- **ProviderHealth** — health status, latency, error tracking

## Routing Policies

- `LOCAL_FIRST` — prefer local providers (Ollama, adapters), fallback to cloud
- `CLOUD_FIRST` — prefer cloud providers, fallback to local
- `CHEAPEST` — prefer local (free) providers, fallback to cloud
- `FASTEST` — select provider with lowest latency
- `MANUAL` — caller explicitly chooses provider

## Usage

```python
from app.ai.manager import ProviderManager
from app.ai.router import SmartRouter
from app.ai.interfaces import ChatRequest, ChatMessage, MessageRole, RoutingPolicy

manager = ProviderManager()
router = SmartRouter(manager)

# Register a provider
from app.ai.interfaces import ProviderConfig, ProviderType
config = ProviderConfig(
    provider_id="openrouter",
    provider_type=ProviderType.CLOUD,
    display_name="OpenRouter",
    api_key="your-key",
)
manager.register(config)

# Route a chat request
request = ChatRequest(
    messages=[ChatMessage(role=MessageRole.USER, content="Hello")],
)
response = await router.route(request, policy=RoutingPolicy.LOCAL_FIRST)
```

## Tests

```bash
python -m pytest backend/app/ai/tests/ -v
```

119 tests covering interfaces, exceptions, models, events, providers, manager, and router.
