"""Workflow serializer — converts workflows to/from various formats."""

from __future__ import annotations

import json
from typing import Any

from app.workflow.exceptions import SerializerError
from app.workflow.interfaces import WorkflowFormat

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class WorkflowSerializer:
    """Serializes workflow definitions to YAML/JSON strings."""

    def serialize(self, definition: dict[str, Any], format: WorkflowFormat = WorkflowFormat.YAML) -> str:
        if format == WorkflowFormat.JSON:
            return self._to_json(definition)
        elif format == WorkflowFormat.YAML:
            return self._to_yaml(definition)
        else:
            raise SerializerError(f"Unsupported format: {format}")

    def deserialize(self, content: str, format: WorkflowFormat = WorkflowFormat.YAML) -> dict[str, Any]:
        if not content or not content.strip():
            raise SerializerError("Empty content")

        if format == WorkflowFormat.JSON:
            return self._from_json(content)
        elif format == WorkflowFormat.YAML:
            return self._from_yaml(content)
        else:
            raise SerializerError(f"Unsupported format: {format}")

    def _to_json(self, definition: dict[str, Any]) -> str:
        try:
            return json.dumps(definition, indent=2, default=str)
        except (TypeError, ValueError) as e:
            raise SerializerError(f"JSON serialization failed: {e}") from e

    def _to_yaml(self, definition: dict[str, Any]) -> str:
        if not HAS_YAML:
            raise SerializerError("PyYAML not installed")
        try:
            return yaml.dump(definition, default_flow_style=False, sort_keys=False)
        except yaml.YAMLError as e:
            raise SerializerError(f"YAML serialization failed: {e}") from e

    def _from_json(self, content: str) -> dict[str, Any]:
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise SerializerError(f"JSON deserialization failed: {e}") from e
        if not isinstance(result, dict):
            raise SerializerError("JSON root must be an object")
        return result

    def _from_yaml(self, content: str) -> dict[str, Any]:
        if not HAS_YAML:
            raise SerializerError("PyYAML not installed")
        try:
            result = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise SerializerError(f"YAML deserialization failed: {e}") from e
        if not isinstance(result, dict):
            raise SerializerError("YAML root must be a mapping")
        return result

    def to_canonical(self, definition: dict[str, Any]) -> str:
        """Serialize to canonical JSON for comparison/hashing."""
        return json.dumps(definition, sort_keys=True, separators=(",", ":"), default=str)
