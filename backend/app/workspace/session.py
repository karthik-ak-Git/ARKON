"""ARKON Workspace - Session Management.

A Workspace owns a Session.
Session stores the state of a workspace across restarts.

Session data:
- Opened Projects
- Running Agents
- Open Documents
- Selected Workflow
- Command History
- Window Layout
- Active Plugins
- Current Branch
- Last Activity

Session can be restored after restart.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from app.workspace.interfaces import ISessionManager


@dataclass
class SessionData:
    """Session data container."""

    opened_projects: list[str] = field(default_factory=list)
    running_agents: list[str] = field(default_factory=list)
    open_documents: list[str] = field(default_factory=list)
    selected_workflow: str | None = None
    command_history: list[dict[str, Any]] = field(default_factory=list)
    window_layout: dict[str, Any] = field(default_factory=dict)
    active_plugins: list[str] = field(default_factory=list)
    current_branch: str = "main"
    last_activity: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "opened_projects": self.opened_projects.copy(),
            "running_agents": self.running_agents.copy(),
            "open_documents": self.open_documents.copy(),
            "selected_workflow": self.selected_workflow,
            "command_history": self.command_history.copy(),
            "window_layout": self.window_layout.copy(),
            "active_plugins": self.active_plugins.copy(),
            "current_branch": self.current_branch,
            "last_activity": self.last_activity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionData:
        """Create from dictionary."""
        return cls(
            opened_projects=data.get("opened_projects", []),
            running_agents=data.get("running_agents", []),
            open_documents=data.get("open_documents", []),
            selected_workflow=data.get("selected_workflow"),
            command_history=data.get("command_history", []),
            window_layout=data.get("window_layout", {}),
            active_plugins=data.get("active_plugins", []),
            current_branch=data.get("current_branch", "main"),
            last_activity=data.get("last_activity", time.time()),
        )


class SessionManager(ISessionManager):
    """Manages workspace session state.

    Session is persisted to disk and restored on workspace open.
    """

    def __init__(self, storage: Any, workspace_id: str) -> None:
        """Initialize session manager.

        Args:
            storage: IWorkspaceStorage instance for this workspace.
            workspace_id: The workspace ID.
        """
        self._storage = storage
        self._workspace_id = workspace_id
        self._data = SessionData()
        self._session_file = "session.json"

    async def load(self) -> dict[str, Any]:
        """Load session from storage.

        Returns:
            Session data as a dictionary.
        """
        try:
            if await self._storage.exists(self._session_file):
                raw = await self._storage.read(self._session_file)
                data = json.loads(raw.decode("utf-8"))
                self._data = SessionData.from_dict(data)
                return self._data.to_dict()
        except Exception:
            # Return empty session on load failure
            pass

        return self._data.to_dict()

    async def save(self) -> None:
        """Save session to storage."""
        self._data.last_activity = time.time()
        data = self._data.to_dict()
        raw = json.dumps(data, indent=2).encode("utf-8")
        await self._storage.write(self._session_file, raw)

    def get(self, key: str) -> Any:
        """Get a session value.

        Args:
            key: Session key.

        Returns:
            Session value, or None if not found.
        """
        return getattr(self._data, key, None)

    def set(self, key: str, value: Any) -> None:
        """Set a session value.

        Args:
            key: Session key.
            value: Session value.
        """
        if hasattr(self._data, key):
            setattr(self._data, key, value)
            self._data.last_activity = time.time()

    def get_dict(self) -> dict[str, Any]:
        """Get session data as dictionary."""
        return self._data.to_dict()

    def set_dict(self, data: dict[str, Any]) -> None:
        """Set session data from dictionary."""
        self._data = SessionData.from_dict(data)
        self._data.last_activity = time.time()

    def clear(self) -> None:
        """Clear session data."""
        self._data = SessionData()

    # =========================================================================
    # Project Management
    # =========================================================================

    def add_project(self, project_id: str) -> None:
        """Add a project to opened projects."""
        if project_id not in self._data.opened_projects:
            self._data.opened_projects.append(project_id)
            self._data.last_activity = time.time()

    def remove_project(self, project_id: str) -> None:
        """Remove a project from opened projects."""
        self._data.opened_projects = [
            p for p in self._data.opened_projects if p != project_id
        ]

    def get_projects(self) -> list[str]:
        """Get list of opened projects."""
        return self._data.opened_projects.copy()

    # =========================================================================
    # Agent Management
    # =========================================================================

    def add_agent(self, agent_id: str) -> None:
        """Add a running agent."""
        if agent_id not in self._data.running_agents:
            self._data.running_agents.append(agent_id)
            self._data.last_activity = time.time()

    def remove_agent(self, agent_id: str) -> None:
        """Remove a running agent."""
        self._data.running_agents = [
            a for a in self._data.running_agents if a != agent_id
        ]

    def get_agents(self) -> list[str]:
        """Get list of running agents."""
        return self._data.running_agents.copy()

    # =========================================================================
    # Document Management
    # =========================================================================

    def add_document(self, doc_path: str) -> None:
        """Add an open document."""
        if doc_path not in self._data.open_documents:
            self._data.open_documents.append(doc_path)
            self._data.last_activity = time.time()

    def remove_document(self, doc_path: str) -> None:
        """Remove an open document."""
        self._data.open_documents = [
            d for d in self._data.open_documents if d != doc_path
        ]

    def get_documents(self) -> list[str]:
        """Get list of open documents."""
        return self._data.open_documents.copy()

    # =========================================================================
    # Command History
    # =========================================================================

    def add_command(self, command: str, args: dict[str, Any] | None = None) -> None:
        """Add a command to history."""
        self._data.command_history.append({
            "command": command,
            "args": args or {},
            "timestamp": time.time(),
        })
        # Keep only last 100 commands
        if len(self._data.command_history) > 100:
            self._data.command_history = self._data.command_history[-100:]
        self._data.last_activity = time.time()

    def get_commands(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent commands."""
        return self._data.command_history[-limit:]

    # =========================================================================
    # Branch
    # =========================================================================

    def set_branch(self, branch: str) -> None:
        """Set current branch."""
        self._data.current_branch = branch
        self._data.last_activity = time.time()

    def get_branch(self) -> str:
        """Get current branch."""
        return self._data.current_branch

    # =========================================================================
    # Plugin Management
    # =========================================================================

    def add_plugin(self, plugin_name: str) -> None:
        """Add an active plugin."""
        if plugin_name not in self._data.active_plugins:
            self._data.active_plugins.append(plugin_name)
            self._data.last_activity = time.time()

    def remove_plugin(self, plugin_name: str) -> None:
        """Remove an active plugin."""
        self._data.active_plugins = [
            p for p in self._data.active_plugins if p != plugin_name
        ]

    def get_plugins(self) -> list[str]:
        """Get list of active plugins."""
        return self._data.active_plugins.copy()
