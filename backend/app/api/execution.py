"""ARKON Execution Engine - REST API.

Endpoints for task submission, status, and management.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any

router = APIRouter(prefix="/api/v1/execution", tags=["execution"])


# --- Request / Response Schemas ---


class SubmitTaskRequest(BaseModel):
    """Request to submit a task."""
    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Task type for handler routing")
    priority: float = Field(default=0.0, description="Lower = higher priority")
    payload: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    max_retries: int = Field(default=3)


class SubmitTaskResponse(BaseModel):
    """Response after submitting a task."""
    task_id: str
    state: str
    message: str


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    state: str
    priority: float
    is_cancelled: bool
    progress: dict[str, Any]


class TaskResultResponse(BaseModel):
    """Task result response."""
    task_id: str
    success: bool
    output: Any = None
    artifacts: list[dict[str, Any]] = []
    duration: float = 0.0
    errors: list[str] = []
    warnings: list[str] = []


class CancelRequest(BaseModel):
    """Request to cancel a task."""
    reason: str = ""


class ExecutionSummaryResponse(BaseModel):
    """Execution summary response."""
    total_tasks: int
    by_state: dict[str, int]
    queue_size: int
    dependency_graph: dict[str, Any]


# --- Endpoints ---


@router.post("/tasks", response_model=SubmitTaskResponse)
async def submit_task(request: SubmitTaskRequest) -> SubmitTaskResponse:
    """Submit a task for execution."""
    from app.execution import ExecutionEngine, Task
    engine = ExecutionEngine()

    task = Task(
        task_id=request.task_id,
        task_type=request.task_type,
        priority=request.priority,
        payload=request.payload,
    )

    try:
        task_id = await engine.submit(task, request.dependencies)
        return SubmitTaskResponse(
            task_id=task_id,
            state="queued",
            message="Task submitted successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get task status."""
    from app.execution import ExecutionEngine
    engine = ExecutionEngine()

    status = await engine.get_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return TaskStatusResponse(**status)


@router.get("/tasks/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(task_id: str) -> TaskResultResponse:
    """Get task result."""
    from app.execution import ExecutionEngine
    engine = ExecutionEngine()

    result = await engine.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Result not found: {task_id}")

    return TaskResultResponse(**result)


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, request: CancelRequest) -> dict:
    """Cancel a task."""
    from app.execution import ExecutionEngine
    engine = ExecutionEngine()

    success = await engine.cancel(task_id, request.reason)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return {"task_id": task_id, "cancelled": True, "reason": request.reason}


@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str) -> dict:
    """Pause a running task."""
    from app.execution import ExecutionEngine
    engine = ExecutionEngine()

    success = await engine.pause(task_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Cannot pause task: {task_id}")

    return {"task_id": task_id, "paused": True}


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str) -> dict:
    """Resume a paused task."""
    from app.execution import ExecutionEngine
    engine = ExecutionEngine()

    success = await engine.resume(task_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Cannot resume task: {task_id}")

    return {"task_id": task_id, "resumed": True}


@router.get("/summary", response_model=ExecutionSummaryResponse)
async def get_execution_summary() -> ExecutionSummaryResponse:
    """Get execution summary."""
    from app.execution import ExecutionEngine
    engine = ExecutionEngine()

    summary = engine.get_execution_summary()
    return ExecutionSummaryResponse(**summary)
