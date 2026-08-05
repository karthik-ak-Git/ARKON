"""Project API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.schemas.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/workspaces/{workspace_id}/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    workspace_id: uuid.UUID,
    data: ProjectCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRead:
    service = ProjectService(session)
    return await service.create_project(workspace_id, data)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    workspace_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> list[ProjectRead]:
    service = ProjectService(session)
    return await service.list_projects(workspace_id, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRead:
    service = ProjectService(session)
    project = await service.get_project(project_id)
    if project is None or project.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRead:
    service = ProjectService(session)
    project = await service.update_project(project_id, data)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = ProjectService(session)
    deleted = await service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
