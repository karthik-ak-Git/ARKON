"""ARKON Execution Engine - Checkpoint System.

Supports automatic checkpoints with configurable policies.
Checkpoints store execution state, progress, intermediate results,
context, errors, and memory.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.execution.interfaces import CheckpointPolicy


@dataclass
class Checkpoint:
    """A snapshot of task execution state.

    Stores:
    - Execution State
    - Progress
    - Intermediate Results
    - Context
    - Errors
    - Memory
    """

    task_id: str = ""
    checkpoint_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)

    # Execution state
    state: str = ""
    attempt: int = 0

    # Progress
    progress: float = 0.0
    current_step: str = ""
    message: str = ""

    # Intermediate results
    results: dict[str, Any] = field(default_factory=dict)

    # Context snapshot
    context: dict[str, Any] = field(default_factory=dict)

    # Errors
    errors: list[dict[str, Any]] = field(default_factory=list)

    # Memory / agent state
    memory: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp,
            "state": self.state,
            "attempt": self.attempt,
            "progress": self.progress,
            "current_step": self.current_step,
            "message": self.message,
            "results": self.results,
            "context": self.context,
            "errors": self.errors,
            "memory": self.memory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Checkpoint:
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id", ""),
            checkpoint_id=data.get("checkpoint_id", uuid.uuid4().hex[:12]),
            timestamp=data.get("timestamp", time.time()),
            state=data.get("state", ""),
            attempt=data.get("attempt", 0),
            progress=data.get("progress", 0.0),
            current_step=data.get("current_step", ""),
            message=data.get("message", ""),
            results=data.get("results", {}),
            context=data.get("context", {}),
            errors=data.get("errors", []),
            memory=data.get("memory", {}),
        )


@dataclass
class CheckpointPolicyConfig:
    """Configuration for checkpoint behavior."""
    policy: CheckpointPolicy = CheckpointPolicy.MANUAL
    interval: float = 30.0
    max_checkpoints: int = 100

    def should_checkpoint(self, elapsed: float) -> bool:
        """Check if a checkpoint should be created based on elapsed time."""
        if self.policy == CheckpointPolicy.PERIODIC:
            return elapsed >= self.interval
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy.value,
            "interval": self.interval,
            "max_checkpoints": self.max_checkpoints,
        }


class CheckpointManager:
    """Manages checkpoint creation and retrieval.

    Supports:
    - Manual checkpoints
    - Periodic checkpoints
    - Before retry checkpoints
    - Before shutdown checkpoints
    """

    def __init__(self, policy_config: CheckpointPolicyConfig | None = None):
        """Initialize checkpoint manager."""
        self._config = policy_config or CheckpointPolicyConfig()
        self._checkpoints: dict[str, list[Checkpoint]] = {}

    def create_checkpoint(
        self,
        task_id: str,
        state: str,
        attempt: int = 0,
        progress: float = 0.0,
        current_step: str = "",
        results: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        errors: list[dict[str, Any]] | None = None,
        memory: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """Create a new checkpoint.

        Args:
            task_id: Task identifier.
            state: Current task state.
            attempt: Current attempt number.
            progress: Current progress.
            current_step: Current step name.
            results: Intermediate results.
            context: Context snapshot.
            errors: Error history.
            memory: Agent memory.

        Returns:
            The created checkpoint.
        """
        checkpoint = Checkpoint(
            task_id=task_id,
            state=state,
            attempt=attempt,
            progress=progress,
            current_step=current_step,
            results=results or {},
            context=context or {},
            errors=errors or [],
            memory=memory or {},
        )

        if task_id not in self._checkpoints:
            self._checkpoints[task_id] = []

        self._checkpoints[task_id].append(checkpoint)

        # Enforce max checkpoints
        if len(self._checkpoints[task_id]) > self._config.max_checkpoints:
            self._checkpoints[task_id] = self._checkpoints[task_id][
                -self._config.max_checkpoints:
            ]

        return checkpoint

    def get_latest(self, task_id: str) -> Checkpoint | None:
        """Get the latest checkpoint for a task."""
        checkpoints = self._checkpoints.get(task_id, [])
        if not checkpoints:
            return None
        return checkpoints[-1]

    def get_all(self, task_id: str) -> list[Checkpoint]:
        """Get all checkpoints for a task."""
        return self._checkpoints.get(task_id, []).copy()

    def get_checkpoint(
        self, task_id: str, checkpoint_id: str
    ) -> Checkpoint | None:
        """Get a specific checkpoint."""
        for cp in self._checkpoints.get(task_id, []):
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None

    def delete(self, task_id: str) -> int:
        """Delete all checkpoints for a task.

        Returns:
            Number of checkpoints deleted.
        """
        checkpoints = self._checkpoints.pop(task_id, [])
        return len(checkpoints)

    def should_checkpoint(self, elapsed: float) -> bool:
        """Check if periodic checkpoint should be created."""
        return self._config.should_checkpoint(elapsed)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": self._config.to_dict(),
            "task_count": len(self._checkpoints),
            "total_checkpoints": sum(
                len(cps) for cps in self._checkpoints.values()
            ),
        }
