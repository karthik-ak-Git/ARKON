"""Repository pattern for Agent entity."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Agent


class AgentRepository:
    """Data access for Agent entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        workspace_id: uuid.UUID,
        name: str,
        agent_type: str = "generic",
        capabilities: list | None = None,
        config: dict | None = None,
    ) -> Agent:
        agent = Agent(
            workspace_id=workspace_id,
            name=name,
            agent_type=agent_type,
            capabilities=capabilities,
            config=config,
        )
        self._session.add(agent)
        await self._session.flush()
        return agent

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        result = await self._session.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self, workspace_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Agent]:
        result = await self._session.execute(
            select(Agent)
            .where(Agent.workspace_id == workspace_id)
            .order_by(Agent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> list[Agent]:
        result = await self._session.execute(
            select(Agent).where(Agent.status == status)
        )
        return list(result.scalars().all())

    async def update(
        self,
        agent: Agent,
        name: str | None = None,
        status: str | None = None,
        capabilities: list | None = None,
        config: dict | None = None,
    ) -> Agent:
        if name is not None:
            agent.name = name
        if status is not None:
            agent.status = status
        if capabilities is not None:
            agent.capabilities = capabilities
        if config is not None:
            agent.config = config
        await self._session.flush()
        return agent

    async def delete(self, agent: Agent) -> None:
        await self._session.delete(agent)
        await self._session.flush()
