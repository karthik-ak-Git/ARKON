from app.api.agents import router as agents_router
from app.api.ai import router as ai_router
from app.api.execution import router as execution_router
from app.api.execution_ws import router as execution_ws_router
from app.api.health import router as health_router
from app.api.onboarding import router as onboarding_router
from app.api.projects import router as projects_router
from app.api.runtime import router as runtime_router
from app.api.runtime_ws import router as runtime_ws_router
from app.api.workspaces import router as workspaces_router

__all__ = [
    "agents_router",
    "ai_router",
    "execution_router",
    "execution_ws_router",
    "health_router",
    "onboarding_router",
    "projects_router",
    "runtime_router",
    "runtime_ws_router",
    "workspaces_router",
]
