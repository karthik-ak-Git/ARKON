# Developer Guide

## Prerequisites

- Python 3.13+
- Node.js 20+
- Rust (for Tauri builds)
- PostgreSQL or SQLite

## Setup

```bash
git clone https://github.com/karthik-ak-Git/ARKON.git
cd ARKON

# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"

# Frontend
cd ../apps/desktop
npm install
```

## Running

```bash
# Backend (terminal 1)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd apps/desktop
npm run dev
```

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd apps/desktop && npm run lint
```

## Code Style

- **Python**: type hints, docstrings, Ruff formatting
- **TypeScript**: strict mode, ESLint
- **Rust**: cargo fmt, cargo clippy

## Project Structure

See [architecture.md](architecture.md) for the full module map.
