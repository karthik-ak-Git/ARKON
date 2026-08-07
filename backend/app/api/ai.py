"""AI Gateway REST API.

Provider management, chat completions, model listing, and routing policy.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.exceptions import (
    AIGatewayError,
    NoProviderAvailableError,
    ProviderNotFoundError,
)
from app.ai.interfaces import ChatRequest, MessageRole, ProviderConfig, ProviderType, RoutingPolicy
from app.ai.manager import ProviderManager
from app.ai.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    HealthResponse,
    MessageModel,
    ModelInfo,
    ModelListResponse,
    ProviderConfigRequest,
    ProviderInfo,
    ProviderListResponse,
    RoutingDecision,
    RoutingPolicyRequest,
    UsageModel,
)
from app.ai.router import SmartRouter

router = APIRouter(prefix="/ai", tags=["ai"])

# Singletons — initialized lazily on first request
_manager: ProviderManager | None = None
_router: SmartRouter | None = None
_current_policy: RoutingPolicy = RoutingPolicy.LOCAL_FIRST


def _get_manager() -> ProviderManager:
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager


def _get_router() -> SmartRouter:
    global _router
    if _router is None:
        _router = SmartRouter(_get_manager())
    return _router


# ---------------------------------------------------------------------------
# Provider management
# ---------------------------------------------------------------------------

@router.get("/providers", response_model=ProviderListResponse)
async def list_providers() -> ProviderListResponse:
    """List all registered AI providers."""
    mgr = _get_manager()
    providers: list[ProviderInfo] = []
    for pid in mgr.list_providers():
        config = mgr.get_config(pid)
        providers.append(
            ProviderInfo(
                provider_id=pid,
                provider_type=config.provider_type.value
                if isinstance(config.provider_type, ProviderType)
                else str(config.provider_type),
                display_name=config.display_name,
                enabled=mgr.is_enabled(pid),
                has_api_key=bool(config.api_key),
                status="enabled" if mgr.is_enabled(pid) else "disabled",
                default_model=config.default_model or "",
            )
        )
    return ProviderListResponse(providers=providers)


@router.post("/providers", response_model=ProviderInfo)
async def register_provider(req: ProviderConfigRequest) -> ProviderInfo:
    """Register a new AI provider."""
    mgr = _get_manager()
    try:
        pt = ProviderType(req.provider_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider_type: {req.provider_type}")

    config = ProviderConfig(
        provider_id=req.provider_id,
        provider_type=pt,
        display_name=req.display_name or req.provider_id,
        enabled=req.enabled,
        api_key=req.api_key,
        base_url=req.base_url,
        default_model=req.default_model,
        timeout=req.timeout,
    )
    try:
        mgr.register(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ProviderInfo(
        provider_id=req.provider_id,
        provider_type=pt.value,
        display_name=config.display_name,
        enabled=config.enabled,
        has_api_key=bool(config.api_key),
        status="enabled" if config.enabled else "disabled",
        default_model=config.default_model,
    )


@router.patch("/providers/{provider_id}/enable")
async def enable_provider(provider_id: str) -> dict:
    """Enable a provider."""
    mgr = _get_manager()
    try:
        mgr.enable(provider_id)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"provider_id": provider_id, "enabled": True}


@router.patch("/providers/{provider_id}/disable")
async def disable_provider(provider_id: str) -> dict:
    """Disable a provider."""
    mgr = _get_manager()
    try:
        mgr.disable(provider_id)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"provider_id": provider_id, "enabled": False}


@router.delete("/providers/{provider_id}")
async def unregister_provider(provider_id: str) -> dict:
    """Unregister a provider."""
    mgr = _get_manager()
    mgr.unregister(provider_id)
    return {"provider_id": provider_id, "removed": True}


@router.put("/providers/{provider_id}", response_model=ProviderInfo)
async def update_provider_config(provider_id: str, req: ProviderConfigRequest) -> ProviderInfo:
    """Update a provider's configuration."""
    mgr = _get_manager()
    try:
        mgr.update_config(
            provider_id,
            api_key=req.api_key,
            base_url=req.base_url,
            default_model=req.default_model,
            timeout=req.timeout,
            enabled=req.enabled,
        )
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    config = mgr.get_config(provider_id)
    return ProviderInfo(
        provider_id=provider_id,
        provider_type=config.provider_type.value
        if isinstance(config.provider_type, ProviderType)
        else str(config.provider_type),
        display_name=config.display_name,
        enabled=mgr.is_enabled(provider_id),
        has_api_key=bool(config.api_key),
        status="enabled" if mgr.is_enabled(provider_id) else "disabled",
        default_model=config.default_model or "",
    )


@router.get("/providers/{provider_id}/health", response_model=HealthResponse)
async def provider_health(provider_id: str) -> HealthResponse:
    """Check health of a specific provider."""
    mgr = _get_manager()
    try:
        health = await mgr.check_health(provider_id)
    except ProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AIGatewayError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return HealthResponse(
        provider_id=health.provider_id,
        status=health.status.value,
        latency_ms=health.latency_ms or 0.0,
        error=health.error or "",
    )


@router.get("/providers/health")
async def all_providers_health() -> dict[str, HealthResponse]:
    """Check health of all enabled providers."""
    mgr = _get_manager()
    results = await mgr.check_all_health()
    return {
        pid: HealthResponse(
            provider_id=h.provider_id,
            status=h.status.value,
            latency_ms=h.latency_ms or 0.0,
            error=h.error or "",
        )
        for pid, h in results.items()
    }


@router.post("/providers/detect-local")
async def detect_local_providers() -> dict:
    """Auto-detect available local providers."""
    mgr = _get_manager()
    detected = await mgr.detect_local_providers()
    return {"detected": detected}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@router.get("/models", response_model=ModelListResponse)
async def list_models(provider_id: str = "") -> ModelListResponse:
    """List available models from a provider or all providers."""
    mgr = _get_manager()
    models: list[ModelInfo] = []

    provider_ids = [provider_id] if provider_id else mgr.list_enabled()

    for pid in provider_ids:
        try:
            provider = mgr.get(pid)
            ai_models = await provider.list_models()
            for m in ai_models:
                models.append(
                    ModelInfo(
                        model_id=m.id,
                        name=m.name,
                        provider_id=m.provider,
                        context_window=m.context_window,
                        max_output=m.max_output,
                        is_free=m.is_free,
                    )
                )
        except Exception:
            continue

    return ModelListResponse(models=models, provider_id=provider_id)


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatCompletionResponse)
async def chat_completion(req: ChatCompletionRequest) -> ChatCompletionResponse:
    """Send a chat completion request through the AI Gateway."""
    router_instance = _get_router()

    messages = [
        ChatRequest.Message(role=MessageRole(m.role), content=m.content)
        for m in req.messages
    ]

    chat_request = ChatRequest(
        messages=messages,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        stream=False,
    )

    try:
        policy = _current_policy
        preferred = req.provider_id or None
        response = await router_instance.route(chat_request, policy=policy)
    except NoProviderAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIGatewayError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatCompletionResponse(
        content=response.content,
        model=response.model,
        provider_id=response.provider_id,
        finish_reason=response.finish_reason,
        usage=UsageModel(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        ),
    )


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

@router.get("/routing")
async def get_routing_policy() -> RoutingDecision:
    """Get the current routing policy."""
    return RoutingDecision(
        provider_id="",
        model="",
        policy=_current_policy.value,
        reason="Current policy setting",
    )


@router.put("/routing")
async def set_routing_policy(req: RoutingPolicyRequest) -> RoutingDecision:
    """Set the routing policy."""
    global _current_policy
    try:
        _current_policy = RoutingPolicy(req.policy)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy: {req.policy}. Must be one of: {[p.value for p in RoutingPolicy]}",
        )

    return RoutingDecision(
        provider_id=req.manual_provider_id or "",
        model="",
        policy=_current_policy.value,
        reason=f"Policy updated to {_current_policy.value}",
    )
