# Workflow Runtime

DAG-based workflow engine for orchestrating multi-step agent tasks.

## Concepts

- **Workflow** — a named collection of nodes and edges
- **Node** — a single step with typed inputs/outputs
- **Edge** — a dependency connection between nodes
- **Planner** — resolves execution order from the DAG

## Creating Workflows

```json
{
  "name": "video-pipeline",
  "nodes": [
    {"id": "input", "type": "input"},
    {"id": "process", "type": "transform", "depends_on": ["input"]},
    {"id": "output", "type": "output", "depends_on": ["process"]}
  ]
}
```

## Features

- Parallel execution of independent nodes
- Checkpoint and recovery on failure
- Event-driven state transitions
- Version management for workflow definitions
- Dynamic node registration via plugins
