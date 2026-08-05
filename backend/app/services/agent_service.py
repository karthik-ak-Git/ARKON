"""Agent service."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.agent_repo import AgentRepository
from app.schemas.schemas import AgentCreate, AgentRead, AgentUpdate

logger = get_logger(__name__)


class AgentService:
    """Handles agent business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AgentRepository(session)

    async def create_agent(
        self, workspace_id: uuid.UUID, data: AgentCreate
    ) -> AgentRead:
        agent = await self._repo.create(
            workspace_id=workspace_id,
            name=data.name,
            agent_type=data.agent_type,
            capabilities=data.capabilities,
            config=data.config,
        )
        logger.info("agent_created", agent_id=str(agent.id), name=data.name)
        return AgentRead.model_validate(agent)

    async def get_agent(self, agent_id: uuid.UUID) -> AgentRead | None:
        agent = await self._repo.get_by_id(agent_id)
        if agent is None:
            return None
        return AgentRead.model_validate(agent)

    async def list_agents(
        self, workspace_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[AgentRead]:
        agents = await self._repo.get_by_workspace(
            workspace_id, limit=limit, offset=offset
        )
        return [AgentRead.model_validate(a) for a in agents]

    async def update_agent(
        self, agent_id: uuid.UUID, data: AgentUpdate
    ) -> AgentRead | None:
        agent = await self._repo.get_by_id(agent_id)
        if agent is None:
            return None
        updated = await self._repo.update(
            agent,
            name=data.name,
            status=data.status,
            capabilities=data.capabilities,
            config=data.config,
        )
        return AgentRead.model_validate(updated)

    async def delete_agent(self, agent_id: uuid.UUID) -> bool:
        agent = await self._repo.get_by_id(agent_id)
        if agent is None:
            return False
        await self._repo.delete(agent)
        return True
