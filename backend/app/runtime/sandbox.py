"""ARKON Runtime - Execution Sandbox.

Creates isolated execution environments for agents.
Every agent executes inside its sandbox.

Responsibilities:
- Filesystem isolation
- Temporary storage
- Environment variables
- Working directory
- Permissions
- Cleanup
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from app.runtime.exceptions import SandboxCreateError, SandboxNotFoundError

logger = structlog.get_logger(__name__)


@dataclass
class SandboxConfig:
    """Sandbox configuration."""
    base_path: str = ""
    temp_path: str = ""
    env: dict[str, str] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    max_size_mb: float = 1024.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_path": self.base_path,
            "temp_path": self.temp_path,
            "env": self.env,
            "permissions": self.permissions,
            "max_size_mb": self.max_size_mb,
        }


@dataclass
class Sandbox:
    """An active sandbox."""
    id: str
    agent_id: str
    base_path: str
    temp_path: str
    env: dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "base_path": self.base_path,
            "temp_path": self.temp_path,
            "env": self.env,
            "created_at": self.created_at,
        }


class SandboxManager:
    """Creates and manages agent sandboxes.

    Every agent executes inside its sandbox.
    """

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize sandbox manager.

        Args:
            base_path: Base path for sandboxes. Uses temp dir if None.
        """
        self._base_path = base_path or os.path.join(
            tempfile.gettempdir(), "arkon_sandboxes"
        )
        self._sandboxes: dict[str, Sandbox] = {}

    async def create(
        self,
        agent_id: str,
        config: dict[str, Any] | None = None,
    ) -> str:
        """Create a sandbox for an agent.

        Args:
            agent_id: The agent to create sandbox for.
            config: Optional sandbox configuration.

        Returns:
            Sandbox ID.

        Raises:
            SandboxCreateError: If creation fails.
        """
        sandbox_id = f"sandbox_{agent_id}_{int(time.time())}"
        sandbox_config = SandboxConfig(
            **(config or {})
        )

        try:
            # Create base path
            base = os.path.join(self._base_path, sandbox_id)
            os.makedirs(base, exist_ok=True)

            # Create temp path
            temp = os.path.join(base, "tmp")
            os.makedirs(temp, exist_ok=True)

            # Create common directories
            for d in ["input", "output", "logs", "cache"]:
                os.makedirs(os.path.join(base, d), exist_ok=True)

            sandbox = Sandbox(
                id=sandbox_id,
                agent_id=agent_id,
                base_path=base,
                temp_path=temp,
                env=sandbox_config.env,
            )

            self._sandboxes[sandbox_id] = sandbox

            logger.info(
                "sandbox_created",
                sandbox_id=sandbox_id,
                agent_id=agent_id,
                path=base,
            )

            return sandbox_id

        except Exception as e:
            raise SandboxCreateError(agent_id, str(e)) from e

    async def destroy(self, sandbox_id: str) -> None:
        """Destroy a sandbox and cleanup.

        Args:
            sandbox_id: The sandbox to destroy.

        Raises:
            SandboxNotFoundError: If sandbox not found.
        """
        if sandbox_id not in self._sandboxes:
            raise SandboxNotFoundError(sandbox_id)

        sandbox = self._sandboxes[sandbox_id]

        try:
            # Remove directory
            if os.path.exists(sandbox.base_path):
                shutil.rmtree(sandbox.base_path, ignore_errors=True)

            del self._sandboxes[sandbox_id]

            logger.info(
                "sandbox_destroyed",
                sandbox_id=sandbox_id,
                agent_id=sandbox.agent_id,
            )

        except Exception as e:
            logger.error(
                "sandbox_destroy_error",
                sandbox_id=sandbox_id,
                error=str(e),
            )
            raise

    def get_path(self, sandbox_id: str) -> str:
        """Get the sandbox filesystem path."""
        if sandbox_id not in self._sandboxes:
            raise SandboxNotFoundError(sandbox_id)
        return self._sandboxes[sandbox_id].base_path

    def get_temp_path(self, sandbox_id: str) -> str:
        """Get the temporary storage path."""
        if sandbox_id not in self._sandboxes:
            raise SandboxNotFoundError(sandbox_id)
        return self._sandboxes[sandbox_id].temp_path

    async def set_env(self, sandbox_id: str, key: str, value: str) -> None:
        """Set an environment variable."""
        if sandbox_id not in self._sandboxes:
            raise SandboxNotFoundError(sandbox_id)
        self._sandboxes[sandbox_id].env[key] = value

    async def get_env(self, sandbox_id: str, key: str) -> str | None:
        """Get an environment variable."""
        if sandbox_id not in self._sandboxes:
            raise SandboxNotFoundError(sandbox_id)
        return self._sandboxes[sandbox_id].env.get(key)

    async def list_active(self) -> list[str]:
        """List active sandbox IDs."""
        return list(self._sandboxes.keys())

    def get_sandbox(self, sandbox_id: str) -> Sandbox | None:
        """Get sandbox by ID."""
        return self._sandboxes.get(sandbox_id)

    async def cleanup_expired(self, max_age: float = 3600.0) -> list[str]:
        """Cleanup sandboxes older than max_age seconds."""
        now = time.time()
        expired = []
        for sid, sandbox in list(self._sandboxes.items()):
            if now - sandbox.created_at > max_age:
                expired.append(sid)
                await self.destroy(sid)
        return expired

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_path": self._base_path,
            "active_count": len(self._sandboxes),
            "sandboxes": {
                sid: sb.to_dict()
                for sid, sb in self._sandboxes.items()
            },
        }
