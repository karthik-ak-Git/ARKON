"""ARKON Runtime - Agent Model.

Core agent data structures.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.runtime.interfaces import AgentState


@dataclass
class AgentConfig:
    """Agent configuration."""
    max_retries: int = 3
    timeout: float = 300.0
    heartbeat_interval: float = 30.0
    auto_restart: bool = False
    priority: int = 0
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "heartbeat_interval": self.heartbeat_interval,
            "auto_restart": self.auto_restart,
            "priority": self.priority,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentConfig:
        return cls(
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 300.0),
            heartbeat_interval=data.get("heartbeat_interval", 30.0),
            auto_restart=data.get("auto_restart", False),
            priority=data.get("priority", 0),
            settings=data.get("settings", {}),
        )


@dataclass
class AgentMetadata:
    """Agent metadata for registry."""
    agent_type: str = ""
    name: str = ""
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    required_resources: dict[str, Any] = field(default_factory=dict)
    supported_models: list[str] = field(default_factory=list)
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "capabilities": self.capabilities,
            "required_resources": self.required_resources,
            "supported_models": self.supported_models,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMetadata:
        return cls(
            agent_type=data.get("agent_type", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            required_resources=data.get("required_resources", {}),
            supported_models=data.get("supported_models", []),
            priority=data.get("priority", 0),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
        )


@dataclass
class AgentInstance:
    """Represents a running agent instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: str = ""
    name: str = ""
    state: AgentState = AgentState.CREATED
    config: AgentConfig = field(default_factory=AgentConfig)
    metadata: AgentMetadata = field(default_factory=AgentMetadata)
    workspace_id: str | None = None
    sandbox_id: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    last_heartbeat: float | None = None
    last_activity: float = field(default_factory=time.time)
    error: str | None = None
    result: Any = None
    task_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "name": self.name,
            "state": self.state.value,
            "config": self.config.to_dict(),
            "metadata": self.metadata.to_dict(),
            "workspace_id": self.workspace_id,
            "sandbox_id": self.sandbox_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_heartbeat": self.last_heartbeat,
            "last_activity": self.last_activity,
            "error": self.error,
            "result": self.result,
            "task_count": self.task_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentInstance:
        state_str = data.get("state", "created")
        try:
            state = AgentState(state_str)
        except ValueError:
            state = AgentState.CREATED

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            agent_type=data.get("agent_type", ""),
            name=data.get("name", ""),
            state=state,
            config=AgentConfig.from_dict(data.get("config", {})),
            metadata=AgentMetadata.from_dict(data.get("metadata", {})),
            workspace_id=data.get("workspace_id"),
            sandbox_id=data.get("sandbox_id"),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            last_heartbeat=data.get("last_heartbeat"),
            last_activity=data.get("last_activity", time.time()),
            error=data.get("error"),
            result=data.get("result"),
            task_count=data.get("task_count", 0),
        )
