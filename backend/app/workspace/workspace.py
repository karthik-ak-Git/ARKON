"""ARKON Workspace - Core model.

A Workspace is a LIVE execution environment.

Not a database record.
Not a CRUD entity.

A workspace is like:
- VS Code Workspace
- Docker Project
- JetBrains Workspace
- Unreal Project

It has:
- Isolated filesystem
- Configuration
- Session state
- Memory
- Plugin state
- Runtime state
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.workspace.exceptions import (
    WorkspaceNotOpenError,
    WorkspaceNotReadyError,
)
from app.workspace.interfaces import IWorkspace, WorkspaceState


@dataclass
class WorkspaceConfig:
    """Workspace configuration."""

    name: str = "default"
    description: str = ""
    base_path: str = ""
    tags: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    auto_save: bool = True
    auto_save_interval: int = 300  # seconds
    max_memory_mb: int = 1024
    max_agents: int = 10
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def path(self) -> str:
        """Alias for base_path (compatibility with API routes)."""
        return self.base_path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "base_path": self.base_path,
            "tags": self.tags,
            "plugins": self.plugins,
            "settings": self.settings,
            "auto_save": self.auto_save,
            "auto_save_interval": self.auto_save_interval,
            "max_memory_mb": self.max_memory_mb,
            "max_agents": self.max_agents,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkspaceConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", "default"),
            description=data.get("description", ""),
            base_path=data.get("base_path", ""),
            tags=data.get("tags", []),
            plugins=data.get("plugins", []),
            settings=data.get("settings", {}),
            auto_save=data.get("auto_save", True),
            auto_save_interval=data.get("auto_save_interval", 300),
            max_memory_mb=data.get("max_memory_mb", 1024),
            max_agents=data.get("max_agents", 10),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


@dataclass
class WorkspaceMemory:
    """Workspace memory - persistent knowledge across sessions."""

    _data: dict[str, Any] = field(default_factory=dict)
    _created_at: float = field(default_factory=time.time)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a memory entry."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a memory entry."""
        self._data[key] = value

    def delete(self, key: str) -> None:
        """Delete a memory entry."""
        self._data.pop(key, None)

    def clear(self) -> None:
        """Clear all memory."""
        self._data.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "data": self._data.copy(),
            "created_at": self._created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkspaceMemory:
        """Create from dictionary."""
        memory = cls()
        memory._data = data.get("data", {})
        memory._created_at = data.get("created_at", time.time())
        return memory


class _RuntimeStateProxy:
    """Lightweight proxy over the runtime_state dict, exposing .state."""

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def state(self) -> str:
        return self._data.get("state", "created")


@dataclass
class Workspace(IWorkspace):
    """A live workspace instance.

    This is NOT a database record.
    This is a live execution environment.
    """

    _id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _name: str = "default"
    _state: WorkspaceState = WorkspaceState.CREATED
    _config: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    _memory: WorkspaceMemory = field(default_factory=WorkspaceMemory)
    _session: dict[str, Any] = field(default_factory=dict)
    _runtime_state: dict[str, Any] = field(default_factory=dict)
    _created_at: float = field(default_factory=time.time)
    _opened_at: float | None = None
    _closed_at: float | None = None
    _last_activity: float = field(default_factory=time.time)

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> WorkspaceState:
        return self._state

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def opened_at(self) -> float | None:
        return self._opened_at

    @property
    def closed_at(self) -> float | None:
        return self._closed_at

    @property
    def last_activity(self) -> float:
        return self._last_activity

    @property
    def description(self) -> str:
        return self._config.description

    @property
    def path(self) -> str:
        return self._config.path

    @property
    def tags(self) -> list[str]:
        return self._config.tags

    @property
    def updated_at(self) -> float:
        return self._config.updated_at

    @property
    def runtime_state(self) -> _RuntimeStateProxy:
        return _RuntimeStateProxy(self._runtime_state)

    @property
    def is_open(self) -> bool:
        return self._state in (
            WorkspaceState.RUNNING,
            WorkspaceState.READY,
            WorkspaceState.SUSPENDED,
        )

    # =========================================================================
    # Configuration
    # =========================================================================

    def get_config(self) -> dict[str, Any]:
        """Return workspace configuration."""
        return self._config.to_dict()

    def set_config(self, config: dict[str, Any]) -> None:
        """Update workspace configuration."""
        for key, value in config.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self._config.updated_at = time.time()

    # =========================================================================
    # Session
    # =========================================================================

    def get_session(self) -> dict[str, Any]:
        """Return workspace session."""
        return self._session.copy()

    def set_session(self, key: str, value: Any) -> None:
        """Set a session value."""
        self._session[key] = value
        self._touch()

    def get_session_value(self, key: str, default: Any = None) -> Any:
        """Get a session value."""
        return self._session.get(key, default)

    # =========================================================================
    # Memory
    # =========================================================================

    def get_memory(self) -> dict[str, Any]:
        """Return workspace memory."""
        return self._memory.to_dict()

    def set_memory(self, key: str, value: Any) -> None:
        """Set a memory entry."""
        self._memory.set(key, value)
        self._touch()

    def get_memory_value(self, key: str, default: Any = None) -> Any:
        """Get a memory entry."""
        return self._memory.get(key, default)

    # =========================================================================
    # Runtime State
    # =========================================================================

    def get_runtime_state(self) -> dict[str, Any]:
        """Return runtime state."""
        return self._runtime_state.copy()

    def set_runtime_state(self, key: str, value: Any) -> None:
        """Set a runtime state entry."""
        self._runtime_state[key] = value
        self._touch()

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    def _set_state(self, state: WorkspaceState) -> None:
        """Set workspace state (internal)."""
        self._state = state
        self._touch()

    def _touch(self) -> None:
        """Update last activity timestamp."""
        self._last_activity = time.time()

    def _mark_opened(self) -> None:
        """Mark workspace as opened."""
        self._opened_at = time.time()
        self._touch()

    def _mark_closed(self) -> None:
        """Mark workspace as closed."""
        self._closed_at = time.time()
        self._touch()

    # =========================================================================
    # Lifecycle Hooks (called by WorkspaceManager)
    # =========================================================================

    async def initialize(self, context: Any = None) -> None:
        """Initialize the workspace."""
        self._set_state(WorkspaceState.INITIALIZING)
        # Initialize is handled by the manager
        self._set_state(WorkspaceState.CREATED)

    async def shutdown(self) -> None:
        """Shutdown the workspace."""
        if self.is_open:
            self._mark_closed()
            self._set_state(WorkspaceState.CLOSED)

    async def health_check(self) -> dict[str, Any]:
        """Return health status."""
        return {
            "id": self._id,
            "name": self._name,
            "state": self._state.value,
            "is_open": self.is_open,
            "last_activity": self._last_activity,
        }

    @property
    def is_healthy(self) -> bool:
        """Quick synchronous health check."""
        return self._state not in (
            WorkspaceState.FAILED,
            WorkspaceState.DELETED,
        )

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self._id,
            "name": self._name,
            "state": self._state.value,
            "config": self._config.to_dict(),
            "memory": self._memory.to_dict(),
            "session": self._session,
            "runtime_state": self._runtime_state,
            "created_at": self._created_at,
            "opened_at": self._opened_at,
            "closed_at": self._closed_at,
            "last_activity": self._last_activity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workspace:
        """Create from dictionary."""
        ws = cls()
        ws._id = data.get("id", ws._id)
        ws._name = data.get("name", ws._name)
        ws._state = WorkspaceState(data.get("state", "created"))
        ws._config = WorkspaceConfig.from_dict(data.get("config", {}))
        ws._memory = WorkspaceMemory.from_dict(data.get("memory", {}))
        ws._session = data.get("session", {})
        ws._runtime_state = data.get("runtime_state", {})
        ws._created_at = data.get("created_at", ws._created_at)
        ws._opened_at = data.get("opened_at")
        ws._closed_at = data.get("closed_at")
        ws._last_activity = data.get("last_activity", ws._last_activity)
        return ws
