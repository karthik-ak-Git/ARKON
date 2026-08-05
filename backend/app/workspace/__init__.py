"""ARKON Workspace Runtime.

The Workspace Runtime provides live execution environments for agents.

Core Concepts:
    Workspace: A live execution environment with memory, session, config
    WorkspaceManager: The ONLY component that creates/destroys workspaces
    Session: The working context (projects, agents, documents, commands)
    Snapshot: Point-in-time capture of workspace state
    Storage: Isolated filesystem for each workspace

Quick Start:
    from app.workspace import WorkspaceManager

    # Create workspace manager
    manager = WorkspaceManager(base_path="./data")

    # Create a workspace
    workspace = await manager.create("my-workspace", "My Workspace")

    # Open a workspace
    workspace = await manager.open("my-workspace")

    # Close a workspace
    await manager.close("my-workspace")
"""

from app.workspace.events import (
    AgentAdded,
    AgentRemoved,
    CommandExecuted,
    ConfigUpdated,
    DocumentAdded,
    DocumentRemoved,
    DocumentUpdated,
    MemoryUpdated,
    ProjectAdded,
    ProjectRemoved,
    SessionUpdated,
    WorkspaceClosed,
    WorkspaceCreated,
    WorkspaceDeleted,
    WorkspaceError,
    WorkspaceEvent,
    WorkspaceOpened,
    WorkspaceResumed,
    WorkspaceSnapshotCreated,
    WorkspaceSnapshotRestored,
    WorkspaceSuspended,
)
from app.workspace.exceptions import (
    SnapshotCreateError,
    SnapshotNotFoundError,
    SnapshotRestoreError,
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptedError,
    WorkspaceCreateError,
    WorkspaceDeleteError,
    WorkspaceError as WorkspaceException,
    WorkspaceNotOpenError,
    WorkspaceNotFoundError,
    WorkspaceOpenError,
    WorkspaceStorageError,
    WorkspaceStorageNotFoundError,
    WorkspaceStoragePermissionError,
)
from app.workspace.interfaces import (
    IWorkspace,
    IWorkspaceManager,
    IWorkspaceSerializer,
    IWorkspaceStorage,
    ISessionManager,
    ISnapshotManager,
    WorkspaceState,
)
from app.workspace.loader import WorkspaceLoader
from app.workspace.manager import WorkspaceManager
from app.workspace.serializer import WorkspaceSerializer
from app.workspace.session import SessionManager, SessionData
from app.workspace.snapshot import SnapshotManager
from app.workspace.storage import WorkspaceStorage
from app.workspace.workspace import (
    Workspace,
    WorkspaceConfig,
    WorkspaceMemory,
)

__all__ = [
    # Manager
    "WorkspaceManager",

    # Models
    "Workspace",
    "WorkspaceConfig",
    "WorkspaceMemory",

    # Session
    "SessionManager",
    "SessionData",

    # Storage
    "WorkspaceStorage",

    # Snapshot
    "SnapshotManager",

    # Serializer
    "WorkspaceSerializer",

    # Loader
    "WorkspaceLoader",

    # Interfaces
    "IWorkspace",
    "IWorkspaceManager",
    "IWorkspaceStorage",
    "ISessionManager",
    "ISnapshotManager",
    "IWorkspaceSerializer",
    "WorkspaceState",

    # Events
    "WorkspaceEvent",
    "WorkspaceCreated",
    "WorkspaceOpened",
    "WorkspaceClosed",
    "WorkspaceSuspended",
    "WorkspaceResumed",
    "WorkspaceDeleted",
    "WorkspaceError",
    "WorkspaceSnapshotCreated",
    "WorkspaceSnapshotRestored",
    "SessionUpdated",
    "MemoryUpdated",
    "ConfigUpdated",
    "ProjectAdded",
    "ProjectRemoved",
    "DocumentAdded",
    "DocumentRemoved",
    "DocumentUpdated",
    "AgentAdded",
    "AgentRemoved",
    "CommandExecuted",

    # Exceptions
    "WorkspaceException",
    "WorkspaceCreateError",
    "WorkspaceOpenError",
    "WorkspaceDeleteError",
    "WorkspaceNotFoundError",
    "WorkspaceAlreadyOpenError",
    "WorkspaceNotOpenError",
    "WorkspaceCorruptedError",
    "WorkspaceStorageError",
    "WorkspaceStorageNotFoundError",
    "WorkspaceStoragePermissionError",
    "SnapshotCreateError",
    "SnapshotNotFoundError",
    "SnapshotRestoreError",
]
