"""ARKON Runtime - Agent Registry.

Stores agent metadata only.
The Registry does NOT execute agents.
"""

from __future__ import annotations

import time
from typing import Any

import structlog

from app.runtime.exceptions import (
    AgentTypeAlreadyRegisteredError,
    AgentTypeNotFoundError,
)

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """Registry stores metadata only.

    The Registry does NOT execute agents.
    It stores:
    - id, name, version, author, description
    - capabilities, required resources
    - supported models, priority, dependencies, tags
    """

    def __init__(self) -> None:
        self._agents: dict[str, dict[str, Any]] = {}

    async def register(
        self,
        agent_type: str,
        metadata: dict[str, Any],
    ) -> None:
        """Register an agent type with metadata.

        Args:
            agent_type: Unique agent type identifier.
            metadata: Agent metadata.

        Raises:
            AgentTypeAlreadyRegisteredError: If already registered.
        """
        if agent_type in self._agents:
            raise AgentTypeAlreadyRegisteredError(agent_type)

        self._agents[agent_type] = {
            **metadata,
            "agent_type": agent_type,
            "registered_at": time.time(),
        }

        logger.info(
            "agent_type_registered",
            agent_type=agent_type,
            capabilities=metadata.get("capabilities", []),
        )

    async def unregister(self, agent_type: str) -> None:
        """Unregister an agent type."""
        if agent_type not in self._agents:
            raise AgentTypeNotFoundError(agent_type)

        del self._agents[agent_type]
        logger.info("agent_type_unregistered", agent_type=agent_type)

    async def get(self, agent_type: str) -> dict[str, Any] | None:
        """Get metadata for an agent type."""
        return self._agents.get(agent_type)

    async def list_all(self) -> list[dict[str, Any]]:
        """List all registered agent types."""
        return list(self._agents.values())

    async def find_by_capability(self, capability: str) -> list[dict[str, Any]]:
        """Find agents that provide a specific capability."""
        result = []
        for metadata in self._agents.values():
            caps = metadata.get("capabilities", [])
            if capability in caps:
                result.append(metadata)
        return result

    async def find_by_capabilities(
        self, capabilities: list[str]
    ) -> list[dict[str, Any]]:
        """Find agents that provide all specified capabilities."""
        if not capabilities:
            return list(self._agents.values())

        result = []
        for metadata in self._agents.values():
            agent_caps = set(metadata.get("capabilities", []))
            if all(c in agent_caps for c in capabilities):
                result.append(metadata)
        return result

    async def find_by_tags(self, tags: list[str]) -> list[dict[str, Any]]:
        """Find agents with specified tags."""
        result = []
        for metadata in self._agents.values():
            agent_tags = set(metadata.get("tags", []))
            if any(t in agent_tags for t in tags):
                result.append(metadata)
        return result

    async def find_by_model(self, model: str) -> list[dict[str, Any]]:
        """Find agents that support a specific model."""
        result = []
        for metadata in self._agents.values():
            models = metadata.get("supported_models", [])
            if model in models:
                result.append(metadata)
        return result

    def count(self) -> int:
        """Get count of registered agents."""
        return len(self._agents)

    def exists(self, agent_type: str) -> bool:
        """Check if agent type is registered."""
        return agent_type in self._agents

    async def clear(self) -> None:
        """Clear all registrations."""
        self._agents.clear()
        logger.info("agent_registry_cleared")

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self._agents),
            "agents": dict(self._agents),
        }
