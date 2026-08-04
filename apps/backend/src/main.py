from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from config.logging import setup_logging
from db.database import engine, Base
from events.event_bus import EventBus
from monitoring.metrics import MetricsMiddleware

setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await engine.begin()
    await engine.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="ARKON Backend",
    description="AI Agent Operating Platform Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.add_middleware(MetricsMiddleware)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root() -> dict:
    return {"name": "ARKON", "version": "0.1.0", "status": "running"}