"""ARKON Kernel - Core.

The Kernel is the operating core of ARKON.

Every subsystem communicates through the Kernel.
Nothing bypasses it.

Think of it like:
- Linux Kernel
- Windows NT Kernel
- Docker Engine
- Kubernetes Control Plane

The Kernel owns:
- Runtime
- Scheduler
- Event Bus
- Memory
- Plugin Loader
- Storage
- Monitoring
- Model Router
- Workflow Engine

The Kernel contains NO business logic.
No Workspace logic.
No Video logic.
No AI logic.
No Workflow logic.
Only platform infrastructure.
"""

from __future__ import annotations

import enum
from typing import Any

import structlog

from app.kernel.context import Context, create_context, update_context
from app.kernel.exceptions import KernelError
from app.kernel.interfaces import IContext, IModule, LifecycleState
from app.kernel.lifecycle import LifecycleManager
from app.kernel.registry import ModuleRegistry
from app.kernel.service_container import ServiceContainer

logger = structlog.get_logger(__name__)


class KernelState(enum.Enum):
    """Possible states for the Kernel itself."""

    CREATED = "created"
    BOOTSTRAPPING = "bootstrapping"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


class Kernel:
    """The ARKON Kernel.

    Central hub for all platform infrastructure.
    Manages modules, services, and lifecycle.

    Usage:
        kernel = Kernel()
        await kernel.bootstrap(config)
        # Application runs...
        await kernel.shutdown()

    Architecture:
        ┌─────────────────────────────────────────────┐
        │                    KERNEL                    │
        ├──────────────┬──────────────┬───────────────┤
        │   Service    │    Module    │   Lifecycle   │
        │  Container   │   Registry   │   Manager     │
        ├──────────────┴──────────────┴───────────────┤
        │              Application Context            │
        ├─────────────────────────────────────────────┤
        │  Runtime │ Scheduler │ EventBus │ Plugins   │
        │  Storage │ Memory    │ Monitor  │ Workflow  │
        └─────────────────────────────────────────────┘
    """

    def __init__(self) -> None:
        self._state = KernelState.CREATED
        self._context: IContext | None = None

        # Core components
        self._services = ServiceContainer()
        self._registry = ModuleRegistry()
        self._lifecycle = LifecycleManager(self._registry)

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> KernelState:
        return self._state

    @property
    def context(self) -> IContext:
        if self._context is None:
            raise KernelError("Kernel not bootstrapped. Call bootstrap() first.")
        return self._context

    @property
    def services(self) -> ServiceContainer:
        return self._services

    @property
    def registry(self) -> ModuleRegistry:
        return self._registry

    # =========================================================================
    # Module Registration
    # =========================================================================

    def register(self, module: IModule) -> None:
        """Register a module with the kernel.

        This does NOT initialize the module — it only tracks it.
        Initialization happens during bootstrap().

        Example:
            kernel.register(Runtime())
            kernel.register(Scheduler())
            kernel.register(EventBus())
        """
        logger.info(
            "kernel_module_registering",
            module=module.name,
            version=module.version,
            dependencies=module.dependencies(),
        )
        self._registry.register(module)

        # Also register module as a service (accessible by type)
        self._services.register(
            type(module),
            module,
            singleton=True,
            overwrite=True,
        )

    def register_service(
        self,
        service_type: type,
        instance: Any,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a service directly (not a module).

        Use this for infrastructure services like Database, Redis, etc.
        """
        self._services.register(service_type, instance, singleton=singleton)

    def resolve(self, service_type: type) -> Any:
        """Resolve a service by type.

        Shortcut for kernel.services.resolve().
        """
        return self._services.resolve(service_type)

    # =========================================================================
    # Bootstrap
    # =========================================================================

    async def bootstrap(self, config: dict[str, Any]) -> IContext:
        """Bootstrap the kernel and all registered modules.

        Order:
        1. Create context with configuration
        2. Initialize and start all modules (in dependency order)
        3. Set kernel state to RUNNING

        Returns:
            The application context, passed to all future operations.

        Raises:
            KernelError: If bootstrap fails.
        """
        self._state = KernelState.BOOTSTRAPPING
        logger.info("kernel_bootstrapping")

        try:
            # Create initial context with config
            self._context = create_context(
                config=config,
                kernel=self,
            )

            # Startup all modules (initialize + start)
            await self._lifecycle.startup(self._context)

            self._state = KernelState.RUNNING
            logger.info(
                "kernel_bootstrapped",
                module_count=len(self._registry),
            )

            return self._context

        except Exception as e:
            self._state = KernelState.STOPPED
            logger.error("kernel_bootstrap_failed", error=str(e))
            raise KernelError(f"Bootstrap failed: {e}") from e

    # =========================================================================
    # Shutdown
    # =========================================================================

    async def shutdown(self) -> None:
        """Shutdown the kernel and all modules.

        Order:
        1. Set state to SHUTTING_DOWN
        2. Stop all modules (in reverse dependency order)
        3. Set state to STOPPED

        Errors during shutdown are logged but don't prevent
        other modules from stopping.
        """
        if self._state != KernelState.RUNNING:
            return

        self._state = KernelState.SHUTTING_DOWN
        logger.info("kernel_shutting_down")

        try:
            await self._lifecycle.shutdown()
        except Exception as e:
            logger.error("kernel_shutdown_error", error=str(e))
        finally:
            self._state = KernelState.STOPPED
            logger.info("kernel_stopped")

    # =========================================================================
    # Health
    # =========================================================================

    async def health_check(self) -> dict[str, Any]:
        """Aggregate health check of all modules.

        Returns a dict with:
        - kernel: Kernel state
        - modules: Per-module health status
        - overall: 'healthy' if all modules healthy, 'degraded' otherwise
        """
        modules_health = {}
        all_healthy = True

        for module in self._registry.all():
            try:
                health = await module.health_check()
                modules_health[module.name] = {
                    "status": "healthy" if module.is_healthy else "unhealthy",
                    "details": health,
                }
                if not module.is_healthy:
                    all_healthy = False
            except Exception as e:
                modules_health[module.name] = {
                    "status": "error",
                    "details": {"error": str(e)},
                }
                all_healthy = False

        return {
            "kernel": {
                "state": self._state.value,
                "module_count": len(self._registry),
            },
            "modules": modules_health,
            "overall": "healthy" if all_healthy else "degraded",
        }

    # =========================================================================
    # Debug
    # =========================================================================

    def snapshot(self) -> dict[str, Any]:
        """Full snapshot of kernel state (for debugging)."""
        return {
            "state": self._state.value,
            "modules": self._registry.snapshot(),
            "services": self._services.registrations(),
            "lifecycle": self._lifecycle.get_state(),
        }
