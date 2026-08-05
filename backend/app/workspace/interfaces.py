"""ARKON Workspace - Interface contracts.

Defines the contracts for workspace components.
No business logic — only structural agreements.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import Any

from app.kernel.interfaces import IInitializable, IHealthCheckable


# =============================================================================
# Workspace States
# =============================================================================

class WorkspaceState(enum.Enum):
    """Possible states for a workspace."""

    CREATED = "created"
    INITIALIZING = "initializing"
    MOUNTING = "mounting"
    LOADING = "loading"
    RESTORING = "restoring"
    READY = "ready"
    RUNNING = "running"
    SNAPSHOTTING = "snapshotting"
    SUSPENDING = "suspending"
    SUSPENDED = "suspended"
    RESUMING = "resuming"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"
    DELETED = "deleted"


# =============================================================================
# Core Interfaces
# =============================================================================

class IWorkspace(IInitializable, IHealthCheckable):
    """Interface for a live workspace instance."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique workspace identifier."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable workspace name."""
        ...

    @property
    @abstractmethod
    def state(self) -> WorkspaceState:
        """Current lifecycle state."""
        ...

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Return workspace configuration."""
        ...

    @abstractmethod
    def set_config(self, config: dict[str, Any]) -> None:
        """Update workspace configuration."""
        ...

    @abstractmethod
    def get_session(self) -> Any:
        """Return workspace session."""
        ...

    @abstractmethod
    def get_memory(self) -> dict[str, Any]:
        """Return workspace memory."""
        ...

    @abstractmethod
    def set_memory(self, key: str, value: Any) -> None:
        """Set a memory entry."""
        ...


class IWorkspaceManager(ABC):
    """Interface for the workspace manager.

    The ONLY component allowed to create or destroy workspaces.
    """

    @abstractmethod
    async def create(
        self,
        name: str,
        config: dict[str, Any] | None = None,
        path: str | None = None,
    ) -> IWorkspace:
        """Create a new workspace."""
        ...

    @abstractmethod
    async def open(self, workspace_id: str) -> IWorkspace:
        """Open an existing workspace."""
        ...

    @abstractmethod
    async def close(self, workspace_id: str) -> None:
        """Close a workspace."""
        ...

    @abstractmethod
    async def delete(self, workspace_id: str) -> None:
        """Delete a workspace permanently."""
        ...

    @abstractmethod
    async def suspend(self, workspace_id: str) -> None:
        """Suspend a workspace."""
        ...

    @abstractmethod
    async def resume(self, workspace_id: str) -> None:
        """Resume a suspended workspace."""
        ...

    @abstractmethod
    async def snapshot(self, workspace_id: str, name: str | None = None) -> str:
        """Create a snapshot. Returns snapshot ID."""
        ...

    @abstractmethod
    async def restore(self, workspace_id: str, snapshot_id: str) -> None:
        """Restore a workspace from snapshot."""
        ...

    @abstractmethod
    def get(self, workspace_id: str) -> IWorkspace | None:
        """Get an active workspace by ID."""
        ...

    @abstractmethod
    def list_active(self) -> list[IWorkspace]:
        """List all active (open) workspaces."""
        ...


class IWorkspaceStorage(ABC):
    """Interface for workspace filesystem operations."""

    @abstractmethod
    def get_path(self, *parts: str) -> str:
        """Get an absolute path within the workspace."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Create the workspace directory structure."""
        ...

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """Read a file from the workspace."""
        ...

    @abstractmethod
    async def write(self, path: str, data: bytes) -> None:
        """Write a file to the workspace."""
        ...

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if a path exists."""
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete a file or directory."""
        ...

    @abstractmethod
    async def list(self, path: str = "") -> list[str]:
        """List files in a directory."""
        ...


class ISessionManager(ABC):
    """Interface for workspace session management."""

    @abstractmethod
    async def load(self) -> dict[str, Any]:
        """Load session from storage."""
        ...

    @abstractmethod
    async def save(self) -> None:
        """Save session to storage."""
        ...

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get a session value."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a session value."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear session data."""
        ...


class ISnapshotManager(ABC):
    """Interface for workspace snapshots."""

    @abstractmethod
    async def create(self, name: str | None = None) -> str:
        """Create a snapshot. Returns snapshot ID."""
        ...

    @abstractmethod
    async def restore(self, snapshot_id: str) -> None:
        """Restore from a snapshot."""
        ...

    @abstractmethod
    async def list(self) -> list[dict[str, Any]]:
        """List all snapshots."""
        ...

    @abstractmethod
    async def delete(self, snapshot_id: str) -> None:
        """Delete a snapshot."""
        ...

    @abstractmethod
    async def get(self, snapshot_id: str) -> dict[str, Any] | None:
        """Get snapshot metadata."""
        ...


class IWorkspaceSerializer(ABC):
    """Interface for workspace serialization."""

    @abstractmethod
    def serialize(self, workspace: IWorkspace) -> dict[str, Any]:
        """Serialize a workspace to a dictionary."""
        ...

    @abstractmethod
    def deserialize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deserialize a dictionary to workspace data."""
        ...

    @abstractmethod
    def export(self, workspace: IWorkspace, path: str) -> None:
        """Export workspace to a file."""
        ...

    @abstractmethod
    def import_workspace(self, path: str) -> dict[str, Any]:
        """Import workspace from a file."""
        ...
