# Architecture

ARKON is a multi-layered platform with a clear separation between the desktop shell, API layer, and core runtime.

## Layers

### Desktop Shell (Tauri + React)
- **Rust process** — window management, system tray, backend lifecycle
- **React frontend** — UI views, API client, state management
- **IPC bridge** — type-safe invoke between frontend and Rust

### API Layer (FastAPI)
- 59 REST endpoints across 9 routers
- 2 WebSocket endpoints (execution, runtime)
- Pydantic v2 request/response validation
- CORS for localhost dev servers

### Core Runtime (Python)
- **Kernel** — bootstraps all infrastructure, manages service lifecycle
- **Service Container** — dependency injection and service registry
- **Repository Pattern** — clean data access layer over SQLAlchemy 2.x

### Infrastructure
- **PostgreSQL / SQLite** — persistent storage
- **Redis** — caching and pub/sub
- **NATS** — message broker (optional)

## Module Map

```
backend/app/
├── kernel/          Bootstrap, service container, registry
├── runtime/         Agent lifecycle, state machine, heartbeat
├── execution/       Task dispatch, dependency graph, retry
├── scheduler/       Priority queue, fairness, preemption
├── capabilities/    Matching, ranking, resolution
├── resources/       CPU, memory, disk, GPU monitoring
├── workflow/        DAG compiler, parser, runtime
├── events/          Pub-sub, dead-letter, replay
├── plugins/         Sandboxed execution, marketplace
├── ai/              Gateway + 7 provider adapters
├── workspace/       Isolated sessions, snapshots
├── api/             REST and WebSocket routers
├── models/          SQLAlchemy domain models
├── schemas/         Pydantic v2 schemas
├── repositories/    Data access layer
└── services/        Business logic
```

## Data Flow

1. User submits task via UI or API
2. API validates request with Pydantic
3. Scheduler assigns priority and queue position
4. Execution engine resolves dependencies
5. Runtime dispatches to appropriate agent
6. Agent interacts with AI gateway or plugins
7. Results flow back through event bus
8. WebSocket pushes updates to frontend
