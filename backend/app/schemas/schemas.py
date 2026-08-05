"""Pydantic schemas for API request/response.

Thin schemas. No business logic. Validation only.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Base
# =============================================================================


class SchemaBase(BaseModel):
    """Base schema with common config."""

    model_config = {"from_attributes": True}


# =============================================================================
# Workspace
# =============================================================================


class WorkspaceCreate(SchemaBase):
    """Schema for creating a workspace."""

    id: str = Field(..., min_length=1, max_length=255, description="Workspace ID")
    name: str = Field(..., min_length=1, max_length=255, description="Workspace name")
    description: str | None = Field(None, description="Workspace description")
    path: str | None = Field(None, description="Filesystem path for projects")
    tags: list[str] | None = Field(None, description="Workspace tags")


class WorkspaceUpdate(SchemaBase):
    """Schema for updating workspace."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = None


class WorkspaceRead(SchemaBase):
    """Schema for reading workspace."""

    id: str
    name: str
    description: str | None
    state: str
    path: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime


class WorkspaceOpen(SchemaBase):
    """Schema for opening a workspace."""

    workspace_id: str


class WorkspaceSnapshotCreate(SchemaBase):
    """Schema for creating a snapshot."""

    name: str | None = Field(None, description="Snapshot name")


class WorkspaceSnapshotRead(SchemaBase):
    """Schema for reading a snapshot."""

    id: str
    name: str
    workspace_id: str
    created_at: float
    status: str


class WorkspaceList(SchemaBase):
    """Schema for listing workspaces."""

    active: list[WorkspaceRead]
    available: list[WorkspaceRead]


# =============================================================================
# Project
# =============================================================================


class ProjectCreate(SchemaBase):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(SchemaBase):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None


class ProjectRead(SchemaBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Workflow
# =============================================================================


class WorkflowCreate(SchemaBase):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class WorkflowUpdate(SchemaBase):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    nodes: list | None = None
    edges: list | None = None


class WorkflowRead(SchemaBase):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    status: str
    nodes: list | None
    edges: list | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Agent
# =============================================================================


class AgentCreate(SchemaBase):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = "generic"
    capabilities: list | None = None
    config: dict | None = None


class AgentUpdate(SchemaBase):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = None
    capabilities: list | None = None
    config: dict | None = None


class AgentRead(SchemaBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    agent_type: str
    status: str
    capabilities: list | None
    config: dict | None
    last_heartbeat: datetime | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Job
# =============================================================================


class JobCreate(SchemaBase):
    name: str = Field(..., min_length=1, max_length=255)
    workflow_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    priority: int = 0
    input_data: dict | None = None


class JobUpdate(SchemaBase):
    status: str | None = None
    agent_id: uuid.UUID | None = None
    output_data: dict | None = None
    error_message: str | None = None


class JobRead(SchemaBase):
    id: uuid.UUID
    workflow_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    name: str
    status: str
    priority: int
    input_data: dict | None
    output_data: dict | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Plugin
# =============================================================================


class PluginCreate(SchemaBase):
    name: str = Field(..., min_length=1, max_length=255)
    version: str
    description: str | None = None
    author: str | None = None
    capabilities: list | None = None
    config: dict | None = None


class PluginUpdate(SchemaBase):
    version: str | None = None
    status: str | None = None
    config: dict | None = None


class PluginRead(SchemaBase):
    id: uuid.UUID
    name: str
    version: str
    description: str | None
    author: str | None
    status: str
    capabilities: list | None
    config: dict | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Event
# =============================================================================


class EventCreate(SchemaBase):
    event_type: str
    source: str
    data: dict | None = None
    workspace_id: uuid.UUID | None = None


class EventRead(SchemaBase):
    id: uuid.UUID
    event_type: str
    source: str
    data: dict | None
    workspace_id: uuid.UUID | None
    created_at: datetime


# =============================================================================
# Memory
# =============================================================================


class MemoryCreate(SchemaBase):
    key: str
    content: str
    memory_type: str = "global"
    workspace_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    metadata_: dict | None = Field(None, alias="metadata")


class MemoryRead(SchemaBase):
    id: uuid.UUID
    key: str
    content: str
    memory_type: str
    workspace_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    metadata_: dict | None
    created_at: datetime


# =============================================================================
# Health
# =============================================================================


class HealthRead(SchemaBase):
    status: str
    version: str
    environment: str
    database: str
    redis: str
