# ARKON Backend

AI Agent Operating Platform - Backend Services

## Tech Stack

- **Python 3.13**
- **FastAPI** - Async web framework
- **SQLAlchemy 2.x** - ORM (async)
- **PostgreSQL** - Primary database
- **Redis** - Caching, queues
- **NATS** - Event bus
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **Docker** - Containerization

## Architecture

```
backend/
├── app/
│   ├── api/          # Thin HTTP controllers
│   ├── core/         # Config, logging, DI
│   ├── database/     # SQLAlchemy setup
│   ├── models/       # Domain models (ORM)
│   ├── schemas/      # Pydantic schemas
│   ├── repositories/ # Data access layer
│   ├── services/     # Business logic
│   ├── runtime/      # Agent lifecycle (Phase 3)
│   ├── scheduler/    # Job scheduling (Phase 4)
│   ├── events/       # Event bus (Phase 5)
│   ├── plugins/      # Plugin system (Phase 6)
│   ├── orchestrator/ # Workflow engine (Phase 7)
│   ├── memory/       # Knowledge store (Phase 2)
│   ├── workspace/    # Workspace management (Phase 2)
│   ├── storage/      # File storage (Phase 2)
│   ├── workers/      # Background jobs (Phase 8)
│   ├── monitoring/   # Metrics, tracing (Phase 8)
│   └── tests/        # Unit + integration tests
├── pyproject.toml    # Project config
├── Dockerfile        # Container build
└── README.md         # This file
```

## Clean Architecture

```
Controller → Service → Repository → Database
   ↑           ↑
 Schema    Business Logic
```

- **Controllers**: Parse HTTP, call services, return responses
- **Services**: Business logic, orchestration
- **Repositories**: Data access, queries
- **Models**: Database schema
- **Schemas**: API contract (request/response)

## Quick Start

```bash
# Start dependencies
docker-compose up -d postgres redis nats

# Install dependencies
cd backend
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/v1/workspaces/ | Create workspace |
| GET | /api/v1/workspaces/ | List workspaces |
| GET | /api/v1/workspaces/:id | Get workspace |
| PATCH | /api/v1/workspaces/:id | Update workspace |
| DELETE | /api/v1/workspaces/:id | Delete workspace |
| POST | /api/v1/workspaces/:id/projects/ | Create project |
| GET | /api/v1/workspaces/:id/projects/ | List projects |
| POST | /api/v1/workspaces/:id/agents/ | Create agent |
| GET | /api/v1/workspaces/:id/agents/ | List agents |

## Development

```bash
# Run tests
pytest

# Type checking
mypy app/

# Linting
ruff check app/

# Format
ruff format app/
```
