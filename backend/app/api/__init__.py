from app.api.agents import router as agents_router
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.workspaces import router as workspaces_router

__all__ = [
    "agents_router",
    "health_router",
    "projects_router",
    "workspaces_router",
]
