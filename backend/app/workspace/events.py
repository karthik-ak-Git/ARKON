"""ARKON Workspace - Events.

Workspace event types for the Kernel event system.

Events:
- WorkspaceCreated
- WorkspaceOpened
- WorkspaceClosed
- WorkspaceSuspended
- WorkspaceResumed
- WorkspaceDeleted
- WorkspaceError
- WorkspaceSnapshotCreated
- WorkspaceSnapshotRestored
- SessionUpdated
- MemoryUpdated
- ConfigUpdated
- ProjectAdded
- ProjectRemoved
- DocumentAdded
- DocumentRemoved
- DocumentUpdated
- AgentAdded
- AgentRemoved
- CommandExecuted
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkspaceEvent:
    """Base workspace event."""

    workspace_id: str
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkspaceCreated(WorkspaceEvent):
    """Emitted when a workspace is created."""

    name: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceOpened(WorkspaceEvent):
    """Emitted when a workspace is opened."""

    pass


@dataclass(frozen=True, slots=True)
class WorkspaceClosed(WorkspaceEvent):
    """Emitted when a workspace is closed."""

    pass


@dataclass(frozen=True, slots=True)
class WorkspaceSuspended(WorkspaceEvent):
    """Emitted when a workspace is suspended."""

    reason: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceResumed(WorkspaceEvent):
    """Emitted when a workspace is resumed."""

    pass


@dataclass(frozen=True, slots=True)
class WorkspaceDeleted(WorkspaceEvent):
    """Emitted when a workspace is deleted."""

    pass


@dataclass(frozen=True, slots=True)
class WorkspaceError(WorkspaceEvent):
    """Emitted when a workspace error occurs."""

    error: str = ""
    error_type: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshotCreated(WorkspaceEvent):
    """Emitted when a snapshot is created."""

    snapshot_id: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshotRestored(WorkspaceEvent):
    """Emitted when a snapshot is restored."""

    snapshot_id: str = ""


@dataclass(frozen=True, slots=True)
class SessionUpdated(WorkspaceEvent):
    """Emitted when session state is updated."""

    field: str = ""


@dataclass(frozen=True, slots=True)
class MemoryUpdated(WorkspaceEvent):
    """Emitted when memory state is updated."""

    operation: str = ""  # add, update, delete, clear


@dataclass(frozen=True, slots=True)
class ConfigUpdated(WorkspaceEvent):
    """Emitted when workspace config is updated."""

    field: str = ""


@dataclass(frozen=True, slots=True)
class ProjectAdded(WorkspaceEvent):
    """Emitted when a project is added to the session."""

    project_name: str = ""


@dataclass(frozen=True, slots=True)
class ProjectRemoved(WorkspaceEvent):
    """Emitted when a project is removed from the session."""

    project_name: str = ""


@dataclass(frozen=True, slots=True)
class DocumentAdded(WorkspaceEvent):
    """Emitted when a document is added to the session."""

    document_name: str = ""


@dataclass(frozen=True, slots=True)
class DocumentRemoved(WorkspaceEvent):
    """Emitted when a document is removed from the session."""

    document_name: str = ""


@dataclass(frozen=True, slots=True)
class DocumentUpdated(WorkspaceEvent):
    """Emitted when a document is updated in the session."""

    document_name: str = ""


@dataclass(frozen=True, slots=True)
class AgentAdded(WorkspaceEvent):
    """Emitted when an agent is added to the session."""

    agent_id: str = ""


@dataclass(frozen=True, slots=True)
class AgentRemoved(WorkspaceEvent):
    """Emitted when an agent is removed from the session."""

    agent_id: str = ""


@dataclass(frozen=True, slots=True)
class CommandExecuted(WorkspaceEvent):
    """Emitted when a command is executed in the session."""

    command: str = ""
    result: str = ""


# Event type registry for serialization
EVENT_TYPES: dict[str, type[WorkspaceEvent]] = {
    "WorkspaceCreated": WorkspaceCreated,
    "WorkspaceOpened": WorkspaceOpened,
    "WorkspaceClosed": WorkspaceClosed,
    "WorkspaceSuspended": WorkspaceSuspended,
    "WorkspaceResumed": WorkspaceResumed,
    "WorkspaceDeleted": WorkspaceDeleted,
    "WorkspaceError": WorkspaceError,
    "WorkspaceSnapshotCreated": WorkspaceSnapshotCreated,
    "WorkspaceSnapshotRestored": WorkspaceSnapshotRestored,
    "SessionUpdated": SessionUpdated,
    "MemoryUpdated": MemoryUpdated,
    "ConfigUpdated": ConfigUpdated,
    "ProjectAdded": ProjectAdded,
    "ProjectRemoved": ProjectRemoved,
    "DocumentAdded": DocumentAdded,
    "DocumentRemoved": DocumentRemoved,
    "DocumentUpdated": DocumentUpdated,
    "AgentAdded": AgentAdded,
    "AgentRemoved": AgentRemoved,
    "CommandExecuted": CommandExecuted,
}
