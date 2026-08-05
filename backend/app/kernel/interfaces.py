"""ARKON Kernel - Interface contracts.

Defines the contracts that all kernel components must implement.
No business logic here — only structural agreements.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import Any


# =============================================================================
# Lifecycle States
# =============================================================================

class LifecycleState(enum.Enum):
    """Possible states for a kernel module."""
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


# =============================================================================
# Core Interfaces
# =============================================================================

class IInitializable(ABC):
    """Interface for components that need initialization."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component. Called once during startup."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown. Called once during shutdown."""
        ...


class IStartable(ABC):
    """Interface for components that can be started/stopped."""

    @abstractmethod
    async def start(self) -> None:
        """Start the component."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the component."""
        ...


class IHealthCheckable(ABC):
    """Interface for components that expose health status."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Return health status. Must be fast and non-blocking."""
        ...

    @property
    @abstractmethod
    def is_healthy(self) -> bool:
        """Quick synchronous health check."""
        ...


class IConfigurable(ABC):
    """Interface for components that accept configuration."""

    @abstractmethod
    def configure(self, config: dict[str, Any]) -> None:
        """Apply configuration. Called before initialize()."""
        ...


# =============================================================================
# Service Container Interface
# =============================================================================

class IServiceContainer(ABC):
    """Interface for the dependency injection container."""

    @abstractmethod
    def register(
        self,
        service_type: type,
        instance: Any,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a service instance."""
        ...

    @abstractmethod
    def resolve(self, service_type: type) -> Any:
        """Resolve a service by type. Raises if not registered."""
        ...

    @abstractmethod
    def resolve_optional(self, service_type: type) -> Any | None:
        """Resolve a service by type. Returns None if not registered."""
        ...

    @abstractmethod
    def has(self, service_type: type) -> bool:
        """Check if a service is registered."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all registrations. Used in testing."""
        ...


# =============================================================================
# Module Registry Interface
# =============================================================================

class IModule(IInitializable, IHealthCheckable):
    """Interface for kernel modules.

    Every subsystem (Runtime, Scheduler, EventBus, etc.) must implement this.
    The kernel discovers, initializes, and manages modules through this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable module name. E.g. 'scheduler', 'event_bus'."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Module version string."""
        ...

    @property
    @abstractmethod
    def state(self) -> LifecycleState:
        """Current lifecycle state."""
        ...

    @abstractmethod
    def dependencies(self) -> list[str]:
        """List of module names this module depends on."""
        ...


# =============================================================================
# Lifecycle Manager Interface
# =============================================================================

class ILifecycleManager(ABC):
    """Interface for coordinating startup/shutdown order."""

    @abstractmethod
    def register(self, module: IModule) -> None:
        """Register a module for lifecycle management."""
        ...

    @abstractmethod
    async def startup(self) -> None:
        """Start all modules in dependency order."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Stop all modules in reverse dependency order."""
        ...

    @abstractmethod
    def get_state(self) -> dict[str, LifecycleState]:
        """Return state of all managed modules."""
        ...


# =============================================================================
# Context Interface
# =============================================================================

class IContext(ABC):
    """Interface for the application context.

    Passed to all modules during initialization.
    Provides access to shared infrastructure without tight coupling.
    """

    @property
    @abstractmethod
    def config(self) -> dict[str, Any]:
        """Application configuration."""
        ...

    @property
    @abstractmethod
    def database(self) -> Any:
        """Database session factory."""
        ...

    @property
    @abstractmethod
    def redis(self) -> Any:
        """Redis connection pool."""
        ...

    @property
    @abstractmethod
    def nats(self) -> Any:
        """NATS connection."""
        ...

    @property
    @abstractmethod
    def logger(self) -> Any:
        """Structured logger."""
        ...

    @property
    @abstractmethod
    def storage(self) -> Any:
        """Storage abstraction."""
        ...

    @property
    @abstractmethod
    def kernel(self) -> Any:
        """Reference to the kernel."""
        ...
