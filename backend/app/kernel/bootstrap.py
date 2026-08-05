"""ARKON Kernel - Bootstrap.

Orchestrates the complete application startup sequence.

Bootstrap Order:
1. Configuration (pydantic-settings)
2. Logger (structlog)
3. Database (async SQLAlchemy)
4. Redis (async connection pool)
5. NATS (async client)
6. Kernel (create + register modules)
7. FastAPI lifespan

This is the ONLY place where infrastructure is created.
Modules receive infrastructure through the Context.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.kernel.context import Context, create_context, update_context
from app.kernel.kernel import Kernel
from app.kernel.service_container import ServiceContainer

logger = structlog.get_logger(__name__)

# Global kernel instance
_kernel: Kernel | None = None


def get_kernel() -> Kernel:
    """Get the global kernel instance."""
    if _kernel is None:
        raise RuntimeError("Kernel not initialized. Call bootstrap() first.")
    return _kernel


async def bootstrap_kernel() -> Kernel:
    """Bootstrap the ARKON kernel.

    This is the entry point for application startup.
    Called once during FastAPI lifespan initialization.

    Returns:
        The fully bootstrapped kernel.

    Raises:
        RuntimeError: If bootstrap fails.
    """
    global _kernel

    logger.info("bootstrap_started")

    # Create kernel
    _kernel = Kernel()

    # Build configuration
    config = {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL,
        "redis_url": settings.REDIS_URL,
        "nats_url": settings.NATS_URL,
        "log_level": settings.LOG_LEVEL,
        "log_format": settings.LOG_FORMAT,
    }

    # Bootstrap kernel (this initializes all registered modules)
    await _kernel.bootstrap(config)

    logger.info("bootstrap_completed")
    return _kernel


async def shutdown_kernel() -> None:
    """Shutdown the kernel and all modules.

    Called during FastAPI lifespan shutdown.
    """
    global _kernel

    if _kernel is not None:
        logger.info("shutdown_started")
        await _kernel.shutdown()
        _kernel = None
        logger.info("shutdown_completed")


@asynccontextmanager
async def kernel_lifespan() -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager.

    Usage in main.py:
        app = FastAPI(lifespan=kernel_lifespan)
    """
    # Startup
    await bootstrap_kernel()
    yield
    # Shutdown
    await shutdown_kernel()


def create_app_context() -> Context:
    """Create a Context from the current kernel state.

    Used to pass context to modules and services.
    """
    kernel = get_kernel()

    return create_context(
        config=kernel.context.config,
        kernel=kernel,
    )


def get_service(service_type: type) -> Any:
    """Convenience function to resolve a service from the kernel."""
    kernel = get_kernel()
    return kernel.resolve(service_type)
