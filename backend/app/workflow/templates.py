"""Built-in workflow templates."""

from __future__ import annotations

from app.workflow.interfaces import WorkflowFormat
from app.workflow.registry import TemplateRegistry, WorkflowTemplate


def _register_linear_pipeline(registry: TemplateRegistry) -> None:
    registry.register(WorkflowTemplate(
        template_id="linear_pipeline",
        name="Linear Pipeline",
        description="A simple linear pipeline: A → B → C",
        tags=["basic", "pipeline"],
        definition={
            "workflow_id": "linear_pipeline",
            "metadata": {"name": "Linear Pipeline", "version": "1.0.0"},
            "nodes": [
                {"node_id": "a", "name": "Step A", "capability": "process"},
                {"node_id": "b", "name": "Step B", "capability": "process"},
                {"node_id": "c", "name": "Step C", "capability": "process"},
            ],
            "edges": [
                {"edge_id": "a_b", "source_node_id": "a", "target_node_id": "b"},
                {"edge_id": "b_c", "source_node_id": "b", "target_node_id": "c"},
            ],
        },
    ))


def _register_fan_out_fan_in(registry: TemplateRegistry) -> None:
    registry.register(WorkflowTemplate(
        template_id="fan_out_fan_in",
        name="Fan-Out Fan-In",
        description="Parallel fan-out with barrier join",
        tags=["parallel", "fan-out"],
        definition={
            "workflow_id": "fan_out_fan_in",
            "metadata": {"name": "Fan-Out Fan-In", "version": "1.0.0"},
            "nodes": [
                {"node_id": "input", "name": "Input", "capability": "input"},
                {"node_id": "branch_a", "name": "Branch A", "capability": "process"},
                {"node_id": "branch_b", "name": "Branch B", "capability": "process"},
                {"node_id": "barrier", "name": "Barrier", "capability": "merge"},
                {"node_id": "output", "name": "Output", "capability": "output"},
            ],
            "edges": [
                {"edge_id": "i_a", "source_node_id": "input", "target_node_id": "branch_a"},
                {"edge_id": "i_b", "source_node_id": "input", "target_node_id": "branch_b"},
                {"edge_id": "a_m", "source_node_id": "branch_a", "target_node_id": "barrier"},
                {"edge_id": "b_m", "source_node_id": "branch_b", "target_node_id": "barrier"},
                {"edge_id": "m_o", "source_node_id": "barrier", "target_node_id": "output"},
            ],
        },
    ))


def _register_conditional(registry: TemplateRegistry) -> None:
    registry.register(WorkflowTemplate(
        template_id="conditional",
        name="Conditional Branch",
        description="Conditional branching workflow",
        tags=["conditional", "branching"],
        definition={
            "workflow_id": "conditional",
            "metadata": {"name": "Conditional Branch", "version": "1.0.0"},
            "nodes": [
                {"node_id": "check", "name": "Condition Check", "capability": "evaluate"},
                {"node_id": "true_path", "name": "True Path", "capability": "process"},
                {"node_id": "false_path", "name": "False Path", "capability": "process"},
                {"node_id": "merge", "name": "Merge", "capability": "merge"},
            ],
            "edges": [
                {"edge_id": "c_t", "source_node_id": "check", "target_node_id": "true_path",
                 "condition": "result == true"},
                {"edge_id": "c_f", "source_node_id": "check", "target_node_id": "false_path",
                 "condition": "result == false"},
                {"edge_id": "t_m", "source_node_id": "true_path", "target_node_id": "merge"},
                {"edge_id": "f_m", "source_node_id": "false_path", "target_node_id": "merge"},
            ],
        },
    ))


def register_builtins(registry: TemplateRegistry) -> None:
    """Register all built-in templates."""
    _register_linear_pipeline(registry)
    _register_fan_out_fan_in(registry)
    _register_conditional(registry)


def create_default_registry() -> TemplateRegistry:
    """Create a registry with all built-in templates."""
    registry = TemplateRegistry()
    register_builtins(registry)
    return registry
