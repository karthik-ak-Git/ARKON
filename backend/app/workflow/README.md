# Workflow Runtime

Workflow definition, validation, compilation, and planning system for ARKON. Workflows describe multi-step AI pipelines as directed acyclic graphs of capability-based nodes.

## Architecture

```
WorkflowRuntime
├── WorkflowParser         — Parse YAML/JSON workflow definitions
├── WorkflowValidator      — Validate schema, references, cycles, capabilities, ports
├── WorkflowCompiler       — Compile validated definitions into execution plans
├── WorkflowPlanner        — Plan execution order, identify parallelism, critical path
├── WorkflowSerializer     — Serialize/deserialize workflow definitions
├── WorkflowLoader         — Load/save from files, strings, directories
├── WorkflowVersionManager — Version control for workflow definitions
├── TemplateRegistry       — Builtin + custom workflow templates
└── WorkflowNode/Edge/DAG  — Graph primitives for workflow structure
```

## Key Concepts

- **Workflow definition** is a plain `dict[str, Any]` — no workflow object carries state through the system
- **Nodes** describe intent via `capability` strings — never reference specific agents or providers
- **Edges** connect node outputs to inputs — no self-loops
- **DAG** validates the workflow is acyclic, finds topological order, identifies critical path
- **Planner** produces an `ExecutionPlan` with ordered tasks and parallelizable groups
- **Compiler** converts validated definitions into executable plans
- **Scheduler** (separate module) receives plans and executes them

## Files

| File | Purpose |
|------|---------|
| `interfaces.py` | Enums, dataclasses (`Port`, `Condition`, `LoopConfig`, `ParallelConfig`, `WorkflowMetadata`, `ExecutionPlanTask`, `ExecutionPlan`, `ValidationResult`), protocols |
| `exceptions.py` | `WorkflowError` hierarchy (14 exception types) |
| `events.py` | Event factory functions for workflow lifecycle events |
| `node.py` | `WorkflowNode` — input/output port management, timeout, retries |
| `edge.py` | `WorkflowEdge` — connection validation, port existence checks |
| `dag.py` | `WorkflowDAG` — graph operations, topological sort, cycle detection, critical path |
| `parser.py` | `WorkflowParser` — YAML/JSON parsing with format detection |
| `validator.py` | `WorkflowValidator` — schema, references, cycles, capabilities, port validation |
| `compiler.py` | `WorkflowCompiler` — definition → `ExecutionPlan` |
| `planner.py` | `WorkflowPlanner` — execution order, parallelism, critical path planning |
| `serializer.py` | `WorkflowSerializer` — round-trip YAML/JSON serialization, canonical form |
| `loader.py` | `WorkflowLoader` — file/string/directory loading and saving |
| `versioning.py` | `WorkflowVersionManager` — semantic versioning for workflow definitions |
| `registry.py` | `TemplateRegistry` + `WorkflowTemplate` — template management |
| `templates.py` | `register_builtins()` — builtin workflow templates (linear, parallel, conditional, loop, fan-out, fan-in, sequential, pipeline, aggregation, error-handling) |
| `runtime.py` | `WorkflowRuntime` — orchestrator facade |

## Usage

```python
from app.workflow.runtime import WorkflowRuntime

runtime = WorkflowRuntime()

# Load a workflow
runtime.load("my_workflow", workflow_dict)

# Validate
result = runtime.validate("my_workflow")
assert result.is_valid

# Compile to execution plan
plan = runtime.compile("my_workflow")

# Serialize
yaml_str = runtime.serialize("my_workflow", format="yaml")
json_str = runtime.serialize("my_workflow", format="json")
```

## Builtin Templates

- **Linear** — sequential task chain
- **Parallel** — concurrent independent tasks with barrier
- **Conditional Branch** — decision node with true/false branches
- **Loop** — iterative processing with conditions
- **Fan-Out / Fan-In** — parallel split with result aggregation
- **Sequential Pipeline** — ordered pipeline with dependencies
- **Aggregation** — collect results from multiple sources
- **Error Handling** — try/catch pattern with fallback
