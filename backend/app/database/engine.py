"""Database engine and session management.

Async SQLAlchemy engine with connection pooling.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


async def create_engine() -> AsyncEngine:
    """Create and return the async database engine."""
    global _engine, _session_factory

    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
    )

    return _engine


async def dispose_engine() -> None:
    """Dispose of the database engine."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


def get_session_factory() -> async_sessionmaker:
    """Get the session factory."""
    if _session_factory is None:
        raise RuntimeError("Database engine not initialized. Call create_engine() first.")
    return _session_factory
