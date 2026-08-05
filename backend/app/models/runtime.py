"""ARKON Runtime - Database Models.

Persist agent state to database.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentInstanceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Agent instance database record."""

    __tablename__ = "runtime_agent_instances"

    agent_type = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    state = Column(String(50), nullable=False, default="created", index=True)
    workspace_id = Column(String(255), nullable=True, index=True)
    sandbox_id = Column(String(255), nullable=True)

    # Config
    max_retries = Column(Integer, default=3)
    timeout = Column(Float, default=300.0)
    heartbeat_interval = Column(Float, default=30.0)
    auto_restart = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    settings = Column(JSON, default=dict)

    # Metadata
    version = Column(String(50), default="1.0.0")
    author = Column(String(255), default="")
    description = Column(Text, default="")
    capabilities = Column(JSON, default=list)
    required_resources = Column(JSON, default=dict)
    supported_models = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    tags = Column(JSON, default=list)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Status
    error = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    task_count = Column(Integer, default=0)

    # Relationships
    heartbeats = relationship("HeartbeatRecord", back_populates="agent")
    executions = relationship("ExecutionHistoryRecord", back_populates="agent")


class HeartbeatRecord(Base, UUIDPrimaryKeyMixin):
    """Heartbeat database record."""

    __tablename__ = "runtime_heartbeats"

    agent_id = Column(
        UUID(as_uuid=False),
        ForeignKey("runtime_agent_instances.id"),
        nullable=False,
        index=True,
    )
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="running")
    cpu = Column(Float, default=0.0)
    memory = Column(Float, default=0.0)
    task_progress = Column(Float, default=0.0)
    current_activity = Column(String(255), default="")
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationship
    agent = relationship("AgentInstanceRecord", back_populates="heartbeats")


class ExecutionHistoryRecord(Base, UUIDPrimaryKeyMixin):
    """Execution history database record."""

    __tablename__ = "runtime_execution_history"

    agent_id = Column(
        UUID(as_uuid=False),
        ForeignKey("runtime_agent_instances.id"),
        nullable=False,
        index=True,
    )
    task_id = Column(String(255), nullable=False)
    task_type = Column(String(255), nullable=False)
    payload = Column(JSON, default=dict)
    status = Column(String(50), default="pending")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    timeout = Column(Float, default=300.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationship
    agent = relationship("AgentInstanceRecord", back_populates="executions")


class RuntimeMetricsRecord(Base, UUIDPrimaryKeyMixin):
    """Runtime metrics database record."""

    __tablename__ = "runtime_metrics"

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_agents = Column(Integer, default=0)
    running_agents = Column(Integer, default=0)
    failed_agents = Column(Integer, default=0)
    completed_agents = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    active_sandboxes = Column(Integer, default=0)
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Float, default=0.0)
    vram_usage = Column(Float, default=0.0)
    metadata_ = Column("metadata", JSON, default=dict)
