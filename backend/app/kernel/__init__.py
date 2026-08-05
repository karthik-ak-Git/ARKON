"""ARKON Kernel.

The operating core of the ARKON platform.

Usage:
    from app.kernel import Kernel, bootstrap_kernel

    # Bootstrap
    kernel = await bootstrap_kernel()

    # Shutdown
    await kernel.shutdown()
"""

from app.kernel.bootstrap import bootstrap_kernel, get_kernel, shutdown_kernel
from app.kernel.context import Context, create_context
from app.kernel.exceptions import (
    CircularDependencyError,
    ConfigurationError,
    ContextNotInitializedError,
    DependencyNotSatisfiedError,
    DuplicateModuleError,
    DuplicateServiceError,
    KernelError,
    LifecycleError,
    ModuleNotFoundError,
    ServiceNotFoundError,
    ShutdownError,
    StartupError,
)
from app.kernel.interfaces import (
    IConfigurable,
    IContext,
    IHealthCheckable,
    IInitializable,
    IModule,
    IServiceContainer,
    IStartable,
    LifecycleState,
)
from app.kernel.kernel import Kernel, KernelState
from app.kernel.lifecycle import LifecycleManager
from app.kernel.registry import ModuleRegistry
from app.kernel.service_container import ServiceContainer

__all__ = [
    # Kernel
    "Kernel",
    "KernelState",
    # Bootstrap
    "bootstrap_kernel",
    "get_kernel",
    "shutdown_kernel",
    # Context
    "Context",
    "create_context",
    # Exceptions
    "KernelError",
    "ServiceNotFoundError",
    "DuplicateServiceError",
    "ModuleNotFoundError",
    "DuplicateModuleError",
    "CircularDependencyError",
    "DependencyNotSatisfiedError",
    "LifecycleError",
    "StartupError",
    "ShutdownError",
    "ContextNotInitializedError",
    "ConfigurationError",
    # Interfaces
    "IInitializable",
    "IStartable",
    "IHealthCheckable",
    "IConfigurable",
    "IServiceContainer",
    "IModule",
    "IContext",
    "LifecycleState",
    # Components
    "ServiceContainer",
    "ModuleRegistry",
    "LifecycleManager",
]
