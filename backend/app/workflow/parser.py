"""Workflow parser — YAML/JSON parsing.

Parses workflow definitions into dicts. No validation, no compilation.
"""

from __future__ import annotations

import json
from typing import Any

from app.workflow.exceptions import WorkflowParseError
from app.workflow.interfaces import WorkflowFormat

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class WorkflowParser:
    """Parses workflow definitions from YAML or JSON strings."""

    def parse(self, content: str, format: WorkflowFormat = WorkflowFormat.YAML) -> dict[str, Any]:
        if not content or not content.strip():
            raise WorkflowParseError("Empty workflow definition")

        try:
            if format == WorkflowFormat.YAML:
                return self._parse_yaml(content)
            elif format == WorkflowFormat.JSON:
                return self._parse_json(content)
            else:
                raise WorkflowParseError(f"Unsupported format: {format}")
        except WorkflowParseError:
            raise
        except Exception as e:
            raise WorkflowParseError(f"Parse error: {e}") from e

    def _parse_yaml(self, content: str) -> dict[str, Any]:
        if not HAS_YAML:
            raise WorkflowParseError(
                "PyYAML not installed. Install with: pip install pyyaml"
            )
        try:
            result = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise WorkflowParseError(f"YAML parse error: {e}") from e

        if not isinstance(result, dict):
            raise WorkflowParseError("YAML must contain a mapping at the root")
        return result

    def _parse_json(self, content: str) -> dict[str, Any]:
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            raise WorkflowParseError(f"JSON parse error: {e}") from e

        if not isinstance(result, dict):
            raise WorkflowParseError("JSON must contain an object at the root")
        return result

    def detect_format(self, content: str) -> WorkflowFormat:
        content = content.strip()
        if content.startswith("{") or content.startswith("["):
            return WorkflowFormat.JSON
        return WorkflowFormat.YAML
