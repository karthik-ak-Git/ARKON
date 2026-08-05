"""Workspace API routes.

The Workspace Manager is the ONLY component that creates/destroys workspaces.
All routes go through the WorkspaceManager.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.schemas.schemas import (
    WorkspaceCreate,
    WorkspaceList,
    WorkspaceOpen,
    WorkspaceRead,
    WorkspaceSnapshotCreate,
    WorkspaceSnapshotRead,
    WorkspaceUpdate,
)
from app.workspace import WorkspaceManager
from app.workspace.exceptions import (
    WorkspaceAlreadyOpenError,
    WorkspaceCreateError,
    WorkspaceDeleteError,
    WorkspaceNotOpenError,
    WorkspaceNotFoundError,
    WorkspaceOpenError,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

# Workspace manager instance (initialized in main.py)
_manager: WorkspaceManager | None = None


def get_manager() -> WorkspaceManager:
    """Get the workspace manager instance."""
    global _manager
    if _manager is None:
        from app.core.config import get_settings

        settings = get_settings()
        _manager = WorkspaceManager(base_path=settings.DATA_DIR)
    return _manager


def set_manager(manager: WorkspaceManager) -> None:
    """Set the workspace manager instance."""
    global _manager
    _manager = manager


# =============================================================================
# Lifecycle Operations
# =============================================================================


@router.post("/", response_model=WorkspaceRead, status_code=201)
async def create_workspace(data: WorkspaceCreate) -> WorkspaceRead:
    """Create a new workspace.

    This is the ONLY way to create a workspace.
    """
    manager = get_manager()
    try:
        workspace = await manager.create(
            workspace_id=data.id,
            name=data.name,
            description=data.description or "",
            path=data.path,
            tags=data.tags,
        )
        return WorkspaceRead(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            state=workspace.runtime_state.state,
            path=workspace.config.path,
            tags=workspace.config.tags,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
    except WorkspaceCreateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WorkspaceAlreadyOpenError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{workspace_id}/open", response_model=WorkspaceRead)
async def open_workspace(workspace_id: str) -> WorkspaceRead:
    """Open an existing workspace."""
    manager = get_manager()
    try:
        workspace = await manager.open(workspace_id)
        return WorkspaceRead(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            state=workspace.runtime_state.state,
            path=workspace.config.path,
            tags=workspace.config.tags,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
    except WorkspaceOpenError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WorkspaceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workspace_id}/close")
async def close_workspace(workspace_id: str) -> dict:
    """Close an active workspace."""
    manager = get_manager()
    try:
        await manager.close(workspace_id)
        return {"status": "closed", "workspace_id": workspace_id}
    except WorkspaceNotOpenError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: str) -> dict:
    """Delete a workspace.

    This is the ONLY way to delete a workspace.
    """
    manager = get_manager()
    try:
        await manager.delete(workspace_id)
        return {"status": "deleted", "workspace_id": workspace_id}
    except WorkspaceDeleteError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# State Operations
# =============================================================================


@router.post("/{workspace_id}/suspend")
async def suspend_workspace(
    workspace_id: str,
    reason: str = Query(default="", description="Reason for suspension"),
) -> dict:
    """Suspend a workspace."""
    manager = get_manager()
    try:
        await manager.suspend(workspace_id, reason)
        return {"status": "suspended", "workspace_id": workspace_id}
    except WorkspaceNotOpenError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workspace_id}/resume")
async def resume_workspace(workspace_id: str) -> dict:
    """Resume a suspended workspace."""
    manager = get_manager()
    try:
        await manager.resume(workspace_id)
        return {"status": "resumed", "workspace_id": workspace_id}
    except WorkspaceNotOpenError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Snapshot Operations
# =============================================================================


@router.post("/{workspace_id}/snapshots", response_model=WorkspaceSnapshotRead)
async def create_snapshot(
    workspace_id: str,
    data: WorkspaceSnapshotCreate | None = None,
) -> WorkspaceSnapshotRead:
    """Create a snapshot of a workspace."""
    manager = get_manager()
    try:
        name = data.name if data else None
        snapshot_id = await manager.snapshot(workspace_id, name)
        return WorkspaceSnapshotRead(
            id=snapshot_id,
            name=name or f"snapshot-{snapshot_id}",
            workspace_id=workspace_id,
            created_at=__import__("time").time(),
            status="created",
        )
    except WorkspaceNotOpenError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workspace_id}/snapshots/{snapshot_id}/restore")
async def restore_snapshot(
    workspace_id: str, snapshot_id: str
) -> dict:
    """Restore from a snapshot."""
    manager = get_manager()
    try:
        await manager.restore(workspace_id, snapshot_id)
        return {
            "status": "restored",
            "workspace_id": workspace_id,
            "snapshot_id": snapshot_id,
        }
    except WorkspaceNotOpenError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Query Operations
# =============================================================================


@router.get("/", response_model=WorkspaceList)
async def list_workspaces() -> WorkspaceList:
    """List all workspaces (active and available)."""
    manager = get_manager()

    # Get active workspaces
    active_ids = manager.list_active()
    active = []
    for ws_id in active_ids:
        ws = manager.get(ws_id)
        if ws:
            active.append(WorkspaceRead(
                id=ws.id,
                name=ws.name,
                description=ws.description,
                state=ws.runtime_state.state,
                path=ws.config.path,
                tags=ws.config.tags,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
            ))

    # Get available workspaces
    available_data = await manager.list_available()
    available = []
    for data in available_data:
        available.append(WorkspaceRead(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            state=data.get("state", "unknown"),
            path=None,
            tags=None,
            created_at=data.get("created_at", 0),
            updated_at=data.get("created_at", 0),
        ))

    return WorkspaceList(active=active, available=available)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(workspace_id: str) -> WorkspaceRead:
    """Get a workspace by ID."""
    manager = get_manager()
    workspace = manager.get(workspace_id)
    if workspace is None:
        # Try to load from disk
        try:
            workspace = await manager.open(workspace_id)
            await manager.close(workspace_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Workspace not found")

    return WorkspaceRead(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        state=workspace.runtime_state.state,
        path=workspace.config.path,
        tags=workspace.config.tags,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )
