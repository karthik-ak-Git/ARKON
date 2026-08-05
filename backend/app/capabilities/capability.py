"""ARKON Capability Registry - Capability Model.

Defines the Capability data structure.
A capability is a named function that can be performed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.capabilities.interfaces import ICapability


@dataclass
class Capability(ICapability):
    """A named function that can be performed.

    Examples: transcription, caption_generation, video_rendering,
    reasoning, filesystem, vision, speech, browser, python_execution,
    image_generation, search, embedding, summarization.
    """

    name: str
    description: str = ""
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def get_category(self) -> str:
        return self.category

    def get_tags(self) -> list[str]:
        return self.tags.copy()

    def get_version(self) -> str:
        return self.version

    def get_metadata(self) -> dict[str, Any]:
        return self.metadata.copy()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Capability:
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
        )
