"""ARKON Execution Engine - Task Dispatcher.

Routes tasks to appropriate handlers based on capability.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

import structlog

from app.execution.interfaces import ITask
from app.execution.exceptions import DispatchError

logger = structlog.get_logger(__name__)


class TaskDispatcher:
    """Dispatches tasks to appropriate handlers.

    Maintains a registry of capability → handler mappings.
    """

    def __init__(self) -> None:
        """Initialize task dispatcher."""
        self._handlers: dict[str, Callable[[ITask], Awaitable[dict[str, Any]]]] = {}
        self._dispatch_history: list[dict[str, Any]] = []

    def register_handler(
        self,
        capability: str,
        handler: Callable[[ITask], Awaitable[dict[str, Any]]],
    ) -> None:
        """Register a handler for a capability.

        Args:
            capability: Capability identifier.
            handler: Async callable that executes the task.
        """
        self._handlers[capability] = handler
        logger.debug("handler_registered", capability=capability)

    def unregister_handler(self, capability: str) -> bool:
        """Unregister a handler."""
        if capability in self._handlers:
            del self._handlers[capability]
            logger.debug("handler_unregistered", capability=capability)
            return True
        return False

    def has_handler(self, capability: str) -> bool:
        """Check if a handler exists for a capability."""
        return capability in self._handlers

    async def dispatch(self, task: ITask) -> dict[str, Any]:
        """Dispatch a task to its handler.

        Args:
            task: Task to dispatch.

        Returns:
            Result from the handler.

        Raises:
            DispatchError: If no handler or handler fails.
        """
        capability = task.get_capability()
        task_id = task.get_id()

        handler = self._handlers.get(capability)
        if handler is None:
            raise DispatchError(
                task_id=task_id,
                reason=f"No handler for capability: {capability}",
            )

        start_time = time.time()

        try:
            result = await handler(task)
            elapsed = time.time() - start_time

            record = {
                "task_id": task_id,
                "capability": capability,
                "success": True,
                "elapsed": elapsed,
                "timestamp": time.time(),
            }
            self._dispatch_history.append(record)

            logger.debug(
                "task_dispatched",
                task_id=task_id,
                capability=capability,
                elapsed=elapsed,
            )

            return result

        except Exception as e:
            elapsed = time.time() - start_time

            record = {
                "task_id": task_id,
                "capability": capability,
                "success": False,
                "error": str(e),
                "elapsed": elapsed,
                "timestamp": time.time(),
            }
            self._dispatch_history.append(record)

            raise DispatchError(
                task_id=task_id,
                reason=f"Handler failed: {e}",
            ) from e

    def get_registered_capabilities(self) -> list[str]:
        """Get all registered capabilities."""
        return list(self._handlers.keys())

    def get_history(
        self,
        task_id: str | None = None,
        capability: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get dispatch history."""
        history = self._dispatch_history

        if task_id:
            history = [h for h in history if h["task_id"] == task_id]
        if capability:
            history = [h for h in history if h["capability"] == capability]

        return history

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "registered_capabilities": list(self._handlers.keys()),
            "history_count": len(self._dispatch_history),
        }
