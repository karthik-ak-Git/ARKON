"""ARKON Workspace - Exceptions.

Domain-specific exceptions for workspace operations.
All workspace errors derive from WorkspaceError.
"""

from __future__ import annotations

from app.kernel.exceptions import KernelError


class WorkspaceError(KernelError):
    """Base exception for all workspace errors."""
    pass


# =============================================================================
# Creation Errors
# =============================================================================

class WorkspaceCreateError(WorkspaceError):
    """Raised when workspace creation fails."""

    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        super().__init__(f"Failed to create workspace '{name}': {reason}")


class WorkspaceAlreadyExistsError(WorkspaceError):
    """Raised when trying to create a workspace that already exists."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Workspace '{name}' already exists")


# =============================================================================
# Lifecycle Errors
# =============================================================================

class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace is not found."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Workspace not found: {workspace_id}")


class WorkspaceNotOpenError(WorkspaceError):
    """Raised when trying to operate on a closed workspace."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Workspace not open: {workspace_id}")


class WorkspaceNotReadyError(WorkspaceError):
    """Raised when workspace is not in ready state."""

    def __init__(self, workspace_id: str, current_state: str) -> None:
        self.workspace_id = workspace_id
        self.current_state = current_state
        super().__init__(
            f"Workspace '{workspace_id}' not ready. Current state: {current_state}"
        )


class WorkspaceAlreadyOpenError(WorkspaceError):
    """Raised when trying to open an already open workspace."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Workspace already open: {workspace_id}")


class WorkspaceAlreadySuspendedError(WorkspaceError):
    """Raised when trying to suspend an already suspended workspace."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Workspace already suspended: {workspace_id}")


# =============================================================================
# Storage Errors
# =============================================================================

class WorkspaceStorageError(WorkspaceError):
    """Raised when workspace storage operations fail."""

    def __init__(self, workspace_id: str, path: str, reason: str) -> None:
        self.workspace_id = workspace_id
        self.path = path
        super().__init__(
            f"Storage error for workspace '{workspace_id}' at '{path}': {reason}"
        )


class WorkspaceStorageNotFoundError(WorkspaceStorageError):
    """Raised when workspace storage directory doesn't exist."""

    def __init__(self, workspace_id: str, path: str) -> None:
        super().__init__(workspace_id, path, "Storage directory not found")


class WorkspaceStoragePermissionError(WorkspaceStorageError):
    """Raised when workspace storage permissions are insufficient."""

    def __init__(self, workspace_id: str, path: str) -> None:
        super().__init__(workspace_id, path, "Permission denied")


# =============================================================================
# Snapshot Errors
# =============================================================================

class SnapshotError(WorkspaceError):
    """Raised when snapshot operations fail."""
    pass


class SnapshotNotFoundError(WorkspaceError):
    """Raised when a snapshot is not found."""

    def __init__(self, snapshot_id: str) -> None:
        self.snapshot_id = snapshot_id
        super().__init__(f"Snapshot not found: {snapshot_id}")


class SnapshotCreateError(WorkspaceError):
    """Raised when snapshot creation fails."""

    def __init__(self, workspace_id: str, reason: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Failed to create snapshot for '{workspace_id}': {reason}")


class SnapshotRestoreError(WorkspaceError):
    """Raised when snapshot restore fails."""

    def __init__(self, workspace_id: str, snapshot_id: str, reason: str) -> None:
        self.workspace_id = workspace_id
        self.snapshot_id = snapshot_id
        super().__init__(
            f"Failed to restore snapshot '{snapshot_id}' for workspace '{workspace_id}': {reason}"
        )


# =============================================================================
# Serialization Errors
# =============================================================================

class SerializationError(WorkspaceError):
    """Raised when serialization/deserialization fails."""
    pass


class SchemaVersionError(WorkspaceError):
    """Raised when schema version is incompatible."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Schema version mismatch: expected {expected}, got {actual}"
        )


# =============================================================================
# Session Errors
# =============================================================================

class SessionError(WorkspaceError):
    """Raised when session operations fail."""
    pass


class SessionNotFoundError(WorkspaceError):
    """Raised when a session is not found."""
    pass


# =============================================================================
# Corrupted/Error State Errors
# =============================================================================


class WorkspaceCorruptedError(WorkspaceError):
    """Raised when workspace data is corrupted."""

    def __init__(self, workspace_id: str, reason: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Workspace '{workspace_id}' is corrupted: {reason}")


class WorkspaceOpenError(WorkspaceError):
    """Raised when workspace opening fails."""

    def __init__(self, workspace_id: str, reason: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Failed to open workspace '{workspace_id}': {reason}")


class WorkspaceDeleteError(WorkspaceError):
    """Raised when workspace deletion fails."""

    def __init__(self, workspace_id: str, reason: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Failed to delete workspace '{workspace_id}': {reason}")
