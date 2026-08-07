# Backend

Python 3.13 + FastAPI + SQLAlchemy 2.x + Pydantic v2

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
```

## Running

```bash
uvicorn app.main:app --reload --port 8000
```

## Structure

- `app/main.py` — FastAPI entry, 9 routers, lifespan manager
- `app/kernel/` — bootstraps infrastructure, manages services
- `app/api/` — REST and WebSocket endpoint definitions
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic v2 request/response schemas
- `app/repositories/` — data access layer
- `app/services/` — business logic

## Testing

```bash
pytest                    # all tests
pytest --cov=app          # with coverage
pytest tests/test_kernel.py  # specific module
```

## API Reference

See [api.md](api.md) for endpoint documentation.
