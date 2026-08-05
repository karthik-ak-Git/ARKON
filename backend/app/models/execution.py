"""ARKON Execution Engine - Database Models.

SQLAlchemy models for task execution persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    Enum as SAEnum,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionTask(Base):
    """Persisted task record."""

    __tablename__ = "execution_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    task_type = Column(String(255), nullable=False, index=True)
    state = Column(
        SAEnum("pending", "queued", "dispatched", "running", "paused",
               "completed", "failed", "cancelled", "timed_out",
               "retrying", "recovered", name="task_state_enum"),
        nullable=False,
        default="pending",
    )
    priority = Column(Float, nullable=False, default=0.0)
    payload = Column(JSON, nullable=True, default=dict)
    retry_count = Column(String(50), nullable=False, default="0")
    max_retries = Column(String(50), nullable=True, default="3")
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    dependencies = relationship(
        "ExecutionDependency",
        back_populates="task",
        foreign_keys="ExecutionDependency.task_id",
    )
    dependents = relationship(
        "ExecutionDependency",
        back_populates="dependency",
        foreign_keys="ExecutionDependency.dependency_id",
    )
    checkpoints = relationship(
        "ExecutionCheckpoint",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_execution_tasks_state_priority", "state", "priority"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "task_id": self.task_id,
            "task_type": self.task_type,
            "state": self.state,
            "priority": self.priority,
            "payload": self.payload,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ExecutionDependency(Base):
    """Task dependency relationship."""

    __tablename__ = "execution_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), ForeignKey("execution_tasks.task_id"), nullable=False)
    dependency_id = Column(String(255), ForeignKey("execution_tasks.task_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    task = relationship("ExecutionTask", back_populates="dependencies", foreign_keys=[task_id])
    dependency = relationship("ExecutionTask", back_populates="dependents", foreign_keys=[dependency_id])

    __table_args__ = (
        Index("ix_execution_dependencies_task_dep", "task_id", "dependency_id", unique=True),
    )


class ExecutionCheckpoint(Base):
    """Task execution checkpoint."""

    __tablename__ = "execution_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), ForeignKey("execution_tasks.task_id"), nullable=False)
    checkpoint_id = Column(String(255), unique=True, nullable=False)
    state = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    task = relationship("ExecutionTask", back_populates="checkpoints")

    __table_args__ = (
        Index("ix_execution_checkpoints_task", "task_id"),
    )


class ExecutionResult(Base):
    """Task execution result."""

    __tablename__ = "execution_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), ForeignKey("execution_tasks.task_id"), nullable=False, unique=True)
    success = Column(Boolean, nullable=False, default=True)
    output = Column(JSON, nullable=True)
    artifacts = Column(JSON, nullable=False, default=list)
    logs = Column(JSON, nullable=False, default=list)
    metrics = Column(JSON, nullable=False, default=dict)
    duration = Column(Float, nullable=False, default=0.0)
    errors = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_execution_results_task", "task_id"),
    )
