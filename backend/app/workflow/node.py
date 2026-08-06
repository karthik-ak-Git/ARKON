"""Workflow node definition.

Nodes describe intent. They reference capabilities.
They never execute. They never reference agents or providers.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.workflow.interfaces import (
    Condition,
    LoopConfig,
    NodeState,
    Port,
)


@dataclass
class WorkflowNode:
    """A workflow node.

    Nodes describe WHAT should happen (capability), not HOW (implementation).
    """

    node_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = ""
    capability: str = ""
    description: str = ""
    state: NodeState = NodeState.PENDING
    priority: int = 5
    timeout: float | None = None
    max_retries: int = 3
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)
    loop: LoopConfig | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    resource_requirements: dict[str, float] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def get_input(self, name: str) -> Port | None:
        for port in self.inputs:
            if port.name == name:
                return port
        return None

    def get_output(self, name: str) -> Port | None:
        for port in self.outputs:
            if port.name == name:
                return port
        return None

    def has_required_inputs(self) -> bool:
        return all(p.required for p in self.inputs)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "node_id": self.node_id,
            "name": self.name,
            "capability": self.capability,
            "description": self.description,
            "state": self.state.value,
            "priority": self.priority,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
            "conditions": [c.to_dict() for c in self.conditions],
            "loop": self.loop.to_dict() if self.loop else None,
            "metadata": self.metadata,
            "tags": self.tags,
            "resource_requirements": self.resource_requirements,
            "config": self.config,
            "created_at": self.created_at,
        }
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowNode:
        data = dict(data)
        data["state"] = NodeState(data.get("state", "pending"))
        data["inputs"] = [Port.from_dict(p) for p in data.get("inputs", [])]
        data["outputs"] = [Port.from_dict(p) for p in data.get("outputs", [])]
        data["conditions"] = [Condition.from_dict(c) for c in data.get("conditions", [])]
        loop_data = data.get("loop")
        data["loop"] = LoopConfig.from_dict(loop_data) if loop_data else None
        known = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in known})
