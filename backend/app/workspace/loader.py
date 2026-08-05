"""ARKON Workspace - Loader.

Loads workspace from disk/database into live workspace object.

Handles:
- Load from filesystem (workspace.json)
- Load from serialized data
- Validate workspace integrity
- Initialize workspace components
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from app.workspace.exceptions import (
    WorkspaceCorruptedError,
    WorkspaceNotFoundError,
    WorkspaceStorageError,
)
from app.workspace.workspace import Workspace

logger = structlog.get_logger(__name__)


class WorkspaceLoader:
    """Loads workspaces from various sources.

    Responsible for reconstructing workspace objects from persisted state.
    """

    def __init__(self, base_path: str) -> None:
        """Initialize workspace loader.

        Args:
            base_path: Base path where workspaces are stored.
        """
        self._base_path = Path(base_path) / "workspaces"

    async def load_from_disk(self, workspace_id: str) -> Workspace:
        """Load a workspace from disk.

        Args:
            workspace_id: The workspace ID to load.

        Returns:
            Loaded Workspace object.

        Raises:
            WorkspaceNotFoundError: If workspace doesn't exist.
            WorkspaceCorruptedError: If workspace data is corrupted.
        """
        ws_path = self._base_path / workspace_id
        ws_json = ws_path / "workspace.json"

        # Check workspace exists
        if not ws_path.exists() or not ws_json.exists():
            raise WorkspaceNotFoundError(workspace_id)

        try:
            # Load workspace.json
            data = json.loads(ws_json.read_text())

            # Validate required fields
            if "id" not in data:
                raise WorkspaceCorruptedError(
                    workspace_id, "Missing 'id' field"
                )

            if data["id"] != workspace_id:
                raise WorkspaceCorruptedError(
                    workspace_id,
                    f"ID mismatch: expected {workspace_id}, got {data['id']}",
                )

            # Reconstruct workspace from data
            workspace = Workspace.from_dict(data)

            logger.info(
                "workspace_loaded_from_disk",
                workspace_id=workspace_id,
            )

            return workspace

        except json.JSONDecodeError as e:
            raise WorkspaceCorruptedError(
                workspace_id, f"Invalid JSON: {e}"
            ) from e
        except Exception as e:
            raise WorkspaceCorruptedError(
                workspace_id, str(e)
            ) from e

    async def load_from_dict(self, data: dict[str, Any]) -> Workspace:
        """Load a workspace from a dictionary.

        Args:
            data: Workspace data dictionary.

        Returns:
            Loaded Workspace object.

        Raises:
            WorkspaceCorruptedError: If data is invalid.
        """
        try:
            if "id" not in data:
                raise WorkspaceCorruptedError(
                    data.get("id", "unknown"),
                    "Missing 'id' field",
                )

            workspace = Workspace.from_dict(data)

            logger.info(
                "workspace_loaded_from_dict",
                workspace_id=workspace.id,
            )

            return workspace

        except Exception as e:
            raise WorkspaceCorruptedError(
                data.get("id", "unknown"), str(e)
            ) from e

    async def exists(self, workspace_id: str) -> bool:
        """Check if a workspace exists on disk.

        Args:
            workspace_id: The workspace ID.

        Returns:
            True if workspace exists.
        """
        ws_path = self._base_path / workspace_id
        ws_json = ws_path / "workspace.json"
        return ws_path.exists() and ws_json.exists()

    async def validate(self, workspace_id: str) -> list[str]:
        """Validate workspace integrity.

        Args:
            workspace_id: The workspace ID.

        Returns:
            List of issues found. Empty if valid.
        """
        issues = []
        ws_path = self._base_path / workspace_id

        if not ws_path.exists():
            return ["Workspace directory does not exist"]

        ws_json = ws_path / "workspace.json"
        if not ws_json.exists():
            issues.append("workspace.json does not exist")
            return issues

        try:
            data = json.loads(ws_json.read_text())

            # Check required fields
            required = ["id", "name", "created_at"]
            for field in required:
                if field not in data:
                    issues.append(f"Missing required field: {field}")

            # Validate ID matches
            if data.get("id") != workspace_id:
                issues.append(
                    f"ID mismatch: expected {workspace_id}, "
                    f"got {data.get('id')}"
                )

            # Validate state
            valid_states = [
                "created", "opening", "open", "closing",
                "closed", "suspending", "suspended",
                "resuming", "error", "corrupted",
                "archived", "migrating", "deleting", "deleted",
            ]
            if data.get("state") not in valid_states:
                issues.append(f"Invalid state: {data.get('state')}")

            # Check required directories
            required_dirs = ["config", "memory", "projects"]
            for dirname in required_dirs:
                dirpath = ws_path / dirname
                if not dirpath.exists():
                    issues.append(f"Missing directory: {dirname}")

        except json.JSONDecodeError:
            issues.append("workspace.json is invalid JSON")
        except Exception as e:
            issues.append(f"Validation error: {e}")

        return issues
