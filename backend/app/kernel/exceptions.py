"""ARKON Kernel - Exceptions.

Domain-specific exceptions for kernel operations.
All kernel errors derive from KernelError for clean catching.
"""

from __future__ import annotations


class KernelError(Exception):
    """Base exception for all kernel errors."""
    pass


# =============================================================================
# Service Container Errors
# =============================================================================

class ServiceNotFoundError(KernelError):
    """Raised when resolving a service that was not registered."""

    def __init__(self, service_type: type) -> None:
        self.service_type = service_type
        super().__init__(
            f"Service not registered: {service_type.__name__}. "
            f"Did you forget to call kernel.register()?"
        )


class DuplicateServiceError(KernelError):
    """Raised when registering a service that already exists."""

    def __init__(self, service_type: type) -> None:
        self.service_type = service_type
        super().__init__(
            f"Service already registered: {service_type.__name__}. "
            f"Use overwrite=True to replace."
        )


# =============================================================================
# Module Errors
# =============================================================================

class ModuleNotFoundError(KernelError):
    """Raised when a required module is not found."""

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        super().__init__(f"Module not found: {module_name}")


class DuplicateModuleError(KernelError):
    """Raised when registering a module with a duplicate name."""

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        super().__init__(f"Module already registered: {module_name}")


class CircularDependencyError(KernelError):
    """Raised when module dependencies form a cycle."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")


class DependencyNotSatisfiedError(KernelError):
    """Raised when a module's dependencies are not available."""

    def __init__(self, module_name: str, missing: list[str]) -> None:
        self.module_name = module_name
        self.missing = missing
        super().__init__(
            f"Module '{module_name}' requires: {', '.join(missing)}"
        )


# =============================================================================
# Lifecycle Errors
# =============================================================================

class LifecycleError(KernelError):
    """Raised during lifecycle transitions."""

    def __init__(self, module_name: str, message: str) -> None:
        self.module_name = module_name
        super().__init__(f"Lifecycle error for '{module_name}': {message}")


class StartupError(KernelError):
    """Raised when kernel startup fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(f"Startup failed: {message}")


class ShutdownError(KernelError):
    """Raised when kernel shutdown fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(f"Shutdown failed: {message}")


# =============================================================================
# Context Errors
# =============================================================================

class ContextNotInitializedError(KernelError):
    """Raised when accessing context before initialization."""

    def __init__(self) -> None:
        super().__init__(
            "Application context not initialized. "
            "Call bootstrap() first."
        )


class ConfigurationError(KernelError):
    """Raised for configuration problems."""

    def __init__(self, key: str, message: str) -> None:
        self.key = key
        super().__init__(f"Configuration error for '{key}': {message}")
