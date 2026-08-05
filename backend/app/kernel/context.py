"""ARKON Kernel - Application Context.

Immutable context passed to all modules during initialization.
Provides access to shared infrastructure without tight coupling.

The context is the only way modules access infrastructure.
Modules never create their own connections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.kernel.exceptions import ContextNotInitializedError
from app.kernel.interfaces import IContext


@dataclass(frozen=True)
class Context(IContext):
    """Application context containing shared infrastructure references.

    Frozen (immutable) to prevent accidental modification after bootstrap.
    All infrastructure references are injected at bootstrap time.

    Usage:
        ctx = Context(config=config, database=db, redis=redis, ...)
        # Pass to modules:
        await module.initialize(ctx)
    """

    _config: dict[str, Any] = field(default=None, repr=False)
    _database: Any = field(default=None, repr=False)
    _redis: Any = field(default=None, repr=False)
    _nats: Any = field(default=None, repr=False)
    _logger: Any = field(default=None, repr=False)
    _storage: Any = field(default=None, repr=False)
    _kernel: Any = field(default=None, repr=False)

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            raise ContextNotInitializedError()
        return self._config

    @property
    def database(self) -> Any:
        if self._database is None:
            raise ContextNotInitializedError()
        return self._database

    @property
    def redis(self) -> Any:
        return self._redis

    @property
    def nats(self) -> Any:
        return self._nats

    @property
    def logger(self) -> Any:
        return self._logger

    @property
    def storage(self) -> Any:
        return self._storage

    @property
    def kernel(self) -> Any:
        return self._kernel


def create_context(
    *,
    config: dict[str, Any],
    database: Any = None,
    redis: Any = None,
    nats: Any = None,
    logger: Any = None,
    storage: Any = None,
    kernel: Any = None,
) -> Context:
    """Factory function to create a Context.

    Allows partial construction — not all services are available at once.
    Context can be updated with additional services as they come online.
    """
    return Context(
        _config=config,
        _database=database,
        _redis=redis,
        _nats=nats,
        _logger=logger,
        _storage=storage,
        _kernel=kernel,
    )


def update_context(
    ctx: Context,
    **kwargs: Any,
) -> Context:
    """Create a new Context with updated fields.

    Since Context is frozen, we create a new one with merged values.
    """
    return Context(
        _config=kwargs.get("config", ctx._config),
        _database=kwargs.get("database", ctx._database),
        _redis=kwargs.get("redis", ctx._redis),
        _nats=kwargs.get("nats", ctx._nats),
        _logger=kwargs.get("logger", ctx._logger),
        _storage=kwargs.get("storage", ctx._storage),
        _kernel=kwargs.get("kernel", ctx._kernel),
    )
