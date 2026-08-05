"""ARKON Workspace - Workspace Manager.

The WorkspaceManager is the ONLY component allowed to create or destroy workspaces.
It orchestrates all workspace lifecycle operations.

Lifecycle:
    create → open → [active] → close → [closed]
                          ↓
                    suspend → [suspended] → resume → [active]
                          ↓
                    snapshot → [snapshot_id]
                          ↓
                    restore → [active]

Responsibilities:
- Create new workspaces
- Open existing workspaces
- Close workspaces
- Suspend/Resume workspaces
- Delete workspaces
- Create/Restore snapshots
- Emit workspace events
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

import structlog

from app.workspace.events import (
    WorkspaceCreated,
    WorkspaceDeleted,
    WorkspaceError,
    WorkspaceEvent,
    WorkspaceOpened,
    WorkspaceSnapshotCreated,
    WorkspaceSnapshotRestored,
)
from app.workspace.exceptions import (
    WorkspaceAlreadyOpenError,
    WorkspaceCreateError,
    WorkspaceDeleteError,
    WorkspaceNotOpenError,
    WorkspaceOpenError,
)
from app.workspace.interfaces import IWorkspace
from app.workspace.loader import WorkspaceLoader
from app.workspace.serializer import WorkspaceSerializer
from app.workspace.session import SessionManager
from app.workspace.snapshot import SnapshotManager
from app.workspace.storage import WorkspaceStorage
from app.workspace.workspace import Workspace, WorkspaceConfig, WorkspaceMemory

logger = structlog.get_logger(__name__)


class WorkspaceManager:
    """The ONLY component allowed to create or destroy workspaces.

    This is the single entry point for all workspace lifecycle operations.
    No other component should create or destroy workspaces directly.
    """

    def __init__(
        self,
        base_path: str,
        event_handler: Callable[[WorkspaceEvent], Any] | None = None,
    ) -> None:
        """Initialize workspace manager.

        Args:
            base_path: Base path for workspace storage.
            event_handler: Optional callback for workspace events.
        """
        self._base_path = base_path
        self._event_handler = event_handler
        self._loader = WorkspaceLoader(base_path)
        self._serializer = WorkspaceSerializer()

        # Active workspaces: workspace_id → Workspace
        self._workspaces: dict[str, Workspace] = {}

    async def create(
        self,
        workspace_id: str,
        name: str,
        description: str = "",
        path: str | None = None,
        tags: list[str] | None = None,
    ) -> Workspace:
        """Create a new workspace.

        This is the ONLY way to create a workspace.

        Args:
            workspace_id: Unique workspace identifier.
            name: Human-readable workspace name.
            description: Optional description.
            path: Optional filesystem path for projects.
            tags: Optional tags.

        Returns:
            Created workspace instance.

        Raises:
            WorkspaceCreateError: If creation fails.
        """
        # Check if workspace already exists
        if workspace_id in self._workspaces:
            raise WorkspaceAlreadyOpenError(workspace_id)

        if await self._loader.exists(workspace_id):
            raise WorkspaceCreateError(
                workspace_id, "Workspace already exists on disk"
            )

        try:
            # Create workspace storage
            storage = WorkspaceStorage(workspace_id, self._base_path)
            await storage.initialize()

            # Create workspace config
            config = WorkspaceConfig(
                name=name,
                description=description,
                base_path=path or f"{self._base_path}/workspaces/{workspace_id}",
            )

            # Create workspace memory
            memory = WorkspaceMemory()

            # Create workspace
            workspace = Workspace(
                _id=workspace_id,
                _name=name,
                _config=config,
                _memory=memory,
            )

            # Save to disk
            await self._save_workspace(workspace, storage)

            # Track active workspace
            self._workspaces[workspace_id] = workspace

            # Emit event
            await self._emit(WorkspaceCreated(
                workspace_id=workspace_id,
                name=name,
            ))

            logger.info(
                "workspace_created",
                workspace_id=workspace_id,
                name=name,
            )

            return workspace

        except Exception as e:
            await self._emit(WorkspaceError(
                workspace_id=workspace_id,
                error=str(e),
                error_type="create",
            ))
            raise WorkspaceCreateError(workspace_id, str(e)) from e

    async def open(self, workspace_id: str) -> Workspace:
        """Open an existing workspace.

        Loads the workspace from disk into active memory.

        Args:
            workspace_id: The workspace to open.

        Returns:
            Opened workspace instance.

        Raises:
            WorkspaceOpenError: If open fails.
        """
        # Check if already open
        if workspace_id in self._workspaces:
            return self._workspaces[workspace_id]

        try:
            # Load from disk
            workspace = await self._loader.load_from_disk(workspace_id)

            # Validate
            issues = await self._loader.validate(workspace_id)
            if issues:
                logger.warning(
                    "workspace_validation_issues",
                    workspace_id=workspace_id,
                    issues=issues,
                )

            # Track active workspace
            self._workspaces[workspace_id] = workspace

            # Emit event
            await self._emit(WorkspaceOpened(
                workspace_id=workspace_id,
            ))

            logger.info(
                "workspace_opened",
                workspace_id=workspace_id,
            )

            return workspace

        except Exception as e:
            await self._emit(WorkspaceError(
                workspace_id=workspace_id,
                error=str(e),
                error_type="open",
            ))
            raise WorkspaceOpenError(workspace_id, str(e)) from e

    async def close(self, workspace_id: str) -> None:
        """Close an active workspace.

        Saves state to disk and removes from active tracking.

        Args:
            workspace_id: The workspace to close.

        Raises:
            WorkspaceNotOpenError: If workspace is not open.
        """
        if workspace_id not in self._workspaces:
            raise WorkspaceNotOpenError(workspace_id)

        try:
            workspace = self._workspaces[workspace_id]
            storage = WorkspaceStorage(workspace_id, self._base_path)

            # Save to disk
            await self._save_workspace(workspace, storage)

            # Remove from active tracking
            del self._workspaces[workspace_id]

            # Emit event
            from app.workspace.events import WorkspaceClosed
            await self._emit(WorkspaceClosed(
                workspace_id=workspace_id,
            ))

            logger.info(
                "workspace_closed",
                workspace_id=workspace_id,
            )

        except Exception as e:
            await self._emit(WorkspaceError(
                workspace_id=workspace_id,
                error=str(e),
                error_type="close",
            ))
            raise

    async def delete(self, workspace_id: str) -> None:
        """Delete a workspace.

        This is the ONLY way to delete a workspace.

        Args:
            workspace_id: The workspace to delete.

        Raises:
            WorkspaceDeleteError: If deletion fails.
        """
        # Close if open
        if workspace_id in self._workspaces:
            await self.close(workspace_id)

        try:
            # Delete from disk
            storage = WorkspaceStorage(workspace_id, self._base_path)
            await storage.delete(".")

            # Emit event
            await self._emit(WorkspaceDeleted(
                workspace_id=workspace_id,
            ))

            logger.info(
                "workspace_deleted",
                workspace_id=workspace_id,
            )

        except Exception as e:
            await self._emit(WorkspaceError(
                workspace_id=workspace_id,
                error=str(e),
                error_type="delete",
            ))
            raise WorkspaceDeleteError(workspace_id, str(e)) from e

    async def suspend(self, workspace_id: str, reason: str = "") -> None:
        """Suspend a workspace.

        Args:
            workspace_id: The workspace to suspend.
            reason: Optional reason for suspension.

        Raises:
            WorkspaceNotOpenError: If workspace is not open.
        """
        if workspace_id not in self._workspaces:
            raise WorkspaceNotOpenError(workspace_id)

        workspace = self._workspaces[workspace_id]
        workspace.set_runtime_state("state", "suspended")

        await self._emit(WorkspaceSuspended(
            workspace_id=workspace_id,
            reason=reason,
        ))

        logger.info(
            "workspace_suspended",
            workspace_id=workspace_id,
            reason=reason,
        )

    async def resume(self, workspace_id: str) -> None:
        """Resume a suspended workspace.

        Args:
            workspace_id: The workspace to resume.

        Raises:
            WorkspaceNotOpenError: If workspace is not open.
        """
        if workspace_id not in self._workspaces:
            raise WorkspaceNotOpenError(workspace_id)

        workspace = self._workspaces[workspace_id]
        workspace.set_runtime_state("state", "open")

        from app.workspace.events import WorkspaceResumed
        await self._emit(WorkspaceResumed(
            workspace_id=workspace_id,
        ))

        logger.info(
            "workspace_resumed",
            workspace_id=workspace_id,
        )

    async def snapshot(
        self, workspace_id: str, name: str | None = None
    ) -> str:
        """Create a snapshot of a workspace.

        Args:
            workspace_id: The workspace to snapshot.
            name: Optional snapshot name.

        Returns:
            Snapshot ID.

        Raises:
            WorkspaceNotOpenError: If workspace is not open.
        """
        if workspace_id not in self._workspaces:
            raise WorkspaceNotOpenError(workspace_id)

        workspace = self._workspaces[workspace_id]
        storage = WorkspaceStorage(workspace_id, self._base_path)
        snapshot_mgr = SnapshotManager(storage, workspace_id)

        snapshot_id = await snapshot_mgr.create(name)

        await self._emit(WorkspaceSnapshotCreated(
            workspace_id=workspace_id,
            snapshot_id=snapshot_id,
        ))

        return snapshot_id

    async def restore(
        self, workspace_id: str, snapshot_id: str
    ) -> None:
        """Restore a workspace from a snapshot.

        Args:
            workspace_id: The workspace to restore.
            snapshot_id: The snapshot to restore from.

        Raises:
            WorkspaceNotOpenError: If workspace is not open.
        """
        if workspace_id not in self._workspaces:
            raise WorkspaceNotOpenError(workspace_id)

        workspace = self._workspaces[workspace_id]
        storage = WorkspaceStorage(workspace_id, self._base_path)
        snapshot_mgr = SnapshotManager(storage, workspace_id)

        await snapshot_mgr.restore(snapshot_id)

        # Reload workspace from disk
        workspace = await self._loader.load_from_disk(workspace_id)
        self._workspaces[workspace_id] = workspace

        await self._emit(WorkspaceSnapshotRestored(
            workspace_id=workspace_id,
            snapshot_id=snapshot_id,
        ))

    def get(self, workspace_id: str) -> Workspace | None:
        """Get an active workspace.

        Args:
            workspace_id: The workspace ID.

        Returns:
            Workspace if open, None otherwise.
        """
        return self._workspaces.get(workspace_id)

    def list_active(self) -> list[str]:
        """List all active workspace IDs."""
        return list(self._workspaces.keys())

    async def list_available(self) -> list[dict[str, Any]]:
        """List all available workspaces on disk.

        Returns:
            List of workspace info dictionaries.
        """
        from pathlib import Path
        import json

        workspaces_path = Path(self._base_path) / "workspaces"
        if not workspaces_path.exists():
            return []

        result = []
        for entry in workspaces_path.iterdir():
            if entry.is_dir():
                ws_json = entry / "workspace.json"
                if ws_json.exists():
                    try:
                        data = json.loads(ws_json.read_text())
                        result.append({
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "description": data.get("description", ""),
                            "created_at": data.get("created_at"),
                            "state": data.get("state"),
                        })
                    except Exception:
                        pass

        return result

    async def _save_workspace(
        self, workspace: Workspace, storage: WorkspaceStorage
    ) -> None:
        """Save workspace to disk."""
        import json
        data = workspace.to_dict()
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        await storage.write("workspace.json", json_bytes)

    async def _emit(self, event: WorkspaceEvent) -> None:
        """Emit a workspace event."""
        if self._event_handler:
            try:
                result = self._event_handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(
                    "workspace_event_error",
                    error=str(e),
                    event_type=type(event).__name__,
                )


# Event types for convenience
from app.workspace.events import (  # noqa: E402, F401
    WorkspaceClosed,
    WorkspaceSuspended,
)
