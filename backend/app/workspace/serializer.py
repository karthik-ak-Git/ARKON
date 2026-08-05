"""ARKON Workspace - Serialization.

Handles workspace serialization and deserialization.

Supports:
- Serialize workspace to dictionary
- Deserialize dictionary to workspace data
- Export workspace to file
- Import workspace from file
- Schema versioning
- Forward compatibility
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import structlog

from app.workspace.exceptions import SchemaVersionError, SerializationError
from app.workspace.interfaces import IWorkspace, IWorkspaceSerializer

logger = structlog.get_logger(__name__)

# Current schema version
SCHEMA_VERSION = "1.0.0"


class WorkspaceSerializer(IWorkspaceSerializer):
    """Serializes and deserializes workspaces.

    Handles conversion between workspace objects and storable formats.
    Includes schema versioning for forward compatibility.
    """

    def serialize(self, workspace: IWorkspace) -> dict[str, Any]:
        """Serialize a workspace to a dictionary.

        Args:
            workspace: The workspace to serialize.

        Returns:
            Dictionary representation of the workspace.
        """
        try:
            return {
                "schema_version": SCHEMA_VERSION,
                "serialized_at": time.time(),
                "workspace": workspace.to_dict(),
            }
        except Exception as e:
            raise SerializationError(
                f"Failed to serialize workspace: {e}"
            ) from e

    def deserialize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deserialize a dictionary to workspace data.

        Args:
            data: Dictionary to deserialize.

        Returns:
            Workspace data dictionary.

        Raises:
            SchemaVersionError: If schema version is incompatible.
            SerializationError: If deserialization fails.
        """
        try:
            # Check schema version
            version = data.get("schema_version", "0.0.0")
            if not self._is_compatible(version):
                raise SchemaVersionError(SCHEMA_VERSION, version)

            return data.get("workspace", {})

        except SchemaVersionError:
            raise
        except Exception as e:
            raise SerializationError(
                f"Failed to deserialize workspace: {e}"
            ) from e

    def export(self, workspace: IWorkspace, path: str) -> None:
        """Export workspace to a file.

        Args:
            workspace: The workspace to export.
            path: File path to export to.

        Raises:
            SerializationError: If export fails.
        """
        try:
            data = self.serialize(workspace)
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, indent=2))

            logger.info(
                "workspace_exported",
                workspace_id=workspace.id,
                path=path,
            )

        except Exception as e:
            raise SerializationError(
                f"Failed to export workspace: {e}"
            ) from e

    def import_workspace(self, path: str) -> dict[str, Any]:
        """Import workspace from a file.

        Args:
            path: File path to import from.

        Returns:
            Workspace data dictionary.

        Raises:
            SerializationError: If import fails.
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                raise SerializationError(f"File not found: {path}")

            data = json.loads(file_path.read_text())
            return self.deserialize(data)

        except json.JSONDecodeError as e:
            raise SerializationError(
                f"Invalid JSON in file: {e}"
            ) from e
        except Exception as e:
            raise SerializationError(
                f"Failed to import workspace: {e}"
            ) from e

    def _is_compatible(self, version: str) -> bool:
        """Check if a schema version is compatible.

        Compatible means same major version.
        """
        try:
            current_parts = SCHEMA_VERSION.split(".")
            version_parts = version.split(".")

            # Major version must match
            return current_parts[0] == version_parts[0]
        except (IndexError, ValueError):
            return False

    def get_schema_version(self) -> str:
        """Get current schema version."""
        return SCHEMA_VERSION
