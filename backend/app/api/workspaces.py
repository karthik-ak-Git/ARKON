"""Workspace API routes.

Thin controllers. Business logic lives in services.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.schemas.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("/", response_model=WorkspaceRead, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
    service = WorkspaceService(session)
    return await service.create_workspace(data)


@router.get("/", response_model=list[WorkspaceRead])
async def list_workspaces(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> list[WorkspaceRead]:
    service = WorkspaceService(session)
    return await service.list_workspaces(limit=limit, offset=offset)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
    service = WorkspaceService(session)
    workspace = await service.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
    service = WorkspaceService(session)
    workspace = await service.update_workspace(workspace_id, data)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = WorkspaceService(session)
    deleted = await service.delete_workspace(workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")
