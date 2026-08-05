"""Repository pattern for data access.

Repositories encapsulate query logic.
Services call repositories. Controllers call services.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Workspace


class WorkspaceRepository:
    """Data access for Workspace entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, description: str | None = None) -> Workspace:
        workspace = Workspace(name=name, description=description)
        self._session.add(workspace)
        await self._session.flush()
        return workspace

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        result = await self._session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 50, offset: int = 0) -> list[Workspace]:
        result = await self._session.execute(
            select(Workspace).order_by(Workspace.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update(
        self,
        workspace: Workspace,
        name: str | None = None,
        description: str | None = None,
        settings: dict | None = None,
    ) -> Workspace:
        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        if settings is not None:
            workspace.settings = settings
        await self._session.flush()
        return workspace

    async def delete(self, workspace: Workspace) -> None:
        await self._session.delete(workspace)
        await self._session.flush()

    async def count(self) -> int:
        result = await self._session.execute(select(Workspace))
        return len(result.scalars().all())
