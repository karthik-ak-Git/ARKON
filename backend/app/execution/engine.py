"""ARKON Execution Engine - Main Engine.

Central orchestrator for the entire task execution pipeline.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable

import structlog

from app.execution.interfaces import (
    ITask,
    IExecutionEngine,
    TaskState,
    RetryPolicy,
    CheckpointPolicy,
)
from app.execution.exceptions import (
    TaskAlreadyExistsError,
    TaskNotFoundError,
    ExecutionEngineError,
)
from app.execution.task import Task, RetryConfig, CheckpointConfig
from app.execution.queue import TaskQueue
from app.execution.dispatcher import TaskDispatcher
from app.execution.executor import TaskExecutor
from app.execution.dependency_graph import DependencyGraph
from app.execution.cancellation import CancellationManager
from app.execution.progress import ProgressTracker
from app.execution.results import ResultStore, TaskResult

logger = structlog.get_logger(__name__)


class ExecutionEngine(IExecutionEngine):
    """Main execution engine.

    Orchestrates the full task lifecycle:
    - Task creation
    - Dependency resolution
    - Queuing
    - Dispatching
    - Execution
    - Result collection

    Designed so that a future Scheduler can submit work into it.
    """

    def __init__(self) -> None:
        """Initialize execution engine with all subcomponents."""
        self._queue = TaskQueue()
        self._dispatcher = TaskDispatcher()
        self._executor = TaskExecutor()
        self._dependency_graph = DependencyGraph()
        self._cancellation = CancellationManager()
        self._progress = ProgressTracker()
        self._results = ResultStore()

        self._running = False
        self._task_handlers: dict[str, Callable[[ITask], Awaitable[dict[str, Any]]]] = {}
        self._tasks: dict[str, ITask] = {}

    async def create_task(
        self,
        capability: str,
        payload: dict[str, Any],
        workspace_id: str | None = None,
        agent_id: str | None = None,
        priority: int = 0,
        dependencies: list[str] | None = None,
        timeout: float | None = None,
        retry_policy: RetryPolicy = RetryPolicy.IMMEDIATE,
        max_retries: int = 3,
        checkpoint_policy: CheckpointPolicy = CheckpointPolicy.MANUAL,
        metadata: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> str:
        """Create a new task.

        Args:
            capability: Task capability type.
            payload: Task payload data.
            workspace_id: Optional workspace ID.
            agent_id: Optional agent ID.
            priority: Task priority (lower = higher priority).
            dependencies: Optional task IDs this task depends on.
            timeout: Optional execution timeout.
            retry_policy: Retry strategy.
            max_retries: Maximum retry attempts.
            checkpoint_policy: Checkpoint strategy.
            metadata: Optional metadata.

        Returns:
            Task ID.

        Raises:
            TaskAlreadyExistsError: If task ID already exists.
        """
        task = Task(
            capability=capability,
            payload=payload,
            workspace_id=workspace_id or "",
            agent_id=agent_id or "",
            priority=priority,
            dependencies=dependencies or [],
            timeout=timeout,
            retry_config=RetryConfig(
                policy=retry_policy,
                max_retries=max_retries,
            ),
            checkpoint_config=CheckpointConfig(
                policy=checkpoint_policy,
            ),
            metadata=metadata or {},
            **({"task_id": task_id} if task_id else {}),
        )

        task_id = task.get_id()

        if task_id in self._tasks:
            raise TaskAlreadyExistsError(task_id)

        # Store task
        self._tasks[task_id] = task

        # Add to dependency graph
        self._dependency_graph.add_task(task_id)

        # Register dependencies
        if dependencies:
            for dep_id in dependencies:
                self._dependency_graph.add_dependency(task_id, dep_id)

        logger.info(
            "task_created",
            task_id=task_id,
            capability=capability,
            has_dependencies=bool(dependencies),
        )

        return task_id

    async def dispatch(self, task_id: str) -> None:
        """Dispatch a task to an agent.

        Args:
            task_id: Task to dispatch.

        Raises:
            TaskNotFoundError: If task not found.
        """
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        # Check if dependencies are met
        ready_tasks = self._dependency_graph.get_ready_tasks()
        if task_id not in ready_tasks:
            logger.debug("task_dependencies_not_met", task_id=task_id)
            return

        # Transition to QUEUED
        task.state = TaskState.QUEUED
        task.queued_at = __import__("time").time()

        # Enqueue
        await self._queue.enqueue(task)

        logger.info("task_dispatched", task_id=task_id)

    async def execute(self, task_id: str) -> Any:
        """Execute a task.

        Args:
            task_id: Task to execute.

        Returns:
            Execution result.

        Raises:
            TaskNotFoundError: If task not found.
        """
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        handler = self._task_handlers.get(task.get_capability())
        if handler is None:
            logger.warning("no_handler_for_capability", capability=task.get_capability())
            return None

        try:
            result = await self._executor.execute(task, handler)

            # Mark as done in dependency graph
            self._dependency_graph.mark_done(task_id)

            # Store result
            exec_result = self._executor.get_result(task_id)
            if exec_result:
                result_obj = TaskResult(
                    task_id=task_id,
                    success=exec_result.get("success", True),
                    output=exec_result.get("output"),
                    duration=exec_result.get("duration", 0.0),
                )
                self._results.store(result_obj)

            return result

        except Exception as e:
            logger.error(
                "task_execution_failed",
                task_id=task_id,
                error=str(e),
            )
            # Mark as failed in dependency graph
            self._dependency_graph.mark_failed(task_id)
            raise

    async def pause(self, task_id: str) -> None:
        """Pause a running task."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        current_state = task.get_state()
        if current_state != TaskState.EXECUTING:
            logger.warning("cannot_pause_task", task_id=task_id, state=current_state.value)
            return

        task.state = TaskState.PAUSED
        logger.info("task_paused", task_id=task_id)

    async def resume(self, task_id: str) -> None:
        """Resume a paused task."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        current_state = task.get_state()
        if current_state != TaskState.PAUSED:
            logger.warning("cannot_resume_task", task_id=task_id, state=current_state.value)
            return

        task.state = TaskState.EXECUTING
        logger.info("task_resumed", task_id=task_id)

    async def cancel(self, task_id: str) -> None:
        """Cancel a task."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        # Request cancellation
        self._cancellation.request_cancellation(task_id, "user_cancelled")

        # Cancel if in queue
        await self._queue.remove(task_id)

        # Transition to CANCELLED
        task.state = TaskState.CANCELLED
        task.cancelled_at = __import__("time").time()

        # Mark as done in dependency graph
        self._dependency_graph.mark_done(task_id)

        logger.info("task_cancelled", task_id=task_id)

    async def retry(self, task_id: str) -> None:
        """Retry a failed task."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        current_state = task.get_state()
        if current_state not in {TaskState.FAILED, TaskState.TIMED_OUT}:
            logger.warning("cannot_retry_task", task_id=task_id, state=current_state.value)
            return

        task.state = TaskState.RECOVERING
        task.attempt += 1

        logger.info("task_retry_started", task_id=task_id, attempt=task.attempt)

    async def recover(self, task_id: str) -> None:
        """Recover a task from checkpoint."""
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        current_state = task.get_state()
        if current_state != TaskState.RECOVERING:
            logger.warning("cannot_recover_task", task_id=task_id, state=current_state.value)
            return

        # Re-queue the task
        task.state = TaskState.QUEUED
        task.queued_at = __import__("time").time()
        await self._queue.enqueue(task)

        logger.info("task_recovered", task_id=task_id)

    async def get_task(self, task_id: str) -> Any:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    async def list_tasks(self, state: TaskState | None = None) -> list[Any]:
        """List tasks, optionally filtered by state."""
        if state is None:
            return list(self._tasks.values())
        return [t for t in self._tasks.values() if t.get_state() == state]

    async def get_progress(self, task_id: str) -> dict[str, Any]:
        """Get task progress."""
        return self._progress.get_progress(task_id)

    async def get_result(self, task_id: str) -> Any:
        """Get task result."""
        result = self._results.get(task_id)
        return result.to_dict() if result else None

    async def shutdown(self) -> None:
        """Gracefully shut down the engine."""
        logger.info("engine_shutting_down")
        self._running = False
        # Cancel all pending tasks
        for task_id, task in self._tasks.items():
            if task.get_state() in {TaskState.QUEUED, TaskState.DISPATCHED}:
                await self.cancel(task_id)
        logger.info("engine_shutdown_complete")

    def register_handler(
        self,
        capability: str,
        handler: Callable[[ITask], Awaitable[dict[str, Any]]],
    ) -> None:
        """Register a task handler.

        Args:
            capability: Capability to handle.
            handler: Async callable that processes the task.
        """
        self._dispatcher.register_handler(capability, handler)
        self._task_handlers[capability] = handler

    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of all tasks."""
        states = {}
        for task in self._tasks.values():
            state = task.get_state().value
            states[state] = states.get(state, 0) + 1

        return {
            "total_tasks": len(self._tasks),
            "by_state": states,
            "queue_size": len(self._tasks),
            "dependency_graph": self._dependency_graph.get_execution_summary(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_tasks": len(self._tasks),
            "task_handlers": list(self._task_handlers.keys()),
            "execution_summary": self.get_execution_summary(),
        }
