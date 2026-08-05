"""ARKON Runtime - Agent Executor.

Executes agent tasks within the runtime.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import structlog

from app.runtime.exceptions import (
    AgentExecutionError,
    AgentNotRunningError,
    TaskValidationError,
)

logger = structlog.get_logger(__name__)


@dataclass
class ExecutionTask:
    """A task to be executed by an agent."""
    id: str = ""
    agent_id: str = ""
    task_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timeout: float = 300.0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    status: str = "pending"
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "timeout": self.timeout,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class AgentExecutor:
    """Executes agent tasks within the runtime."""

    def __init__(
        self,
        event_handler: Callable | None = None,
    ) -> None:
        """Initialize executor."""
        self._event_handler = event_handler
        self._tasks: dict[str, ExecutionTask] = {}
        self._executions: dict[str, asyncio.Task] = {}

    async def execute(
        self,
        agent_id: str,
        task: dict[str, Any],
        agent: Any = None,
        context: Any = None,
    ) -> Any:
        """Execute a task for an agent.

        Args:
            agent_id: The agent to execute for.
            task: Task specification.
            agent: The agent instance.
            context: Execution context.

        Returns:
            Task result.

        Raises:
            AgentExecutionError: If execution fails.
        """
        task_id = task.get("id", f"task_{agent_id}_{int(time.time())}")
        task_type = task.get("type", "unknown")

        execution_task = ExecutionTask(
            id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            payload=task.get("payload", {}),
            timeout=task.get("timeout", 300.0),
            status="running",
            started_at=time.time(),
        )
        self._tasks[task_id] = execution_task

        try:
            if agent is None:
                raise AgentExecutionError(
                    agent_id, "No agent instance provided"
                )

            # Execute through agent
            result = await asyncio.wait_for(
                agent.execute(task),
                timeout=execution_task.timeout,
            )

            execution_task.status = "completed"
            execution_task.result = result
            execution_task.completed_at = time.time()

            logger.info(
                "task_completed",
                task_id=task_id,
                agent_id=agent_id,
                task_type=task_type,
            )

            return result

        except asyncio.TimeoutError:
            execution_task.status = "failed"
            execution_task.error = f"Timeout after {execution_task.timeout}s"
            execution_task.completed_at = time.time()

            raise AgentExecutionError(
                agent_id,
                f"Task timed out after {execution_task.timeout}s",
            )

        except Exception as e:
            execution_task.status = "failed"
            execution_task.error = str(e)
            execution_task.completed_at = time.time()

            raise AgentExecutionError(agent_id, str(e)) from e

    async def cancel(self, agent_id: str) -> None:
        """Cancel an execution."""
        for task_id, task in self._tasks.items():
            if task.agent_id == agent_id and task.status == "running":
                task.status = "cancelled"
                task.completed_at = time.time()

                if task_id in self._executions:
                    self._executions[task_id].cancel()
                    del self._executions[task_id]

    async def get_status(self, agent_id: str) -> dict[str, Any]:
        """Get execution status for an agent."""
        agent_tasks = [
            t for t in self._tasks.values()
            if t.agent_id == agent_id
        ]

        running = [
            t.to_dict() for t in agent_tasks
            if t.status == "running"
        ]
        completed = [
            t.to_dict() for t in agent_tasks
            if t.status == "completed"
        ]
        failed = [
            t.to_dict() for t in agent_tasks
            if t.status == "failed"
        ]

        return {
            "agent_id": agent_id,
            "total_tasks": len(agent_tasks),
            "running": running,
            "completed": completed,
            "failed": failed,
        }

    def get_task(self, task_id: str) -> ExecutionTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[ExecutionTask]:
        """Get all tasks."""
        return list(self._tasks.values())

    async def cleanup(self) -> None:
        """Cleanup completed tasks."""
        to_remove = [
            tid for tid, task in self._tasks.items()
            if task.status in ("completed", "failed", "cancelled")
        ]
        for tid in to_remove:
            del self._tasks[tid]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tasks": len(self._tasks),
            "tasks": [t.to_dict() for t in self._tasks.values()],
        }
