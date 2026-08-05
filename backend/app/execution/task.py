"""ARKON Execution Engine - Task Model.

Defines the Task data structure.
Every task contains all information needed for execution.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.execution.interfaces import (
    CheckpointPolicy,
    RetryPolicy,
    TaskState,
)


@dataclass
class RetryConfig:
    """Task retry configuration."""
    policy: RetryPolicy = RetryPolicy.IMMEDIATE
    max_retries: int = 3
    delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy.value,
            "max_retries": self.max_retries,
            "delay": self.delay,
            "max_delay": self.max_delay,
            "backoff_multiplier": self.backoff_multiplier,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetryConfig:
        return cls(
            policy=RetryPolicy(data.get("policy", "immediate")),
            max_retries=data.get("max_retries", 3),
            delay=data.get("delay", 1.0),
            max_delay=data.get("max_delay", 60.0),
            backoff_multiplier=data.get("backoff_multiplier", 2.0),
        )


@dataclass
class CheckpointConfig:
    """Task checkpoint configuration."""
    policy: CheckpointPolicy = CheckpointPolicy.MANUAL
    interval: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy.value,
            "interval": self.interval,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointConfig:
        return cls(
            policy=CheckpointPolicy(data.get("policy", "manual")),
            interval=data.get("interval", 30.0),
        )


@dataclass
class Task:
    """A unit of work to be executed.

    Every task contains:
    - Task ID, Workspace ID, Agent ID
    - Capability, Payload, Priority
    - Dependencies, Timeout
    - Retry Policy, Checkpoint Policy
    - Metadata, Context
    """

    capability: str
    payload: dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    workspace_id: str = ""
    agent_id: str = ""
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    timeout: float | None = None
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    checkpoint_config: CheckpointConfig = field(default_factory=CheckpointConfig)
    metadata: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    # State
    state: TaskState = TaskState.CREATED
    created_at: float = field(default_factory=time.time)
    queued_at: float | None = None
    dispatched_at: float | None = None
    started_at: float | None = None
    completed_at: float | None = None
    failed_at: float | None = None
    cancelled_at: float | None = None
    updated_at: float = field(default_factory=time.time)

    # Execution tracking
    attempt: int = 0
    last_error: str = ""
    last_error_type: str = ""

    def get_id(self) -> str:
        return self.task_id

    def get_state(self) -> TaskState:
        return self.state

    def get_capability(self) -> str:
        return self.capability

    def get_payload(self) -> dict[str, Any]:
        return self.payload

    def get_priority(self) -> int:
        return self.priority

    def get_dependencies(self) -> list[str]:
        return self.dependencies.copy()

    def get_timeout(self) -> float | None:
        return self.timeout

    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.state in {
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        }

    def duration(self) -> float | None:
        """Calculate execution duration."""
        if self.started_at is None:
            return None
        end = self.completed_at or self.failed_at or time.time()
        return end - self.started_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "capability": self.capability,
            "payload": self.payload,
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "timeout": self.timeout,
            "retry_config": self.retry_config.to_dict(),
            "checkpoint_config": self.checkpoint_config.to_dict(),
            "metadata": self.metadata,
            "context": self.context,
            "state": self.state.value,
            "created_at": self.created_at,
            "queued_at": self.queued_at,
            "dispatched_at": self.dispatched_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "failed_at": self.failed_at,
            "cancelled_at": self.cancelled_at,
            "updated_at": self.updated_at,
            "attempt": self.attempt,
            "last_error": self.last_error,
            "last_error_type": self.last_error_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id", uuid.uuid4().hex[:16]),
            capability=data.get("capability", ""),
            payload=data.get("payload", {}),
            workspace_id=data.get("workspace_id", ""),
            agent_id=data.get("agent_id", ""),
            priority=data.get("priority", 0),
            dependencies=data.get("dependencies", []),
            timeout=data.get("timeout"),
            retry_config=RetryConfig.from_dict(data.get("retry_config", {})),
            checkpoint_config=CheckpointConfig.from_dict(
                data.get("checkpoint_config", {})
            ),
            metadata=data.get("metadata", {}),
            context=data.get("context", {}),
            state=TaskState(data.get("state", "created")),
            created_at=data.get("created_at", time.time()),
            queued_at=data.get("queued_at"),
            dispatched_at=data.get("dispatched_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            failed_at=data.get("failed_at"),
            cancelled_at=data.get("cancelled_at"),
            updated_at=data.get("updated_at", time.time()),
            attempt=data.get("attempt", 0),
            last_error=data.get("last_error", ""),
            last_error_type=data.get("last_error_type", ""),
        )
