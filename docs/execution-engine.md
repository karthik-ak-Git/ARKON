# Execution Engine

Task dispatch, dependency resolution, and lifecycle management.

## Task States

```
PENDING → RUNNING → COMPLETED
                ↘ FAILED → RETRYING → RUNNING
                ↘ CANCELLED
```

## Features

- **Dependency Resolution** — tasks run only when prerequisites complete
- **Checkpoint/Restart** — save progress and resume on failure
- **Retry Logic** — configurable retry with backoff
- **Progress Tracking** — real-time progress updates via WebSocket
- **Cancellation** — graceful task cancellation

## API

```bash
# Submit a task
POST /api/v1/execution/submit
{
  "task_type": "agent_run",
  "agent_id": "agent-01",
  "input_data": {"action": "process"}
}

# Check status
GET /api/v1/execution/{task_id}

# Cancel
POST /api/v1/execution/{task_id}/cancel
```
