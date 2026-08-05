"""ARKON Workspace - Storage.

Every workspace has an isolated filesystem.

Directory structure:
    workspace/
    ├── workspace.json     # Workspace metadata
    ├── config/            # Configuration files
    ├── memory/            # Memory persistence
    ├── projects/          # Project files
    ├── artifacts/         # Generated artifacts
    ├── assets/            # Static assets
    ├── plugins/           # Plugin state
    ├── jobs/              # Job data
    ├── logs/              # Workspace logs
    ├── cache/             # Temporary cache
    ├── exports/           # Exported files
    └── .snapshots/        # Snapshot data

Storage paths are configurable.
Never hardcode paths.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import structlog

from app.workspace.exceptions import (
    WorkspaceStorageError,
    WorkspaceStorageNotFoundError,
    WorkspaceStoragePermissionError,
)
from app.workspace.interfaces import IWorkspaceStorage

logger = structlog.get_logger(__name__)

# Default directory structure
DEFAULT_DIRECTORIES = [
    "config",
    "memory",
    "projects",
    "artifacts",
    "assets",
    "plugins",
    "jobs",
    "logs",
    "cache",
    "exports",
    ".snapshots",
]


class WorkspaceStorage(IWorkspaceStorage):
    """Manages the workspace filesystem.

    Provides isolated storage for each workspace.
    All paths are relative to the workspace root.
    """

    def __init__(
        self,
        workspace_id: str,
        base_path: str,
        directories: list[str] | None = None,
    ) -> None:
        """Initialize workspace storage.

        Args:
            workspace_id: The workspace ID.
            base_path: Base path where workspaces are stored.
            directories: Optional custom directory structure.
        """
        self._workspace_id = workspace_id
        self._base_path = Path(base_path) / "workspaces" / workspace_id
        self._directories = directories or DEFAULT_DIRECTORIES

    @property
    def root(self) -> Path:
        """Get the workspace root path."""
        return self._base_path

    def get_path(self, *parts: str) -> str:
        """Get an absolute path within the workspace.

        Args:
            *parts: Path components.

        Returns:
            Absolute path as string.
        """
        return str(self._base_path / Path(*parts))

    async def initialize(self) -> None:
        """Create the workspace directory structure.

        Creates all required directories if they don't exist.
        """
        try:
            # Create workspace root
            self._base_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            for dirname in self._directories:
                dirpath = self._base_path / dirname
                dirpath.mkdir(parents=True, exist_ok=True)

            # Create workspace.json if it doesn't exist
            ws_json = self._base_path / "workspace.json"
            if not ws_json.exists():
                import json
                data = {"id": self._workspace_id, "version": "1.0.0"}
                ws_json.write_text(json.dumps(data, indent=2))

            logger.info(
                "workspace_storage_initialized",
                workspace_id=self._workspace_id,
                root=str(self._base_path),
            )

        except PermissionError as e:
            raise WorkspaceStoragePermissionError(
                self._workspace_id, str(self._base_path)
            ) from e
        except Exception as e:
            raise WorkspaceStorageError(
                self._workspace_id, str(self._base_path), str(e)
            ) from e

    async def read(self, path: str) -> bytes:
        """Read a file from the workspace.

        Args:
            path: Relative path within workspace.

        Returns:
            File contents as bytes.

        Raises:
            WorkspaceStorageError: If read fails.
        """
        full_path = self._base_path / path
        try:
            return full_path.read_bytes()
        except FileNotFoundError as e:
            raise WorkspaceStorageError(
                self._workspace_id, path, "File not found"
            ) from e
        except Exception as e:
            raise WorkspaceStorageError(
                self._workspace_id, path, str(e)
            ) from e

    async def write(self, path: str, data: bytes) -> None:
        """Write a file to the workspace.

        Args:
            path: Relative path within workspace.
            data: File contents.

        Raises:
            WorkspaceStorageError: If write fails.
        """
        full_path = self._base_path / path
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(data)
        except Exception as e:
            raise WorkspaceStorageError(
                self._workspace_id, path, str(e)
            ) from e

    async def exists(self, path: str) -> bool:
        """Check if a path exists.

        Args:
            path: Relative path within workspace.

        Returns:
            True if path exists.
        """
        full_path = self._base_path / path
        return full_path.exists()

    async def delete(self, path: str) -> None:
        """Delete a file or directory.

        Args:
            path: Relative path within workspace.

        Raises:
            WorkspaceStorageError: If delete fails.
        """
        full_path = self._base_path / path
        try:
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(str(full_path))
        except Exception as e:
            raise WorkspaceStorageError(
                self._workspace_id, path, str(e)
            ) from e

    async def list(self, path: str = "") -> list[str]:
        """List files in a directory.

        Args:
            path: Relative path within workspace. Empty for root.

        Returns:
            List of file/directory names.
        """
        full_path = self._base_path / path
        try:
            if not full_path.exists():
                return []
            return [
                entry.name
                for entry in full_path.iterdir()
                if not entry.name.startswith(".")
            ]
        except Exception:
            return []

    async def copy(self, source: str, dest: str) -> None:
        """Copy a file or directory within the workspace.

        Args:
            source: Source relative path.
            dest: Destination relative path.
        """
        src_path = self._base_path / source
        dest_path = self._base_path / dest
        try:
            if src_path.is_file():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_path), str(dest_path))
            elif src_path.is_dir():
                shutil.copytree(str(src_path), str(dest_path))
        except Exception as e:
            raise WorkspaceStorageError(
                self._workspace_id, source, str(e)
            ) from e

    async def move(self, source: str, dest: str) -> None:
        """Move a file or directory within the workspace.

        Args:
            source: Source relative path.
            dest: Destination relative path.
        """
        src_path = self._base_path / source
        dest_path = self._base_path / dest
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dest_path))
        except Exception as e:
            raise WorkspaceStorageError(
                self._workspace_id, source, str(e)
            ) from e

    async def get_size(self) -> int:
        """Get total size of workspace in bytes.

        Returns:
            Total size in bytes.
        """
        total = 0
        for dirpath, dirnames, filenames in os.walk(str(self._base_path)):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total += os.path.getsize(filepath)
        return total

    def __repr__(self) -> str:
        return (
            f"WorkspaceStorage(workspace_id={self._workspace_id!r}, "
            f"root={str(self._base_path)!r})"
        )
