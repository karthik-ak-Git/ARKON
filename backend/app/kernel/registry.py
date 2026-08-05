"""ARKON Kernel - Module Registry.

Tracks all registered modules and their metadata.
The registry is the source of truth for what modules exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.kernel.exceptions import DuplicateModuleError, ModuleNotFoundError
from app.kernel.interfaces import IModule, LifecycleState


@dataclass
class ModuleInfo:
    """Metadata about a registered module."""

    module: IModule
    registered_at: float = 0.0
    initialized_at: float = 0.0
    started_at: float = 0.0
    stopped_at: float = 0.0


class ModuleRegistry:
    """Registry for all kernel modules.

    Modules register themselves with the kernel, which delegates to this registry.
    The registry tracks modules but does NOT manage their lifecycle —
    that's the LifecycleManager's job.

    Usage:
        registry = ModuleRegistry()
        registry.register(runtime_module)
        registry.register(scheduler_module)

        for module in registry.all():
            print(module.name)
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleInfo] = {}

    def register(self, module: IModule) -> None:
        """Register a module.

        Raises:
            DuplicateModuleError: If a module with the same name exists.
        """
        if module.name in self._modules:
            raise DuplicateModuleError(module.name)

        import time

        self._modules[module.name] = ModuleInfo(
            module=module,
            registered_at=time.time(),
        )

    def unregister(self, name: str) -> None:
        """Unregister a module by name."""
        if name not in self._modules:
            raise ModuleNotFoundError(name)
        del self._modules[name]

    def get(self, name: str) -> IModule:
        """Get a module by name."""
        if name not in self._modules:
            raise ModuleNotFoundError(name)
        return self._modules[name].module

    def get_optional(self, name: str) -> IModule | None:
        """Get a module by name. Returns None if not found."""
        return self._modules.get(name, None)

    def has(self, name: str) -> bool:
        """Check if a module is registered."""
        return name in self._modules

    def all(self) -> list[IModule]:
        """Return all registered modules."""
        return [info.module for info in self._modules.values()]

    def info(self, name: str) -> ModuleInfo:
        """Get detailed info about a module."""
        if name not in self._modules:
            raise ModuleNotFoundError(name)
        return self._modules[name]

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a snapshot of all modules (for debugging/health)."""
        result = {}
        for name, info in self._modules.items():
            result[name] = {
                "version": info.module.version,
                "state": info.module.state.value,
                "dependencies": info.module.dependencies(),
                "is_healthy": info.module.is_healthy,
                "registered_at": info.registered_at,
            }
        return result

    def clear(self) -> None:
        """Remove all modules. Used in testing."""
        self._modules.clear()

    def __len__(self) -> int:
        return len(self._modules)

    def __contains__(self, name: str) -> bool:
        return name in self._modules
