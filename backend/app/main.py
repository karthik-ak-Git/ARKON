"""ARKON Backend - AI Agent Operating Platform.

FastAPI application entry point.
Uses the Kernel for bootstrapping all infrastructure.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.kernel.bootstrap import bootstrap_kernel, shutdown_kernel

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown via Kernel."""
    # Startup
    setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info(
        "starting_arkon",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Bootstrap the kernel (this initializes all infrastructure)
    kernel = await bootstrap_kernel()
    logger.info(
        "kernel_bootstrapped",
        state=kernel.state.value,
        module_count=len(kernel.registry),
    )

    # Initialize database engine
    from app.database.engine import create_engine, dispose_engine
    await create_engine()
    logger.info("database_engine_initialized")

    # Initialize workspace manager
    from app.workspace import WorkspaceManager
    from app.api.workspaces import set_manager

    workspace_manager = WorkspaceManager(base_path=settings.STORAGE_PATH)
    set_manager(workspace_manager)
    logger.info("workspace_manager_initialized")

    yield

    # Shutdown
    from app.database.engine import dispose_engine
    await dispose_engine()
    await shutdown_kernel()
    logger.info("arkon_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ARKON Backend",
        description="AI Agent Operating Platform - Backend API",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.api import (
        agents_router,
        ai_router,
        execution_router,
        execution_ws_router,
        health_router,
        onboarding_router,
        projects_router,
        runtime_router,
        runtime_ws_router,
        workspaces_router,
    )

    app.include_router(health_router)
    app.include_router(onboarding_router, prefix=settings.API_V1_PREFIX)
    app.include_router(workspaces_router, prefix=settings.API_V1_PREFIX)
    app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
    app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
    app.include_router(ai_router)
    app.include_router(execution_router)
    app.include_router(execution_ws_router)
    app.include_router(runtime_router)
    app.include_router(runtime_ws_router)

    return app


app = create_app()
