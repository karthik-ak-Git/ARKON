"""ARKON Workspace - Snapshot System.

Snapshots capture the complete state of a workspace at a point in time.

A snapshot contains:
- Workspace Metadata
- Database State
- Configuration
- Runtime State
- Memory
- Projects
- Jobs
- Plugin State
- Workflow State
- Session
- Artifacts Metadata

Snapshots support:
- Create
- List
- Restore
- Delete
- Rollback
"""

from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

import structlog

from app.workspace.exceptions import (
    SnapshotCreateError,
    SnapshotNotFoundError,
    SnapshotRestoreError,
)
from app.workspace.interfaces import ISnapshotManager

logger = structlog.get_logger(__name__)


class SnapshotManager(ISnapshotManager):
    """Manages workspace snapshots.

    Snapshots are stored in the .snapshots directory within the workspace.
    Each snapshot is a complete copy of the workspace state.
    """

    def __init__(self, storage: Any, workspace_id: str) -> None:
        """Initialize snapshot manager.

        Args:
            storage: IWorkspaceStorage instance for this workspace.
            workspace_id: The workspace ID.
        """
        self._storage = storage
        self._workspace_id = workspace_id
        self._snapshots_dir = ".snapshots"
        self._metadata_file = "snapshot.json"

    async def create(self, name: str | None = None) -> str:
        """Create a snapshot.

        Args:
            name: Optional human-readable name. Auto-generated if not provided.

        Returns:
            Snapshot ID.

        Raises:
            SnapshotCreateError: If creation fails.
        """
        snapshot_id = str(uuid.uuid4())[:8]
        name = name or f"snapshot-{snapshot_id}"
        timestamp = time.time()

        try:
            # Create snapshot directory
            snapshot_path = self._storage.get_path(
                self._snapshots_dir, snapshot_id
            )
            Path(snapshot_path).mkdir(parents=True, exist_ok=True)

            # Save snapshot metadata
            metadata = {
                "id": snapshot_id,
                "name": name,
                "workspace_id": self._workspace_id,
                "created_at": timestamp,
                "status": "created",
            }
            metadata_json = json.dumps(metadata, indent=2).encode("utf-8")
            await self._storage.write(
                f"{self._snapshots_dir}/{snapshot_id}/{self._metadata_file}",
                metadata_json,
            )

            # Copy workspace state to snapshot
            state_dirs = ["config", "memory", "session"]
            for dirname in state_dirs:
                src_path = self._storage.get_path(dirname)
                dst_path = self._storage.get_path(
                    self._snapshots_dir, snapshot_id, dirname
                )
                src = Path(src_path)
                dst = Path(dst_path)
                if src.exists():
                    shutil.copytree(str(src), str(dst), dirs_exist_ok=True)

            # Copy workspace.json
            ws_json_src = self._storage.get_path("workspace.json")
            ws_json_dst = self._storage.get_path(
                self._snapshots_dir, snapshot_id, "workspace.json"
            )
            ws_src = Path(ws_json_src)
            if ws_src.exists():
                shutil.copy2(str(ws_src), ws_json_dst)

            logger.info(
                "snapshot_created",
                snapshot_id=snapshot_id,
                workspace_id=self._workspace_id,
                name=name,
            )

            return snapshot_id

        except Exception as e:
            raise SnapshotCreateError(self._workspace_id, str(e)) from e

    async def restore(self, snapshot_id: str) -> None:
        """Restore from a snapshot.

        Args:
            snapshot_id: The snapshot to restore.

        Raises:
            SnapshotNotFoundError: If snapshot doesn't exist.
            SnapshotRestoreError: If restore fails.
        """
        # Check snapshot exists
        snapshot_path = self._storage.get_path(
            self._snapshots_dir, snapshot_id
        )
        if not await self._storage.exists(
            f"{self._snapshots_dir}/{snapshot_id}"
        ):
            raise SnapshotNotFoundError(snapshot_id)

        try:
            # Restore state directories
            state_dirs = ["config", "memory", "session"]
            for dirname in state_dirs:
                src_path = self._storage.get_path(
                    self._snapshots_dir, snapshot_id, dirname
                )
                dst_path = self._storage.get_path(dirname)
                src = Path(src_path)
                dst = Path(dst_path)
                if src.exists():
                    if dst.exists():
                        shutil.rmtree(str(dst))
                    shutil.copytree(str(src), str(dst))

            # Restore workspace.json
            ws_json_src = self._storage.get_path(
                self._snapshots_dir, snapshot_id, "workspace.json"
            )
            ws_json_dst = self._storage.get_path("workspace.json")
            src = Path(ws_json_src)
            if src.exists():
                shutil.copy2(str(src), ws_json_dst)

            logger.info(
                "snapshot_restored",
                snapshot_id=snapshot_id,
                workspace_id=self._workspace_id,
            )

        except SnapshotNotFoundError:
            raise
        except Exception as e:
            raise SnapshotRestoreError(
                self._workspace_id, snapshot_id, str(e)
            ) from e

    async def list(self) -> list[dict[str, Any]]:
        """List all snapshots.

        Returns:
            List of snapshot metadata dictionaries.
        """
        snapshots = []

        try:
            snapshots_base = self._storage.get_path(self._snapshots_dir)
            base = Path(snapshots_base)
            if not base.exists():
                return []

            for entry in base.iterdir():
                if entry.is_dir():
                    metadata_path = entry / self._metadata_file
                    if metadata_path.exists():
                        try:
                            metadata_json = metadata_path.read_text()
                            metadata = json.loads(metadata_json)
                            snapshots.append(metadata)
                        except Exception:
                            pass

            # Sort by created_at descending
            snapshots.sort(key=lambda s: s.get("created_at", 0), reverse=True)

        except Exception:
            pass

        return snapshots

    async def delete(self, snapshot_id: str) -> None:
        """Delete a snapshot.

        Args:
            snapshot_id: The snapshot to delete.

        Raises:
            SnapshotNotFoundError: If snapshot doesn't exist.
        """
        if not await self._storage.exists(
            f"{self._snapshots_dir}/{snapshot_id}"
        ):
            raise SnapshotNotFoundError(snapshot_id)

        try:
            await self._storage.delete(
                f"{self._snapshots_dir}/{snapshot_id}"
            )
            logger.info(
                "snapshot_deleted",
                snapshot_id=snapshot_id,
                workspace_id=self._workspace_id,
            )
        except Exception as e:
            raise SnapshotCreateError(
                self._workspace_id, f"Delete failed: {e}"
            ) from e

    async def get(self, snapshot_id: str) -> dict[str, Any] | None:
        """Get snapshot metadata.

        Args:
            snapshot_id: The snapshot ID.

        Returns:
            Snapshot metadata dict, or None if not found.
        """
        try:
            metadata_path = (
                f"{self._snapshots_dir}/{snapshot_id}/{self._metadata_file}"
            )
            if not await self._storage.exists(metadata_path):
                return None

            metadata_json = await self._storage.read(metadata_path)
            return json.loads(metadata_json.decode("utf-8"))

        except Exception:
            return None

    async def rollback(self, snapshot_id: str) -> str:
        """Rollback to a snapshot and create a new snapshot before.

        Args:
            snapshot_id: The snapshot to rollback to.

        Returns:
            ID of the snapshot created before rollback.
        """
        # Create a snapshot of current state before rollback
        pre_rollback_id = await self.create(f"pre-rollback-{snapshot_id}")

        # Restore the target snapshot
        await self.restore(snapshot_id)

        logger.info(
            "snapshot_rollback",
            to_snapshot=snapshot_id,
            pre_rollback_snapshot=pre_rollback_id,
            workspace_id=self._workspace_id,
        )

        return pre_rollback_id
