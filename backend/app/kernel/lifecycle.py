"""ARKON Kernel - Lifecycle Manager.

Coordinates startup and shutdown order based on dependency graph.
Uses topological sort to determine correct initialization sequence.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

import structlog

from app.kernel.exceptions import (
    CircularDependencyError,
    DependencyNotSatisfiedError,
    LifecycleError,
)
from app.kernel.interfaces import IContext, IModule, LifecycleState
from app.kernel.registry import ModuleRegistry

logger = structlog.get_logger(__name__)


class LifecycleManager:
    """Manages module startup and shutdown order.

    Responsibilities:
    - Topological sort of modules by dependencies
    - Startup in dependency order (dependencies first)
    - Shutdown in reverse order (dependents first)
    - Failure handling (partial startup, rollback)

    Usage:
        lm = LifecycleManager(registry)
        await lm.startup(context)
        # ... application runs ...
        await lm.shutdown()
    """

    def __init__(self, registry: ModuleRegistry) -> None:
        self._registry = registry
        self._started: list[str] = []  # Track startup order for shutdown

    async def startup(self, context: IContext) -> None:
        """Initialize and start all modules in dependency order.

        Order:
        1. Topological sort modules by dependencies
        2. Call initialize() on each
        3. Call start() on each
        4. Track which modules started (for shutdown)

        Raises:
            CircularDependencyError: If modules form a cycle.
            DependencyNotSatisfiedError: If a required module is missing.
            LifecycleError: If a module fails to start.
        """
        sorted_modules = self._resolve_startup_order()

        logger.info(
            "lifecycle_startup",
            module_count=len(sorted_modules),
            order=[m.name for m in sorted_modules],
        )

        for module in sorted_modules:
            try:
                module._state = LifecycleState.INITIALIZING
                logger.info("module_initializing", module=module.name)

                await module.initialize(context)

                module._state = LifecycleState.INITIALIZED
                logger.info("module_initialized", module=module.name)

                module._state = LifecycleState.STARTING
                await module.start()

                module._state = LifecycleState.RUNNING
                self._started.append(module.name)

                import time as _time

                info = self._registry.info(module.name)
                info.started_at = _time.time()

                logger.info("module_started", module=module.name)

            except Exception as e:
                module._state = LifecycleState.FAILED
                logger.error(
                    "module_start_failed",
                    module=module.name,
                    error=str(e),
                )
                # Attempt cleanup of already-started modules
                await self._rollback()
                raise LifecycleError(
                    module.name, f"Failed to start: {e}"
                ) from e

    async def shutdown(self) -> None:
        """Stop all modules in reverse dependency order.

        Order is reversed from startup — dependents stop before dependencies.
        This ensures clean teardown.

        Errors during shutdown are logged but don't prevent other modules
        from stopping.
        """
        stopped = []
        for module_name in reversed(self._started):
            try:
                module = self._registry.get(module_name)
                if module.state == LifecycleState.RUNNING:
                    module._state = LifecycleState.STOPPING
                    logger.info("module_stopping", module=module_name)

                    await module.stop()

                    module._state = LifecycleState.STOPPED
                    stopped.append(module_name)

                    import time as _time

                    info = self._registry.info(module_name)
                    info.stopped_at = _time.time()

                    logger.info("module_stopped", module=module_name)

            except Exception as e:
                logger.error(
                    "module_stop_failed",
                    module=module_name,
                    error=str(e),
                )

        self._started = [
            name for name in self._started if name not in stopped
        ]

    def get_state(self) -> dict[str, LifecycleState]:
        """Return current state of all modules."""
        result = {}
        for module in self._registry.all():
            result[module.name] = module.state
        return result

    def _resolve_startup_order(self) -> list[IModule]:
        """Topological sort of modules by dependencies.

        Returns modules in startup order (dependencies first).

        Raises:
            CircularDependencyError: If dependencies form a cycle.
            DependencyNotSatisfiedError: If a required module is missing.
        """
        modules = {m.name: m for m in self._registry.all()}
        visited: set[str] = set()
        visiting: set[str] = set()
        order: list[str] = []

        def dfs(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise CircularDependencyError([name])

            visiting.add(name)

            if name in modules:
                for dep in modules[name].dependencies():
                    if dep not in modules:
                        raise DependencyNotSatisfiedError(name, [dep])
                    dfs(dep)

            visiting.remove(name)
            visited.add(name)
            order.append(name)

        for name in modules:
            dfs(name)

        return [modules[name] for name in order if name in modules]

    async def _rollback(self) -> None:
        """Stop modules that were successfully started."""
        for module_name in reversed(self._started):
            try:
                module = self._registry.get(module_name)
                if module.state == LifecycleState.RUNNING:
                    await module.stop()
                    module._state = LifecycleState.STOPPED
            except Exception:
                pass  # Best effort during rollback
        self._started.clear()
