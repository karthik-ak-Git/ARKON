"""Workspace service.

Business logic for workspace operations.
Services call repositories. Controllers call services.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.workspace_repo import WorkspaceRepository
from app.schemas.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate

logger = get_logger(__name__)


class WorkspaceService:
    """Handles workspace business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WorkspaceRepository(session)

    async def create_workspace(self, data: WorkspaceCreate) -> WorkspaceRead:
        """Create a new workspace."""
        workspace = await self._repo.create(name=data.name, description=data.description)
        logger.info("workspace_created", workspace_id=str(workspace.id), name=data.name)
        return WorkspaceRead.model_validate(workspace)

    async def get_workspace(self, workspace_id: uuid.UUID) -> WorkspaceRead | None:
        """Get a workspace by ID."""
        workspace = await self._repo.get_by_id(workspace_id)
        if workspace is None:
            return None
        return WorkspaceRead.model_validate(workspace)

    async def list_workspaces(
        self, limit: int = 50, offset: int = 0
    ) -> list[WorkspaceRead]:
        """List all workspaces."""
        workspaces = await self._repo.get_all(limit=limit, offset=offset)
        return [WorkspaceRead.model_validate(w) for w in workspaces]

    async def update_workspace(
        self, workspace_id: uuid.UUID, data: WorkspaceUpdate
    ) -> WorkspaceRead | None:
        """Update a workspace."""
        workspace = await self._repo.get_by_id(workspace_id)
        if workspace is None:
            return None
        updated = await self._repo.update(
            workspace,
            name=data.name,
            description=data.description,
            settings=data.settings,
        )
        logger.info("workspace_updated", workspace_id=str(workspace_id))
        return WorkspaceRead.model_validate(updated)

    async def delete_workspace(self, workspace_id: uuid.UUID) -> bool:
        """Delete a workspace."""
        workspace = await self._repo.get_by_id(workspace_id)
        if workspace is None:
            return False
        await self._repo.delete(workspace)
        logger.info("workspace_deleted", workspace_id=str(workspace_id))
        return True
