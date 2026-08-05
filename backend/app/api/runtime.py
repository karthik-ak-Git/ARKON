"""ARKON Runtime - REST API Endpoints.

Agent Runtime API.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.runtime.manager import AgentManager

router = APIRouter(prefix="/api/runtime", tags=["runtime"])

# Will be set during app startup
_agent_manager: AgentManager | None = None


def set_agent_manager(manager: AgentManager) -> None:
    global _agent_manager
    _agent_manager = manager


def get_agent_manager() -> AgentManager:
    if _agent_manager is None:
        raise HTTPException(status_code=503, detail="Runtime not initialized")
    return _agent_manager


# =============================================================================
# Request/Response Models
# =============================================================================


class AgentSpawnRequest(BaseModel):
    agent_type: str = Field(..., description="Agent type to spawn")
    name: str = Field(..., description="Agent name")
    config: dict[str, Any] | None = Field(None, description="Agent configuration")
    workspace_id: str | None = Field(None, description="Workspace ID")


class AgentTaskRequest(BaseModel):
    task_type: str = Field("unknown", description="Task type")
    payload: dict[str, Any] = Field(default_factory=dict, description="Task payload")
    timeout: float = Field(300.0, description="Task timeout in seconds")


class AgentHeartbeatRequest(BaseModel):
    status: dict[str, Any] = Field(
        default_factory=lambda: {
            "status": "running",
            "cpu": 0.0,
            "memory": 0.0,
            "task_progress": 0.0,
            "current_activity": "idle",
        },
        description="Heartbeat status",
    )


class AgentResponse(BaseModel):
    id: str
    agent_type: str
    name: str
    state: str
    workspace_id: str | None = None
    created_at: float
    started_at: float | None = None
    error: str | None = None


class AgentListResponse(BaseModel):
    agents: list[dict[str, Any]]
    total: int


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/agents")
async def list_agents() -> AgentListResponse:
    """List all active agents."""
    manager = get_agent_manager()
    agents = await manager.list_active()
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> dict[str, Any]:
    """Get agent by ID."""
    manager = get_agent_manager()
    agent = await manager.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent.to_dict()


@router.post("/agents")
async def create_agent(request: AgentSpawnRequest) -> dict[str, Any]:
    """Create a new agent."""
    manager = get_agent_manager()
    try:
        agent_id = await manager.spawn(
            agent_type=request.agent_type,
            name=request.name,
            config=request.config,
            workspace_id=request.workspace_id,
        )
        agent = await manager.get(agent_id)
        return agent.to_dict() if agent else {"id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str) -> dict[str, str]:
    """Delete an agent."""
    manager = get_agent_manager()
    try:
        await manager.destroy(agent_id)
        return {"status": "deleted", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/start")
async def start_agent(agent_id: str) -> dict[str, str]:
    """Start an agent."""
    manager = get_agent_manager()
    try:
        await manager.start(agent_id)
        return {"status": "started", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/pause")
async def pause_agent(agent_id: str) -> dict[str, str]:
    """Pause an agent."""
    manager = get_agent_manager()
    try:
        await manager.pause(agent_id)
        return {"status": "paused", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/resume")
async def resume_agent(agent_id: str) -> dict[str, str]:
    """Resume an agent."""
    manager = get_agent_manager()
    try:
        await manager.resume(agent_id)
        return {"status": "resumed", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/cancel")
async def cancel_agent(agent_id: str) -> dict[str, str]:
    """Cancel an agent."""
    manager = get_agent_manager()
    try:
        await manager.cancel(agent_id)
        return {"status": "cancelled", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/health")
async def get_agent_health(agent_id: str) -> dict[str, Any]:
    """Get agent health."""
    manager = get_agent_manager()
    try:
        return await manager.health(agent_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/heartbeat")
async def get_agent_heartbeat(agent_id: str) -> dict[str, Any]:
    """Get agent heartbeat."""
    manager = get_agent_manager()
    try:
        return await manager.heartbeat(agent_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/heartbeat")
async def send_agent_heartbeat(
    agent_id: str, request: AgentHeartbeatRequest
) -> dict[str, Any]:
    """Send agent heartbeat."""
    manager = get_agent_manager()
    try:
        return await manager.heartbeat(agent_id, request.status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/execute")
async def execute_agent_task(
    agent_id: str, request: AgentTaskRequest
) -> dict[str, Any]:
    """Execute a task for an agent."""
    manager = get_agent_manager()
    try:
        result = await manager.execute(agent_id, {
            "type": request.task_type,
            "payload": request.payload,
            "timeout": request.timeout,
        })
        return {"agent_id": agent_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/state")
async def get_agent_state(agent_id: str) -> dict[str, Any]:
    """Get agent state machine."""
    manager = get_agent_manager()
    agent = await manager.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {
        "agent_id": agent_id,
        "state": agent.state.value,
    }


# =============================================================================
# Registry Endpoints
# =============================================================================


@router.get("/registry")
async def list_registry() -> dict[str, Any]:
    """List all registered agent types."""
    manager = get_agent_manager()
    agents = await manager.get_registry().list_all()
    return {"agents": agents, "count": len(agents)}


@router.get("/registry/{agent_type}")
async def get_registry_entry(agent_type: str) -> dict[str, Any]:
    """Get registry entry for agent type."""
    manager = get_agent_manager()
    entry = await manager.get_registry().get(agent_type)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Agent type not found: {agent_type}")
    return entry


# =============================================================================
# Capability Endpoints
# =============================================================================


@router.get("/capabilities")
async def list_capabilities() -> dict[str, Any]:
    """List all capabilities."""
    manager = get_agent_manager()
    caps = manager.get_capabilities().to_dict()
    return {"capabilities": caps, "count": len(caps)}


@router.get("/capabilities/{capability}")
async def find_agents_by_capability(capability: str) -> dict[str, Any]:
    """Find agents that provide a capability."""
    manager = get_agent_manager()
    agents = manager.get_capabilities().find(capability)
    return {"capability": capability, "agents": agents}


# =============================================================================
# Resource Endpoints
# =============================================================================


@router.get("/resources")
async def get_resources() -> dict[str, Any]:
    """Get resource usage."""
    manager = get_agent_manager()
    return manager.get_resources().to_dict()
