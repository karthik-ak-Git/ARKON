# API Reference

Base URL: `http://localhost:8000`

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Workspaces

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workspaces/` | List workspaces |
| POST | `/api/v1/workspaces/` | Create workspace |
| GET | `/api/v1/workspaces/{id}` | Get workspace |
| PUT | `/api/v1/workspaces/{id}` | Update workspace |
| DELETE | `/api/v1/workspaces/{id}` | Delete workspace |

## Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/` | List projects |
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/{id}` | Get project |

## Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents/` | List agents |
| POST | `/api/v1/agents/` | Create agent |
| GET | `/api/v1/agents/{id}` | Get agent |

## AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/providers` | Register AI provider |
| POST | `/ai/complete` | Generate completion |

## Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/execution/submit` | Submit task |
| GET | `/api/v1/execution/{id}` | Get task status |
| POST | `/api/v1/execution/{id}/cancel` | Cancel task |
| GET | `/api/v1/execution/summary` | Execution summary |

## WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/execution/{task_id}` | Real-time task updates |
| `/ws/runtime/agents` | Agent heartbeat stream |
