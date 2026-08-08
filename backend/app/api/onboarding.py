"""Onboarding REST API.

First-run experience state management.
Persists to JSON file in STORAGE_PATH.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class OnboardingData(BaseModel):
    """Data collected during onboarding."""
    workspace_name: str | None = None
    workspace_description: str | None = None
    providers_configured: list[str] = Field(default_factory=list)
    routing_policy: str = "local_first"
    thinking_profile: str = "balanced"


class OnboardingStatus(BaseModel):
    """Current onboarding state."""
    completed: bool = False
    current_step: int = 0
    data: OnboardingData = Field(default_factory=OnboardingData)


class OnboardingCompleteRequest(BaseModel):
    """Request to mark onboarding as complete."""
    data: OnboardingData | None = None


# ---------------------------------------------------------------------------
# File persistence
# ---------------------------------------------------------------------------

def _onboarding_path() -> Path:
    return Path(settings.STORAGE_PATH) / "onboarding.json"


def _load_status() -> OnboardingStatus:
    path = _onboarding_path()
    if not path.exists():
        return OnboardingStatus()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return OnboardingStatus(**raw)
    except Exception:
        return OnboardingStatus()


def _save_status(status: OnboardingStatus) -> None:
    path = _onboarding_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(status.model_dump(), indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status() -> OnboardingStatus:
    """Get the current onboarding state."""
    return _load_status()


@router.post("/complete", response_model=OnboardingStatus)
async def complete_onboarding(req: OnboardingCompleteRequest | None = None) -> OnboardingStatus:
    """Mark onboarding as complete and save any collected data."""
    status = _load_status()
    status.completed = True
    status.current_step = 7
    if req and req.data:
        status.data = req.data
    _save_status(status)
    return status


@router.put("/step/{step}")
async def update_onboarding_step(step: int, data: OnboardingData | None = None) -> OnboardingStatus:
    """Update the current onboarding step and optionally save data."""
    if step < 0 or step > 7:
        raise HTTPException(status_code=400, detail="Step must be 0-7")
    status = _load_status()
    status.current_step = step
    if data:
        status.data = data
    _save_status(status)
    return status


@router.delete("/reset")
async def reset_onboarding() -> OnboardingStatus:
    """Reset onboarding to allow re-run."""
    status = OnboardingStatus()
    _save_status(status)
    return status
