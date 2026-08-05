"""ARKON Runtime - Execution Context.

Provides the context for every agent execution.
Never use globals.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.runtime.interfaces import IContext


@dataclass
class ExecutionContext(IContext):
    """Execution context provided to every agent.

    Every execution receives:
    - Workspace, Kernel Context, Memory, Storage
    - Logger, Configuration, Capabilities
    - Session, Cancellation Token

    Never use globals.
    """

    workspace: Any = None
    kernel: Any = None
    memory: Any = None
    storage: Any = None
    logger: Any = None
    config: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    session: Any = None
    _cancelled: bool = False
    _created_at: float = field(default_factory=time.time)

    def get_workspace(self) -> Any:
        return self.workspace

    def get_kernel(self) -> Any:
        return self.kernel

    def get_memory(self) -> Any:
        return self.memory

    def get_storage(self) -> Any:
        return self.storage

    def get_logger(self) -> Any:
        return self.logger

    def get_config(self) -> dict[str, Any]:
        return self.config

    def get_capabilities(self) -> list[str]:
        return self.capabilities

    def get_session(self) -> Any:
        return self.session

    def is_cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace": str(self.workspace) if self.workspace else None,
            "kernel": str(self.kernel) if self.kernel else None,
            "memory": str(self.memory) if self.memory else None,
            "storage": str(self.storage) if self.storage else None,
            "config": self.config,
            "capabilities": self.capabilities,
            "session": str(self.session) if self.session else None,
            "cancelled": self._cancelled,
            "created_at": self._created_at,
        }
