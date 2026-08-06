"""Workflow template registry.

Stores and retrieves workflow templates.
"""

from __future__ import annotations

from typing import Any

from app.workflow.exceptions import TemplateNotFoundError, RegistryError
from app.workflow.interfaces import WorkflowFormat


class WorkflowTemplate:
    """A stored workflow template."""

    def __init__(
        self,
        template_id: str,
        name: str,
        definition: dict[str, Any],
        description: str = "",
        tags: list[str] | None = None,
        format: WorkflowFormat = WorkflowFormat.YAML,
    ) -> None:
        self.template_id = template_id
        self.name = name
        self.description = description
        self.definition = definition
        self.tags = tags or []
        self.format = format

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "definition": self.definition,
            "tags": self.tags,
            "format": self.format.value,
        }


class TemplateRegistry:
    """Registry for workflow templates."""

    def __init__(self) -> None:
        self._templates: dict[str, WorkflowTemplate] = {}

    def register(self, template: WorkflowTemplate) -> None:
        if template.template_id in self._templates:
            raise RegistryError(
                f"Template '{template.template_id}' already registered"
            )
        self._templates[template.template_id] = template

    def unregister(self, template_id: str) -> None:
        self._templates.pop(template_id, None)

    def get(self, template_id: str) -> WorkflowTemplate:
        if template_id not in self._templates:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")
        return self._templates[template_id]

    def list_templates(self) -> list[WorkflowTemplate]:
        return list(self._templates.values())

    def list_by_tag(self, tag: str) -> list[WorkflowTemplate]:
        return [t for t in self._templates.values() if tag in t.tags]

    def has(self, template_id: str) -> bool:
        return template_id in self._templates

    def count(self) -> int:
        return len(self._templates)

    def clear(self) -> None:
        self._templates.clear()
