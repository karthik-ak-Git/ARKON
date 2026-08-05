"""ARKON Runtime - Capability Registry.

Mandatory capability system.
Every agent registers capabilities.
Never hardcode agent names.

The scheduler will later ask:
"Who can perform capability X?"

Never:
"Run CaptionAgent"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from app.runtime.exceptions import CapabilityNotFoundError

logger = structlog.get_logger(__name__)


@dataclass
class Capability:
    """A registered capability."""
    name: str
    description: str = ""
    agent_types: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityRegistry:
    """Mandatory capability registry.

    Every agent registers capabilities.
    The scheduler queries this to find agents.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(
        self,
        capability: str,
        agent_type: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a capability for an agent type."""
        if capability not in self._capabilities:
            self._capabilities[capability] = Capability(
                name=capability,
                description=description,
            )

        cap = self._capabilities[capability]
        if agent_type not in cap.agent_types:
            cap.agent_types.append(agent_type)

        if metadata:
            cap.metadata.update(metadata)

        logger.debug(
            "capability_registered",
            capability=capability,
            agent_type=agent_type,
        )

    def unregister(self, capability: str, agent_type: str) -> None:
        """Unregister a capability for an agent type."""
        if capability in self._capabilities:
            cap = self._capabilities[capability]
            if agent_type in cap.agent_types:
                cap.agent_types.remove(agent_type)
            if not cap.agent_types:
                del self._capabilities[capability]

    def find(self, capability: str) -> list[str]:
        """Find agent types that provide a capability."""
        if capability not in self._capabilities:
            return []
        return self._capabilities[capability].agent_types.copy()

    def find_all(
        self, capabilities: list[str]
    ) -> dict[str, list[str]]:
        """Find agent types for all capabilities.

        Returns:
            Dict mapping capability to list of agent types.
        """
        result = {}
        for cap in capabilities:
            result[cap] = self.find(cap)
        return result

    def find_agents_with_all(
        self, capabilities: list[str]
    ) -> list[str]:
        """Find agent types that provide ALL specified capabilities."""
        if not capabilities:
            return []

        sets = []
        for cap in capabilities:
            agents = self.find(cap)
            if not agents:
                return []
            sets.append(set(agents))

        intersection = sets[0]
        for s in sets[1:]:
            intersection = intersection & s

        return list(intersection)

    def find_agents_with_any(
        self, capabilities: list[str]
    ) -> list[str]:
        """Find agent types that provide ANY of the specified capabilities."""
        result = set()
        for cap in capabilities:
            result.update(self.find(cap))
        return list(result)

    def get_all(self) -> dict[str, Capability]:
        """Get all capabilities."""
        return self._capabilities.copy()

    def get_capability(self, name: str) -> Capability | None:
        """Get a specific capability."""
        return self._capabilities.get(name)

    def list_capability_names(self) -> list[str]:
        """List all capability names."""
        return list(self._capabilities.keys())

    def clear(self) -> None:
        """Clear all capabilities."""
        self._capabilities.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            name: {
                "name": cap.name,
                "description": cap.description,
                "agent_types": cap.agent_types,
                "metadata": cap.metadata,
            }
            for name, cap in self._capabilities.items()
        }
