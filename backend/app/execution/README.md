# ARKON Execution Engine

Task execution pipeline with dependency management, cancellation, progress tracking, and recovery.

## Architecture

The Execution Engine manages tasks; the Runtime manages agents — these are different responsibilities.

```
Scheduler (future) → Execution Engine → Runtime → Agent
```

## Components

- **TaskQueue**: Priority-based task queue
- **TaskDispatcher**: Routes tasks to handlers by type
- **TaskExecutor**: Executes tasks with lifecycle management
- **DependencyGraph**: DAG-based dependency resolution
- **CancellationManager**: Task cancellation support
- **ProgressTracker**: Progress reporting
- **ResultStore**: Task result storage
- **CheckpointManager**: Checkpoint creation and management
- **RecoveryManager**: Task recovery strategies
- **RetryManager**: Retry policies and execution

## Usage

```python
from app.execution import ExecutionEngine, Task

engine = ExecutionEngine()

# Register a handler
async def my_handler(task):
    return {"result": "success"}

engine.register_handler("my_task", my_handler)

# Submit a task
task = Task(task_id="task-1", task_type="my_task")
await engine.submit(task)

# Process
await engine.process_all()
```

## Design Principles

1. **No business logic** — only execution infrastructure
2. **Scheduler-friendly** — designed so a future Scheduler can submit work
3. **Dependency-aware** — DAG-based task ordering
4. **Resilient** — checkpointing and recovery support
