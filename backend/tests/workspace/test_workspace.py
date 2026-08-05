"""Unit tests for ARKON Workspace Runtime.

Tests the workspace runtime components:
- Workspace model
- Session management
- Storage
- Snapshot system
- Serializer
- Loader
- Events
- Workspace Manager
"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.workspace import (
    SessionManager,
    SnapshotManager,
    Workspace,
    WorkspaceConfig,
    WorkspaceLoader,
    WorkspaceManager,
    WorkspaceMemory,
    WorkspaceSerializer,
    WorkspaceStorage,
)
from app.workspace.events import (
    WorkspaceCreated,
    WorkspaceOpened,
    WorkspaceSnapshotCreated,
)
from app.workspace.exceptions import (
    SchemaVersionError,
    SnapshotNotFoundError,
    WorkspaceAlreadyOpenError,
    WorkspaceCreateError,
    WorkspaceDeleteError,
    WorkspaceNotOpenError,
    WorkspaceNotFoundError,
    WorkspaceOpenError,
)
from app.workspace.session import SessionData


# =============================================================================
# Workspace Model Tests
# =============================================================================


class TestWorkspace:
    """Tests for the Workspace model."""

    def test_create_workspace(self):
        """Test creating a workspace."""
        ws = Workspace(_id="test-123", _name="Test Workspace")

        assert ws.id == "test-123"
        assert ws.name == "Test Workspace"

    def test_workspace_to_dict(self):
        """Test workspace serialization to dict."""
        ws = Workspace(_id="test-123", _name="Test Workspace")
        data = ws.to_dict()

        assert data["id"] == "test-123"
        assert data["name"] == "Test Workspace"

    def test_workspace_from_dict(self):
        """Test workspace deserialization from dict."""
        data = {
            "id": "test-123",
            "name": "Test Workspace",
            "created_at": time.time(),
            "state": "created",
            "config": {"name": "Test"},
            "memory": {},
        }

        ws = Workspace.from_dict(data)

        assert ws.id == "test-123"
        assert ws.name == "Test Workspace"


# =============================================================================
# Session Tests
# =============================================================================


class TestSessionData:
    """Tests for SessionData."""

    def test_create_session(self):
        """Test creating session data."""
        session = SessionData()

        assert session.opened_projects == []
        assert session.running_agents == []

    def test_to_dict(self):
        """Test session serialization."""
        session = SessionData(opened_projects=["proj-1"])

        data = session.to_dict()

        assert "proj-1" in data["opened_projects"]

    def test_from_dict(self):
        """Test session deserialization."""
        data = {
            "opened_projects": ["proj-1"],
            "running_agents": [],
        }

        session = SessionData.from_dict(data)

        assert "proj-1" in session.opened_projects


# =============================================================================
# Storage Tests
# =============================================================================


class TestWorkspaceStorage:
    """Tests for WorkspaceStorage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a test storage instance."""
        return WorkspaceStorage("test-ws", str(tmp_path))

    @pytest.mark.asyncio
    async def test_initialize(self, storage):
        """Test storage initialization."""
        await storage.initialize()

        assert storage.root.exists()
        assert (storage.root / "workspace.json").exists()

    @pytest.mark.asyncio
    async def test_read_write(self, storage):
        """Test read and write operations."""
        await storage.initialize()

        await storage.write("test.txt", b"hello world")
        data = await storage.read("test.txt")

        assert data == b"hello world"

    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """Test path existence check."""
        await storage.initialize()

        await storage.write("test.txt", b"data")

        assert await storage.exists("test.txt")
        assert not await storage.exists("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        """Test file deletion."""
        await storage.initialize()

        await storage.write("test.txt", b"data")
        await storage.delete("test.txt")

        assert not await storage.exists("test.txt")

    @pytest.mark.asyncio
    async def test_list(self, storage):
        """Test directory listing."""
        await storage.initialize()

        await storage.write("file1.txt", b"data1")
        await storage.write("file2.txt", b"data2")

        files = await storage.list()

        assert "file1.txt" in files
        assert "file2.txt" in files

    @pytest.mark.asyncio
    async def test_copy(self, storage):
        """Test file copy."""
        await storage.initialize()

        await storage.write("source.txt", b"data")
        await storage.copy("source.txt", "dest.txt")

        assert await storage.exists("dest.txt")
        assert await storage.read("dest.txt") == b"data"

    @pytest.mark.asyncio
    async def test_move(self, storage):
        """Test file move."""
        await storage.initialize()

        await storage.write("source.txt", b"data")
        await storage.move("source.txt", "dest.txt")

        assert not await storage.exists("source.txt")
        assert await storage.exists("dest.txt")

    @pytest.mark.asyncio
    async def test_get_size(self, storage):
        """Test getting storage size."""
        await storage.initialize()

        await storage.write("test.txt", b"hello")

        size = await storage.get_size()

        assert size > 0


# =============================================================================
# Snapshot Tests
# =============================================================================


class TestSnapshotManager:
    """Tests for SnapshotManager."""

    @pytest.fixture
    def snapshot_mgr(self, tmp_path):
        """Create a test snapshot manager."""
        storage = WorkspaceStorage("test-ws", str(tmp_path))
        return SnapshotManager(storage, "test-ws")

    @pytest.mark.asyncio
    async def test_create_snapshot(self, snapshot_mgr, tmp_path):
        """Test creating a snapshot."""
        # Initialize storage
        storage = WorkspaceStorage("test-ws", str(tmp_path))
        await storage.initialize()

        snapshot_id = await snapshot_mgr.create("test-snapshot")

        assert snapshot_id is not None
        assert len(snapshot_id) == 8

    @pytest.mark.asyncio
    async def test_list_snapshots(self, snapshot_mgr, tmp_path):
        """Test listing snapshots."""
        storage = WorkspaceStorage("test-ws", str(tmp_path))
        await storage.initialize()

        await snapshot_mgr.create("snap-1")
        await snapshot_mgr.create("snap-2")

        snapshots = await snapshot_mgr.list()

        assert len(snapshots) == 2

    @pytest.mark.asyncio
    async def test_delete_snapshot(self, snapshot_mgr, tmp_path):
        """Test deleting a snapshot."""
        storage = WorkspaceStorage("test-ws", str(tmp_path))
        await storage.initialize()

        snapshot_id = await snapshot_mgr.create("to-delete")
        await snapshot_mgr.delete(snapshot_id)

        snapshots = await snapshot_mgr.list()
        assert len(snapshots) == 0

    @pytest.mark.asyncio
    async def test_get_snapshot(self, snapshot_mgr, tmp_path):
        """Test getting snapshot metadata."""
        storage = WorkspaceStorage("test-ws", str(tmp_path))
        await storage.initialize()

        snapshot_id = await snapshot_mgr.create("my-snap")
        metadata = await snapshot_mgr.get(snapshot_id)

        assert metadata is not None
        assert metadata["name"] == "my-snap"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_snapshot(self, snapshot_mgr):
        """Test deleting nonexistent snapshot raises error."""
        with pytest.raises(SnapshotNotFoundError):
            await snapshot_mgr.delete("nonexistent")


# =============================================================================
# Serializer Tests
# =============================================================================


class TestWorkspaceSerializer:
    """Tests for WorkspaceSerializer."""

    def test_serialize(self):
        """Test workspace serialization."""
        serializer = WorkspaceSerializer()
        ws = Workspace(_id="test-123", _name="Test")

        data = serializer.serialize(ws)

        assert "schema_version" in data
        assert "workspace" in data
        assert data["workspace"]["id"] == "test-123"

    def test_deserialize(self):
        """Test workspace deserialization."""
        serializer = WorkspaceSerializer()
        data = {
            "schema_version": "1.0.0",
            "workspace": {"id": "test-123", "name": "Test"},
        }

        result = serializer.deserialize(data)

        assert result["id"] == "test-123"

    def test_schema_version_check(self):
        """Test schema version compatibility."""
        serializer = WorkspaceSerializer()

        # Compatible version
        assert serializer._is_compatible("1.0.0") is True
        assert serializer._is_compatible("1.5.0") is True

        # Incompatible version
        assert serializer._is_compatible("2.0.0") is False
        assert serializer._is_compatible("0.9.0") is False

    def test_export_import(self, tmp_path):
        """Test export and import."""
        serializer = WorkspaceSerializer()
        ws = Workspace(_id="test-123", _name="Test")

        export_path = str(tmp_path / "export.json")
        serializer.export(ws, export_path)

        imported = serializer.import_workspace(export_path)

        assert imported["id"] == "test-123"


# =============================================================================
# Loader Tests
# =============================================================================


class TestWorkspaceLoader:
    """Tests for WorkspaceLoader."""

    @pytest.fixture
    def loader(self, tmp_path):
        """Create a test loader."""
        return WorkspaceLoader(str(tmp_path))

    @pytest.mark.asyncio
    async def test_load_from_disk(self, loader, tmp_path):
        """Test loading workspace from disk."""
        # Create workspace on disk
        ws_dir = tmp_path / "workspaces" / "test-ws"
        ws_dir.mkdir(parents=True)

        ws_data = {
            "id": "test-ws",
            "name": "Test Workspace",
            "created_at": time.time(),
            "state": "created",
            "config": {"name": "Test"},
            "memory": {},
        }
        (ws_dir / "workspace.json").write_text(json.dumps(ws_data))

        workspace = await loader.load_from_disk("test-ws")

        assert workspace.id == "test-ws"
        assert workspace.name == "Test Workspace"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, loader):
        """Test loading nonexistent workspace raises error."""
        with pytest.raises(WorkspaceNotFoundError):
            await loader.load_from_disk("nonexistent")

    @pytest.mark.asyncio
    async def test_exists(self, loader, tmp_path):
        """Test checking workspace existence."""
        # Create workspace
        ws_dir = tmp_path / "workspaces" / "test-ws"
        ws_dir.mkdir(parents=True)
        (ws_dir / "workspace.json").write_text("{}")

        assert await loader.exists("test-ws")
        assert not await loader.exists("nonexistent")

    @pytest.mark.asyncio
    async def test_validate(self, loader, tmp_path):
        """Test workspace validation."""
        # Create valid workspace
        ws_dir = tmp_path / "workspaces" / "test-ws"
        ws_dir.mkdir(parents=True)
        (ws_dir / "config").mkdir()
        (ws_dir / "memory").mkdir()
        (ws_dir / "projects").mkdir()

        ws_data = {
            "id": "test-ws",
            "name": "Test",
            "created_at": time.time(),
            "state": "created",
        }
        (ws_dir / "workspace.json").write_text(json.dumps(ws_data))

        issues = await loader.validate("test-ws")

        assert issues == []


# =============================================================================
# Events Tests
# =============================================================================


class TestWorkspaceEvents:
    """Tests for workspace events."""

    def test_workspace_created_event(self):
        """Test WorkspaceCreated event."""
        event = WorkspaceCreated(
            workspace_id="test-123",
            name="Test Workspace",
        )

        assert event.workspace_id == "test-123"
        assert event.name == "Test Workspace"
        assert event.timestamp > 0

    def test_workspace_opened_event(self):
        """Test WorkspaceOpened event."""
        event = WorkspaceOpened(workspace_id="test-123")

        assert event.workspace_id == "test-123"

    def test_snapshot_created_event(self):
        """Test WorkspaceSnapshotCreated event."""
        event = WorkspaceSnapshotCreated(
            workspace_id="test-123",
            snapshot_id="snap-abc",
        )

        assert event.snapshot_id == "snap-abc"


# =============================================================================
# Workspace Manager Tests
# =============================================================================


class TestWorkspaceManager:
    """Tests for WorkspaceManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a test workspace manager."""
        return WorkspaceManager(base_path=str(tmp_path))

    @pytest.mark.asyncio
    async def test_create_workspace(self, manager):
        """Test creating a workspace."""
        ws = await manager.create("test-123", "Test Workspace")

        assert ws.id == "test-123"
        assert ws.name == "Test Workspace"
        assert "test-123" in manager.list_active()

    @pytest.mark.asyncio
    async def test_create_duplicate_workspace(self, manager):
        """Test creating duplicate workspace raises error."""
        await manager.create("test-123", "Test")

        with pytest.raises(WorkspaceAlreadyOpenError):
            await manager.create("test-123", "Test 2")

    @pytest.mark.asyncio
    async def test_open_workspace(self, manager):
        """Test opening a workspace."""
        await manager.create("test-123", "Test")
        await manager.close("test-123")

        ws = await manager.open("test-123")

        assert ws.id == "test-123"
        assert "test-123" in manager.list_active()

    @pytest.mark.asyncio
    async def test_open_nonexistent_workspace(self, manager):
        """Test opening nonexistent workspace raises error."""
        with pytest.raises(WorkspaceOpenError):
            await manager.open("nonexistent")

    @pytest.mark.asyncio
    async def test_close_workspace(self, manager):
        """Test closing a workspace."""
        await manager.create("test-123", "Test")
        await manager.close("test-123")

        assert "test-123" not in manager.list_active()

    @pytest.mark.asyncio
    async def test_close_nonexistent_workspace(self, manager):
        """Test closing nonexistent workspace raises error."""
        with pytest.raises(WorkspaceNotOpenError):
            await manager.close("nonexistent")

    @pytest.mark.asyncio
    async def test_delete_workspace(self, manager):
        """Test deleting a workspace."""
        await manager.create("test-123", "Test")
        await manager.delete("test-123")

        assert "test-123" not in manager.list_active()

    @pytest.mark.asyncio
    async def test_suspend_resume(self, manager):
        """Test suspend and resume."""
        await manager.create("test-123", "Test")
        await manager.open("test-123")

        await manager.suspend("test-123", "testing")
        ws = manager.get("test-123")
        assert ws.get_runtime_state()["state"] == "suspended"

        await manager.resume("test-123")
        ws = manager.get("test-123")
        assert ws.get_runtime_state()["state"] == "open"

    @pytest.mark.asyncio
    async def test_snapshot(self, manager):
        """Test creating a snapshot."""
        await manager.create("test-123", "Test")
        await manager.open("test-123")

        snapshot_id = await manager.snapshot("test-123", "test-snap")

        assert snapshot_id is not None

    @pytest.mark.asyncio
    async def test_list_active(self, manager):
        """Test listing active workspaces."""
        await manager.create("ws-1", "Workspace 1")
        await manager.create("ws-2", "Workspace 2")

        active = manager.list_active()

        assert len(active) == 2
        assert "ws-1" in active
        assert "ws-2" in active

    @pytest.mark.asyncio
    async def test_event_handler(self, tmp_path):
        """Test event handler is called."""
        events = []

        def handler(event):
            events.append(event)

        manager = WorkspaceManager(
            base_path=str(tmp_path),
            event_handler=handler,
        )

        await manager.create("test-123", "Test")

        assert len(events) == 1
        assert isinstance(events[0], WorkspaceCreated)
