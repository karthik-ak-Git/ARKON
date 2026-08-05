# ARKON Workspace Runtime

A workspace is a **live execution environment** (like VS Code Workspace, Docker Project), NOT a database record.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Workspace Manager                          │
│                    (ONLY creates/destroys)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Workspace   │  │   Session    │  │   Memory     │          │
│  │   (Live Env)  │  │   (Context)  │  │   (KV Store) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Storage     │  │   Snapshot   │  │   Events     │          │
│  │   (Filesystem)│  │   (Version)  │  │   (Actions)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Concepts

### Workspace
A live execution environment containing:
- **Config**: Project settings, environment variables
- **Memory**: Key-value store (global, project, agent scoped)
- **Session**: Working context (projects, agents, documents, commands)

### WorkspaceManager
The **ONLY** component allowed to create or destroy workspaces.

```python
from app.workspace import WorkspaceManager

manager = WorkspaceManager(base_path="./data")

# Create
workspace = await manager.create("my-ws", "My Workspace")

# Open
workspace = await manager.open("my-ws")

# Close
await manager.close("my-ws")

# Delete
await manager.delete("my-ws")
```

### Session
The working context:
- Projects: Active project names
- Agents: Registered agents
- Documents: Open documents
- Workflow: Current workflow state
- Commands: Command history
- Layout: UI layout preferences

### Snapshots
Point-in-time captures of workspace state:

```python
# Create snapshot
snapshot_id = await manager.snapshot("my-ws", "before-refactor")

# List snapshots
snapshots = await snapshot_mgr.list()

# Restore
await manager.restore("my-ws", snapshot_id)
```

## Directory Structure

```
workspace/
├── workspace.json     # Workspace metadata
├── config/            # Configuration files
├── memory/            # Memory persistence
├── projects/          # Project files
├── artifacts/         # Generated artifacts
├── assets/            # Static assets
├── plugins/           # Plugin state
├── jobs/              # Job data
├── logs/              # Workspace logs
├── cache/             # Temporary cache
├── exports/           # Exported files
└── .snapshots/        # Snapshot data
```

## Lifecycle

```
create → open → [active] → close → [closed]
                          ↓
                    suspend → [suspended] → resume → [active]
                          ↓
                    snapshot → [snapshot_id]
                          ↓
                    restore → [active]
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workspaces/` | Create workspace |
| POST | `/workspaces/{id}/open` | Open workspace |
| POST | `/workspaces/{id}/close` | Close workspace |
| DELETE | `/workspaces/{id}` | Delete workspace |
| POST | `/workspaces/{id}/suspend` | Suspend workspace |
| POST | `/workspaces/{id}/resume` | Resume workspace |
| POST | `/workspaces/{id}/snapshots` | Create snapshot |
| POST | `/workspaces/{id}/snapshots/{sid}/restore` | Restore snapshot |
| GET | `/workspaces/` | List all workspaces |
| GET | `/workspaces/{id}` | Get workspace |

## Events

| Event | Description |
|-------|-------------|
| `WorkspaceCreated` | Workspace created |
| `WorkspaceOpened` | Workspace opened |
| `WorkspaceClosed` | Workspace closed |
| `WorkspaceSuspended` | Workspace suspended |
| `WorkspaceResumed` | Workspace resumed |
| `WorkspaceDeleted` | Workspace deleted |
| `WorkspaceError` | Workspace error |
| `WorkspaceSnapshotCreated` | Snapshot created |
| `WorkspaceSnapshotRestored` | Snapshot restored |

## Implementation Status

| Component | Status |
|-----------|--------|
| Interfaces | ✅ Complete |
| Exceptions | ✅ Complete |
| Workspace Model | ✅ Complete |
| Session Management | ✅ Complete |
| Storage | ✅ Complete |
| Snapshot System | ✅ Complete |
| Serializer | ✅ Complete |
| Loader | ✅ Complete |
| Events | ✅ Complete |
| Workspace Manager | ✅ Complete |
| Database Models | ✅ Complete |
| API Endpoints | ✅ Complete |
| Unit Tests | ✅ Complete |

## Next Phase

**Phase 3: Agent Runtime** - Implement agent lifecycle (AgentManager as the ONLY component that creates/destroys agents).
