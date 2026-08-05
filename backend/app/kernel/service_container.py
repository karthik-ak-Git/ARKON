"""ARKON Kernel - Service Container.

Lightweight dependency injection container.
Supports singleton, transient, and lazy registration patterns.
No framework magic — explicit registration and resolution.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable

from app.kernel.exceptions import DuplicateServiceError, ServiceNotFoundError
from app.kernel.interfaces import IServiceContainer


@dataclass
class ServiceRegistration:
    """Internal record for a registered service."""

    service_type: type
    factory: Callable[[], Any] | None = None
    instance: Any = None
    is_singleton: bool = True
    is_lazy: bool = False
    _resolved: Any = field(default=None, repr=False)


class ServiceContainer(IServiceContainer):
    """Dependency injection container.

    Usage:
        container = ServiceContainer()
        container.register(Database, db_instance)
        container.register(Cache, cache_factory, singleton=False)

        db = container.resolve(Database)
    """

    def __init__(self) -> None:
        self._services: dict[type, ServiceRegistration] = {}

    def register(
        self,
        service_type: type,
        instance: Any,
        *,
        singleton: bool = True,
        overwrite: bool = False,
    ) -> None:
        """Register a service instance or factory.

        Args:
            service_type: The type/interface to register under.
            instance: Either an instance or a callable factory.
            singleton: If True, same instance returned each time.
            overwrite: If True, replace existing registration.

        Raises:
            DuplicateServiceError: If already registered and overwrite=False.
        """
        if service_type in self._services and not overwrite:
            raise DuplicateServiceError(service_type)

        if callable(instance) and not isinstance(instance, type):
            # It's a factory function
            self._services[service_type] = ServiceRegistration(
                service_type=service_type,
                factory=instance,
                is_singleton=singleton,
            )
        else:
            # It's an instance or class
            self._services[service_type] = ServiceRegistration(
                service_type=service_type,
                instance=instance,
                is_singleton=singleton,
            )

    def register_lazy(
        self,
        service_type: type,
        factory: Callable[[], Any],
    ) -> None:
        """Register a service that will be created on first resolution.

        Args:
            service_type: The type/interface to register under.
            factory: Callable that returns the service instance.
        """
        self._services[service_type] = ServiceRegistration(
            service_type=service_type,
            factory=factory,
            is_singleton=True,
            is_lazy=True,
        )

    def resolve(self, service_type: type) -> Any:
        """Resolve a service by type.

        Args:
            service_type: The type to resolve.

        Returns:
            The registered service instance.

        Raises:
            ServiceNotFoundError: If not registered.
        """
        if service_type not in self._services:
            raise ServiceNotFoundError(service_type)

        reg = self._services[service_type]

        # Return cached singleton
        if reg.is_singleton and reg._resolved is not None:
            return reg._resolved

        # Resolve from factory
        if reg.factory is not None:
            instance = reg.factory()
            if reg.is_singleton:
                reg._resolved = instance
            return instance

        # Return stored instance
        if reg.instance is not None:
            return reg.instance

        raise ServiceNotFoundError(service_type)

    def resolve_optional(self, service_type: type) -> Any | None:
        """Resolve a service by type. Returns None if not registered."""
        try:
            return self.resolve(service_type)
        except ServiceNotFoundError:
            return None

    def has(self, service_type: type) -> bool:
        """Check if a service is registered."""
        return service_type in self._services

    def clear(self) -> None:
        """Remove all registrations. Used in testing."""
        self._services.clear()

    def registrations(self) -> dict[str, dict[str, Any]]:
        """Return a snapshot of all registrations (for debugging)."""
        result = {}
        for service_type, reg in self._services.items():
            name = service_type.__name__
            result[name] = {
                "type": service_type,
                "is_singleton": reg.is_singleton,
                "is_lazy": reg.is_lazy,
                "has_instance": reg.instance is not None,
                "has_factory": reg.factory is not None,
                "is_resolved": reg._resolved is not None,
            }
        return result
