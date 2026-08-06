"""Workflow versioning — version tracking and compatibility checks."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.workflow.exceptions import WorkflowVersionError
from app.workflow.interfaces import WorkflowFormat


@dataclass
class WorkflowVersion:
    """A versioned snapshot of a workflow definition."""

    version_id: str = ""
    version: str = "1.0.0"
    workflow_id: str = ""
    definition: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    description: str = ""
    checksum: str = ""


class WorkflowVersionManager:
    """Manages workflow versions."""

    def __init__(self) -> None:
        self._versions: dict[str, list[WorkflowVersion]] = {}

    def create_version(
        self,
        workflow_id: str,
        definition: dict[str, Any],
        version: str = "",
        description: str = "",
    ) -> WorkflowVersion:
        if not version:
            version = self._next_version(workflow_id)

        self._validate_version_format(version)

        wv = WorkflowVersion(
            version_id=f"{workflow_id}:{version}",
            version=version,
            workflow_id=workflow_id,
            definition=dict(definition),
            description=description,
        )

        self._versions.setdefault(workflow_id, []).append(wv)
        return wv

    def get_version(self, workflow_id: str, version: str) -> WorkflowVersion:
        versions = self._versions.get(workflow_id, [])
        for v in versions:
            if v.version == version:
                return v
        raise WorkflowVersionError(
            f"Version '{version}' not found for workflow '{workflow_id}'"
        )

    def get_latest(self, workflow_id: str) -> WorkflowVersion:
        versions = self._versions.get(workflow_id, [])
        if not versions:
            raise WorkflowVersionError(
                f"No versions found for workflow '{workflow_id}'"
            )
        return versions[-1]

    def list_versions(self, workflow_id: str) -> list[WorkflowVersion]:
        return list(self._versions.get(workflow_id, []))

    def list_workflows(self) -> list[str]:
        return list(self._versions.keys())

    def is_compatible(self, version_a: str, version_b: str) -> bool:
        """Check if two versions are compatible (same major version)."""
        self._validate_version_format(version_a)
        self._validate_version_format(version_b)
        major_a = int(version_a.split(".")[0])
        major_b = int(version_b.split(".")[0])
        return major_a == major_b

    def bump_version(
        self,
        current: str,
        bump_type: str = "patch",
    ) -> str:
        self._validate_version_format(current)
        parts = [int(p) for p in current.split(".")]

        if bump_type == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif bump_type == "minor":
            parts[1] += 1
            parts[2] = 0
        elif bump_type == "patch":
            parts[2] += 1
        else:
            raise WorkflowVersionError(f"Unknown bump type: {bump_type}")

        return f"{parts[0]}.{parts[1]}.{parts[2]}"

    def _next_version(self, workflow_id: str) -> str:
        versions = self._versions.get(workflow_id, [])
        if not versions:
            return "1.0.0"
        latest = versions[-1].version
        return self.bump_version(latest, "patch")

    def _validate_version_format(self, version: str) -> None:
        parts = version.split(".")
        if len(parts) != 3:
            raise WorkflowVersionError(f"Invalid version format: {version}")
        if not all(p.isdigit() for p in parts):
            raise WorkflowVersionError(f"Invalid version format: {version}")
