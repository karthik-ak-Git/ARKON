"""WorkflowRuntime — the orchestrator.

Loads, validates, compiles, and plans workflows.
Produces ExecutionPlans for the Scheduler.
NEVER executes, NEVER talks to agents, NEVER allocates resources.
"""

from __future__ import annotations

import time
from typing import Any

from app.workflow.compiler import WorkflowCompiler
from app.workflow.exceptions import (
    WorkflowCompilationError,
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowPlanningError,
    WorkflowValidationError,
)
from app.workflow.interfaces import (
    ExecutionPlan,
    ValidationResult,
    WorkflowFormat,
    WorkflowState,
)
from app.workflow.loader import WorkflowLoader
from app.workflow.parser import WorkflowParser
from app.workflow.registry import TemplateRegistry, WorkflowTemplate
from app.workflow.serializer import WorkflowSerializer
from app.workflow.templates import create_default_registry
from app.workflow.validator import WorkflowValidator
from app.workflow.versioning import WorkflowVersionManager


class WorkflowRuntime:
    """Orchestrates workflow loading, validation, compilation, and planning.

    This is the public API for the Workflow Runtime subsystem.
    It never executes work. It produces ExecutionPlans for the Scheduler.
    """

    def __init__(self) -> None:
        self._parser = WorkflowParser()
        self._validator = WorkflowValidator()
        self._compiler = WorkflowCompiler()
        self._loader = WorkflowLoader()
        self._serializer = WorkflowSerializer()
        self._version_manager = WorkflowVersionManager()
        self._registry = create_default_registry()
        self._workflows: dict[str, dict[str, Any]] = {}
        self._plans: dict[str, ExecutionPlan] = {}

    # ── Loading ────────────────────────────────────────────────────────────

    def load(self, definition: dict[str, Any]) -> str:
        wf_id = definition.get("workflow_id", "unknown")
        self._workflows[wf_id] = definition
        return wf_id

    def load_from_string(
        self, content: str, format: WorkflowFormat | None = None
    ) -> str:
        definition = self._loader.load_string(content, format)
        return self.load(definition)

    def load_from_file(self, path: str) -> str:
        definition = self._loader.load_file(path)
        return self.load(definition)

    def load_from_template(self, template_id: str) -> str:
        template = self._registry.get(template_id)
        definition = dict(template.definition)
        return self.load(definition)

    # ── Validation ─────────────────────────────────────────────────────────

    def validate(self, workflow_id: str) -> ValidationResult:
        definition = self._get(workflow_id)
        return self._validator.validate(definition)

    def validate_definition(self, definition: dict[str, Any]) -> ValidationResult:
        return self._validator.validate(definition)

    # ── Compilation ────────────────────────────────────────────────────────

    def compile(self, workflow_id: str) -> ExecutionPlan:
        definition = self._get(workflow_id)
        plan = self._compiler.compile(definition)
        self._plans[plan.plan_id] = plan
        return plan

    def compile_definition(self, definition: dict[str, Any]) -> ExecutionPlan:
        plan = self._compiler.compile(definition)
        self._plans[plan.plan_id] = plan
        return plan

    # ── Versioning ─────────────────────────────────────────────────────────

    def save_version(
        self,
        workflow_id: str,
        version: str = "",
        description: str = "",
    ) -> str:
        definition = self._get(workflow_id)
        wv = self._version_manager.create_version(
            workflow_id, definition, version, description
        )
        return wv.version_id

    def get_version(self, workflow_id: str, version: str) -> dict[str, Any]:
        wv = self._version_manager.get_version(workflow_id, version)
        return wv.definition

    def get_latest_version(self, workflow_id: str) -> dict[str, Any]:
        wv = self._version_manager.get_latest(workflow_id)
        return wv.definition

    def list_versions(self, workflow_id: str) -> list[str]:
        return [v.version for v in self._version_manager.list_versions(workflow_id)]

    # ── Templates ──────────────────────────────────────────────────────────

    def register_template(self, template: WorkflowTemplate) -> None:
        self._registry.register(template)

    def get_template(self, template_id: str) -> WorkflowTemplate:
        return self._registry.get(template_id)

    def list_templates(self) -> list[WorkflowTemplate]:
        return self._registry.list_templates()

    # ── Queries ────────────────────────────────────────────────────────────

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        return dict(self._get(workflow_id))

    def list_workflows(self) -> list[str]:
        return list(self._workflows.keys())

    def get_plan(self, plan_id: str) -> ExecutionPlan | None:
        return self._plans.get(plan_id)

    def get_plan_for_workflow(self, workflow_id: str) -> ExecutionPlan | None:
        for plan in self._plans.values():
            if plan.workflow_id == workflow_id:
                return plan
        return None

    def has_workflow(self, workflow_id: str) -> bool:
        return workflow_id in self._workflows

    def remove_workflow(self, workflow_id: str) -> None:
        self._workflows.pop(workflow_id, None)

    # ── Serialization ──────────────────────────────────────────────────────

    def serialize(
        self, workflow_id: str, format: WorkflowFormat = WorkflowFormat.YAML
    ) -> str:
        definition = self._get(workflow_id)
        return self._serializer.serialize(definition, format)

    # ── Internals ──────────────────────────────────────────────────────────

    def _get(self, workflow_id: str) -> dict[str, Any]:
        if workflow_id not in self._workflows:
            raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found")
        return self._workflows[workflow_id]
