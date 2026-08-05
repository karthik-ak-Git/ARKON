"""Domain models.

SQLAlchemy models for all domain entities.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# =============================================================================
# Workspace
# =============================================================================


class Workspace(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Workspace - top-level container for projects and agents."""

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    agents: Mapped[list["Agent"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


# =============================================================================
# Project
# =============================================================================


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Project - scoped unit of work within a workspace."""

    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_workspace_id", "workspace_id"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="projects")
    workflows: Mapped[list["Workflow"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


# =============================================================================
# Workflow
# =============================================================================


class Workflow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Workflow - directed graph of execution steps."""

    __tablename__ = "workflows"
    __table_args__ = (Index("ix_workflows_project_id", "project_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    nodes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    edges: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="workflows")
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan"
    )


# =============================================================================
# Agent
# =============================================================================


class Agent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Agent - autonomous execution unit."""

    __tablename__ = "agents"
    __table_args__ = (Index("ix_agents_workspace_id", "workspace_id"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, default="generic")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="idle")
    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="agents")
    jobs: Mapped[list["Job"]] = relationship(back_populates="agent")


# =============================================================================
# Job
# =============================================================================


class Job(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Job - unit of work assigned to an agent."""

    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_workflow_id", "workflow_id"),
        Index("ix_jobs_agent_id", "agent_id"),
        Index("ix_jobs_status", "status"),
    )

    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    workflow: Mapped["Workflow | None"] = relationship(back_populates="jobs")
    agent: Mapped["Agent | None"] = relationship(back_populates="jobs")


# =============================================================================
# Plugin
# =============================================================================


class Plugin(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Plugin - extendable capability module."""

    __tablename__ = "plugins"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="inactive")
    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)


# =============================================================================
# Event
# =============================================================================


class Event(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Event - immutable record of something that happened."""

    __tablename__ = "events"
    __table_args__ = (Index("ix_events_event_type", "event_type"),)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True
    )


# =============================================================================
# Memory
# =============================================================================


class Memory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Memory - persistent knowledge store."""

    __tablename__ = "memories"
    __table_args__ = (
        Index("ix_memories_workspace_id", "workspace_id"),
        Index("ix_memories_agent_id", "agent_id"),
        Index("ix_memories_memory_type", "memory_type"),
    )

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    memory_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="global"
    )  # global | workspace | project | agent
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=dict)


# =============================================================================
# Artifact
# =============================================================================


class Artifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Artifact - file or output produced by a job."""

    __tablename__ = "artifacts"
    __table_args__ = (Index("ix_artifacts_job_id", "job_id"),)

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)


# =============================================================================
# Session
# =============================================================================


class Session(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Session - user interaction session."""

    __tablename__ = "sessions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)


# =============================================================================
# Checkpoint
# =============================================================================


class Checkpoint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Checkpoint - saved state for recovery."""

    __tablename__ = "checkpoints"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


# =============================================================================
# Log
# =============================================================================


class LogEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """LogEntry - structured log line."""

    __tablename__ = "log_entries"
    __table_args__ = (Index("ix_log_entries_job_id", "job_id"),)

    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)


# =============================================================================
# Model
# =============================================================================


class Model(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Model - registered LLM or AI model."""

    __tablename__ = "models"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="remote"
    )  # local | remote
    endpoint: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="available")
    rate_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
