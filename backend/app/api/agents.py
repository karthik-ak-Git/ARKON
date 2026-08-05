"""Agent API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.schemas.schemas import AgentCreate, AgentRead, AgentUpdate
from app.services.agent_service import AgentService

router = APIRouter(prefix="/workspaces/{workspace_id}/agents", tags=["agents"])


@router.post("/", response_model=AgentRead, status_code=201)
async def create_agent(
    workspace_id: uuid.UUID,
    data: AgentCreate,
    session: AsyncSession = Depends(get_db_session),
) -> AgentRead:
    service = AgentService(session)
    return await service.create_agent(workspace_id, data)


@router.get("/", response_model=list[AgentRead])
async def list_agents(
    workspace_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> list[AgentRead]:
    service = AgentService(session)
    return await service.list_agents(workspace_id, limit=limit, offset=offset)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> AgentRead:
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    if agent is None or agent.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: AgentUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> AgentRead:
    service = AgentService(session)
    agent = await service.update_agent(agent_id, data)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = AgentService(session)
    deleted = await service.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
