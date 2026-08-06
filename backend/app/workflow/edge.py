"""Workflow edge definition.

Edges define data/control flow between nodes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.workflow.interfaces import EdgeType


@dataclass
class WorkflowEdge:
    """A workflow edge connecting two nodes."""

    edge_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    source_node_id: str = ""
    target_node_id: str = ""
    source_port: str = ""
    target_port: str = ""
    edge_type: EdgeType = EdgeType.DATA
    condition: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def connects(self, source: str, target: str) -> bool:
        return self.source_node_id == source and self.target_node_id == target

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "source_port": self.source_port,
            "target_port": self.target_port,
            "edge_type": self.edge_type.value,
            "condition": self.condition,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowEdge:
        data = dict(data)
        data["edge_type"] = EdgeType(data.get("edge_type", "data"))
        known = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in known})
