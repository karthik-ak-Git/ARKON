"""AI Gateway request/response models for REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class MessageModel(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[MessageModel]
    model: str = ""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    stream: bool = False
    provider_id: str = ""


class UsageModel(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = ""
    content: str
    model: str
    provider_id: str
    finish_reason: str = "stop"
    usage: UsageModel = Field(default_factory=UsageModel)


# --- Streaming ---

class StreamChunk(BaseModel):
    event_type: str
    content: str = ""
    done: bool = False


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ModelInfo(BaseModel):
    model_id: str
    name: str
    provider_id: str
    context_window: int = 0
    max_output: int = 0
    is_free: bool = True


class ModelListResponse(BaseModel):
    models: list[ModelInfo]
    provider_id: str = ""


# ---------------------------------------------------------------------------
# Provider management
# ---------------------------------------------------------------------------

class ProviderConfigRequest(BaseModel):
    provider_id: str
    provider_type: str
    display_name: str = ""
    enabled: bool = True
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    timeout: float = 30.0
    max_retries: int = 2


class ProviderInfo(BaseModel):
    provider_id: str
    provider_type: str
    display_name: str
    enabled: bool
    has_api_key: bool
    status: str = "unknown"
    default_model: str = ""


class ProviderListResponse(BaseModel):
    providers: list[ProviderInfo]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    provider_id: str
    status: str
    latency_ms: float = 0.0
    error: str = ""


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

class RoutingPolicyRequest(BaseModel):
    policy: str = "local_first"
    manual_provider_id: str = ""


class RoutingDecision(BaseModel):
    provider_id: str
    model: str
    policy: str
    reason: str = ""
