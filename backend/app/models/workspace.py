"""Workspace database models.

SQLAlchemy models for workspace persistence.

These models store workspace metadata in PostgreSQL.
The actual workspace state is stored on disk in the workspace filesystem.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WorkspaceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Workspace record in the database.

    Stores workspace metadata for listing and searching.
    The actual workspace state is on disk.
    """

    __tablename__ = "workspace_records"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="created"
    )
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    __table_args__ = (
        Index("ix_workspace_records_state", "state"),
        Index("ix_workspace_records_name", "name"),
    )


class SnapshotRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Snapshot record in the database.

    Stores snapshot metadata for listing and management.
    The actual snapshot data is on disk.
    """

    __tablename__ = "snapshot_records"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="created"
    )
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    __table_args__ = (
        Index("ix_snapshot_records_workspace_id", "workspace_id"),
    )


class SessionRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Session record in the database.

    Stores session metadata for quick access.
    The full session state is on disk.
    """

    __tablename__ = "session_records"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    last_accessed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    __table_args__ = (
        Index("ix_session_records_workspace_id", "workspace_id"),
    )
