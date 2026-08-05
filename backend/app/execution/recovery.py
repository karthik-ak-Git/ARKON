"""ARKON Execution Engine - Recovery System.

Supports resume after crash, restart, checkpoint, and rollback.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

import structlog

from app.execution.checkpoint import Checkpoint, CheckpointManager
from app.execution.exceptions import (
    CheckpointNotFoundError,
    RecoveryFailedError,
)

logger = structlog.get_logger(__name__)


class RecoveryStrategy(str, Enum):
    """Recovery strategy types."""

    RESUME = "resume"
    ROLLBACK = "rollback"
    RESTART = "restart"


class RecoveryManager:
    """Manages task recovery from checkpoints.

    Supports:
    - Resume after crash
    - Resume after restart
    - Resume after checkpoint
    - Rollback to previous state
    """

    def __init__(self, checkpoint_manager: CheckpointManager):
        """Initialize recovery manager."""
        self._checkpoints = checkpoint_manager
        self._recovery_history: list[dict[str, Any]] = []

    async def can_recover(self, task_id: str) -> bool:
        """Check if a task can be recovered."""
        checkpoint = self._checkpoints.get_latest(task_id)
        return checkpoint is not None

    async def recover(
        self,
        task_id: str,
        strategy: RecoveryStrategy = RecoveryStrategy.RESUME,
    ) -> dict[str, Any]:
        """Recover a task from its latest checkpoint.

        Args:
            task_id: Task identifier.
            strategy: Recovery strategy.

        Returns:
            Recovery result with checkpoint data.

        Raises:
            CheckpointNotFoundError: No checkpoint available.
            RecoveryFailedError: Recovery failed.
        """
        checkpoint = self._checkpoints.get_latest(task_id)
        if checkpoint is None:
            raise CheckpointNotFoundError(task_id)

        try:
            recovery_result = {
                "task_id": task_id,
                "strategy": strategy.value,
                "checkpoint_id": checkpoint.checkpoint_id,
                "checkpoint_timestamp": checkpoint.timestamp,
                "restored_state": checkpoint.state,
                "restored_progress": checkpoint.progress,
                "restored_attempt": checkpoint.attempt,
                "restored_results": checkpoint.results,
                "restored_context": checkpoint.context,
                "recovered_at": time.time(),
            }

            self._recovery_history.append(recovery_result)

            logger.info(
                "task_recovered",
                task_id=task_id,
                strategy=strategy.value,
                checkpoint_id=checkpoint.checkpoint_id,
            )

            return recovery_result

        except Exception as e:
            raise RecoveryFailedError(task_id, str(e))

    async def rollback(
        self, task_id: str, checkpoint_id: str | None = None
    ) -> dict[str, Any]:
        """Rollback to a specific checkpoint.

        Args:
            task_id: Task identifier.
            checkpoint_id: Specific checkpoint to rollback to.

        Returns:
            Rollback result.
        """
        if checkpoint_id:
            checkpoint = self._checkpoints.get_checkpoint(task_id, checkpoint_id)
        else:
            checkpoint = self._checkpoints.get_latest(task_id)

        if checkpoint is None:
            raise CheckpointNotFoundError(task_id)

        result = {
            "task_id": task_id,
            "strategy": "rollback",
            "checkpoint_id": checkpoint.checkpoint_id,
            "rolled_back_to": checkpoint.state,
            "rolled_back_progress": checkpoint.progress,
            "rolled_back_at": time.time(),
        }

        self._recovery_history.append(result)

        logger.info(
            "task_rollback",
            task_id=task_id,
            checkpoint_id=checkpoint.checkpoint_id,
        )

        return result

    def get_recovery_history(self, task_id: str | None = None) -> list[dict[str, Any]]:
        """Get recovery history, optionally filtered by task."""
        if task_id:
            return [
                r for r in self._recovery_history if r["task_id"] == task_id
            ]
        return self._recovery_history.copy()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recovery_count": len(self._recovery_history),
        }
