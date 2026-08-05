"""Project service."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.project_repo import ProjectRepository
from app.schemas.schemas import ProjectCreate, ProjectRead, ProjectUpdate

logger = get_logger(__name__)


class ProjectService:
    """Handles project business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectRepository(session)

    async def create_project(
        self, workspace_id: uuid.UUID, data: ProjectCreate
    ) -> ProjectRead:
        project = await self._repo.create(
            workspace_id=workspace_id, name=data.name, description=data.description
        )
        logger.info(
            "project_created",
            project_id=str(project.id),
            workspace_id=str(workspace_id),
        )
        return ProjectRead.model_validate(project)

    async def get_project(self, project_id: uuid.UUID) -> ProjectRead | None:
        project = await self._repo.get_by_id(project_id)
        if project is None:
            return None
        return ProjectRead.model_validate(project)

    async def list_projects(
        self, workspace_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[ProjectRead]:
        projects = await self._repo.get_by_workspace(
            workspace_id, limit=limit, offset=offset
        )
        return [ProjectRead.model_validate(p) for p in projects]

    async def update_project(
        self, project_id: uuid.UUID, data: ProjectUpdate
    ) -> ProjectRead | None:
        project = await self._repo.get_by_id(project_id)
        if project is None:
            return None
        updated = await self._repo.update(
            project, name=data.name, description=data.description, status=data.status
        )
        return ProjectRead.model_validate(updated)

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        project = await self._repo.get_by_id(project_id)
        if project is None:
            return False
        await self._repo.delete(project)
        return True
