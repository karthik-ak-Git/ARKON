"""Repository pattern for Project entity."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Project


class ProjectRepository:
    """Data access for Project entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, workspace_id: uuid.UUID, name: str, description: str | None = None
    ) -> Project:
        project = Project(workspace_id=workspace_id, name=name, description=description)
        self._session.add(project)
        await self._session.flush()
        return project

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self._session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self, workspace_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Project]:
        result = await self._session.execute(
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(
        self,
        project: Project,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Project:
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status
        await self._session.flush()
        return project

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)
        await self._session.flush()
