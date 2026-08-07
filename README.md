<div align="center">

# ARKON

**AI Agent Operating Platform**

*Run specialized AI agents, workflows, plugins, and local/cloud AI providers — all from a single desktop application.*

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/user/arkon/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Tauri 2](https://img.shields.io/badge/Tauri-2-FFC131.svg)](https://tauri.app/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-1200+-brightgreen.svg)](#testing)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](#)

</div>

---

## Introduction

ARKON is not a chatbot. It is not a video editor. It is an **operating platform** for AI agents.

ARKON provides the infrastructure to run hundreds of specialized AI agents simultaneously — each with its own capabilities, memory, and execution context. Agents can be orchestrated through workflows, connected to local or cloud AI providers, extended through plugins, and monitored in real time.

The platform is designed as a foundation. The first application built on top of ARKON is an AI-powered video editing platform, but the core is general-purpose: any domain that requires multi-agent coordination, plugin-based extensibility, and hybrid local/cloud AI integration.

**Key characteristics:**

- Multi-agent runtime with sandboxed execution
- Workflow engine with DAG-based orchestration
- Plugin system with dependency resolution and marketplace support
- AI gateway supporting 7+ providers (cloud and local)
- Real-time WebSocket updates
- Desktop application built with Tauri (Python + React)

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent Runtime** | Spawn, manage, and coordinate hundreds of AI agents concurrently |
| **Workflow Runtime** | DAG-based workflow engine with node orchestration, branching, and error recovery |
| **Execution Engine** | Task dispatch, dependency resolution, checkpoint/restart, and retry logic |
| **Capability Registry** | Dynamic capability matching, ranking, and resolution across agents |
| **Resource Manager** | CPU, memory, disk, and GPU monitoring with quotas and allocation |
| **Scheduler** | Priority-based scheduling with fairness, preemption, and backpressure |
| **Plugin Runtime** | Sandboxed plugin execution with lifecycle management and marketplace |
| **Event Bus** | Publish-subscribe messaging with dead-letter queues and replay |
| **AI Gateway** | Unified interface to OpenRouter, Gemini, Ollama, NVIDIA NIM, Copilot, and more |
| **Workspace Runtime** | Isolated workspace sessions with snapshots and state persistence |
| **WebSocket Updates** | Real-time execution status, agent heartbeats, and resource metrics |
| **Desktop Application** | Tauri-based native app with embedded Python backend |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Desktop UI (React)                       │
│                      Tauri Shell (Rust)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│                        API Layer (FastAPI)                       │
│         59 REST Endpoints · 2 WebSocket Endpoints               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                         Kernel (Core)                           │
│              Bootstrap · Service Container · Registry            │
└──┬───────────────┬──────────────┬───────────────────────────────┘
   │               │              │
   ▼               ▼              ▼
┌─────────┐ ┌───────────┐ ┌──────────────┐
│Workspace │ │  Agent    │ │  Execution   │
│ Runtime  │ │ Runtime   │ │   Engine     │
└────┬─────┘ └─────┬─────┘ └──────┬───────┘
     │             │              │
     ▼             ▼              ▼
┌─────────┐ ┌───────────┐ ┌──────────────┐
│Scheduler│ │Capability │ │  Resource    │
│         │ │ Registry  │ │  Manager     │
└────┬────┘ └─────┬─────┘ └──────┬───────┘
     │            │              │
     ▼            ▼              ▼
┌─────────┐ ┌───────────┐ ┌──────────────┐
│Event Bus│ │  Plugin   │ │  AI Gateway  │
│         │ │ Runtime   │ │              │
└─────────┘ └───────────┘ └──────────────┘
```

---

## Screenshots

> Screenshots will be added after the first stable release.

| Welcome Screen | Workspace | Execution |
|:-:|:-:|:-:|
| ![Welcome](docs/screenshots/welcome.png) | ![Workspace](docs/screenshots/workspace.png) | ![Execution](docs/screenshots/execution.png) |

| Agents | Workflow | Plugins | Settings |
|:-:|:-:|:-:|:-:|
| ![Agents](docs/screenshots/agents.png) | ![Workflow](docs/screenshots/workflow.png) | ![Plugins](docs/screenshots/plugins.png) | ![Settings](docs/screenshots/settings.png) |

---

## Downloads

| Package | Description | Link |
|---------|-------------|------|
| Windows Installer | NSIS installer, requires no additional setup | **Coming Soon** |
| Portable Version | No installation required, run from any directory | **Coming Soon** |
| Source Code | Clone and build from source | [View Releases](https://github.com/user/arkon/releases) |

> Pre-built binaries are not yet available. See [Installation](#installation) to build from source.

---

## Installation

### Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/)
- [Rust](https://rustup.rs/) (for Tauri desktop build)
- [PostgreSQL](https://www.postgresql.org/) (or SQLite for development)
- [Redis](https://redis.io/) (optional, for caching)
- [NATS](https://nats.io/) (optional, for messaging)

### Developer Installation

```bash
# Clone the repository
git clone https://github.com/user/arkon.git
cd arkon

# Install backend dependencies
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -e ".[dev]"

# Start the backend
uvicorn app.main:app --reload --port 8000

# In a new terminal — install frontend dependencies
cd apps/desktop
npm install

# Start the frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` and the backend API at `http://localhost:8000`.

---

## Desktop Build

### Build the Tauri Application

```bash
cd apps/desktop

# Development mode (with hot reload)
npm run dev:tauri

# Production build (creates installer)
npm run build:tauri
```

### Build the Python Backend (for bundling)

```bash
# From the project root
scripts\build-backend.bat
```

This uses PyInstaller to bundle the Python backend into a standalone executable.

### Full Build Pipeline

```bash
# Build everything: frontend, backend, bundle, installer
scripts\build-all.bat
```

### Portable Version

```bash
scripts\package-portable.bat
```

Creates `release\ARKON_Portable.zip` — a self-contained directory that runs without installation.

---

## Project Structure

```
ARKON/
├── apps/
│   └── desktop/                  # Tauri desktop application
│       ├── src/                  # React frontend (TypeScript)
│       │   ├── api/              # API client layer
│       │   ├── components/       # UI components
│       │   ├── lib/              # Utilities, config, crash handler
│       │   └── store/            # Zustand state management
│       └── src-tauri/            # Tauri backend (Rust)
│           └── src/              # Process management, IPC commands
│
├── backend/                      # Python FastAPI backend
│   └── app/
│       ├── ai/                   # AI Gateway + 7 provider adapters
│       ├── api/                  # REST & WebSocket endpoints
│       ├── capabilities/         # Capability registry and matching
│       ├── events/               # Event bus with pub-sub
│       ├── execution/            # Task execution engine
│       ├── kernel/               # Core bootstrap and service container
│       ├── models/               # SQLAlchemy domain models
│       ├── plugins/              # Plugin runtime and marketplace
│       ├── repositories/         # Data access layer
│       ├── resources/            # Resource monitoring and allocation
│       ├── runtime/              # Agent runtime management
│       ├── scheduler/            # Task scheduling and prioritization
│       ├── workflow/             # DAG-based workflow engine
│       └── workspace/            # Workspace session management
│
├── worker/                       # Background job processor
├── packages/
│   └── types/                    # Shared TypeScript type definitions
├── plugins/                      # Plugin installation directory
├── scripts/                      # Build and packaging scripts
├── installer/                    # NSIS installer configuration
├── docs/                         # Documentation
└── docker-compose.yml            # Container orchestration
```

---

## Platform Modules

### Frontend

The desktop frontend is built with **React 19**, **TypeScript**, **Vite**, and **Tailwind CSS**. It communicates with the backend via REST APIs and WebSocket connections.

**Key components:**
- `CommandBox` — command parser and task submission
- `MainWorkspace` — dynamic view router
- `Sidebar` — navigation with execution and resource monitoring
- 12 view components covering agents, workflows, plugins, execution, and more

### Backend

The backend is a **Python 3.13** application built with **FastAPI**, **SQLAlchemy 2.x** (async), **Pydantic v2**, and **structlog**. It exposes 59 REST endpoints and 2 WebSocket endpoints.

**Architecture:**
- **Kernel** — bootstraps all infrastructure, manages service lifecycle
- **Service Container** — dependency injection and service registry
- **Repository Pattern** — clean data access layer

### Plugin System

ARKON includes a full plugin runtime with:
- Plugin manifests and dependency resolution
- Sandboxed execution environments
- Lifecycle management (install, enable, disable, uninstall)
- Marketplace support
- Versioning and updates

### AI Gateway

Unified interface to multiple AI providers:

| Provider | Type | Status |
|----------|------|--------|
| OpenRouter | Cloud | Supported |
| Google Gemini | Cloud | Supported |
| NVIDIA NIM | Cloud | Supported |
| Ollama | Local | Supported |
| GitHub Copilot | Adapter | Supported |
| Gemini CLI | Adapter | Supported |
| OpenCode | Adapter | Supported |

### Workflow Runtime

DAG-based workflow engine supporting:
- Node definition with typed inputs/outputs
- Edge connections with dependency tracking
- Parallel execution paths
- Checkpoint and recovery
- Event-driven transitions

---

## Quick Start

### 1. Create a Workspace

```bash
curl -X POST http://localhost:8000/api/v1/workspaces/ \
  -H "Content-Type: application/json" \
  -d '{"name": "my-project"}'
```

### 2. Connect an AI Provider

```bash
curl -X POST http://localhost:8000/ai/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ollama-local",
    "provider_type": "ollama",
    "config": {"base_url": "http://localhost:11434"}
  }'
```

### 3. Install a Plugin

```bash
curl -X POST http://localhost:8000/api/v1/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"name": "filesystem", "version": "latest"}'
```

### 4. Create a Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "video-pipeline",
    "nodes": [
      {"id": "input", "type": "input"},
      {"id": "process", "type": "transform", "depends_on": ["input"]},
      {"id": "output", "type": "output", "depends_on": ["process"]}
    ]
  }'
```

### 5. Run an Agent

```bash
curl -X POST http://localhost:8000/api/v1/execution/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_run",
    "agent_id": "video-editor-01",
    "input_data": {"action": "trim", "start": 0, "end": 30}
  }'
```

---

## Supported AI Providers

### Cloud

| Provider | Models | Authentication |
|----------|--------|----------------|
| [OpenRouter](https://openrouter.ai/) | 100+ models including free tiers | API Key |
| [Google Gemini](https://ai.google.dev/) | Gemini Pro, Flash, Ultra | API Key |
| [NVIDIA NIM](https://build.nvidia.com/) | Llama, Mistral, Phi | API Key |

### Local

| Provider | Models | Setup |
|----------|--------|-------|
| [Ollama](https://ollama.com/) | Llama 3, Mistral, Phi 3, Gemma | `ollama serve` |

### Adapters

| Adapter | Description |
|---------|-------------|
| GitHub Copilot | Use Copilot models via API |
| Gemini CLI | Interface with Gemini CLI tools |
| OpenCode | Interface with OpenCode CLI |

---

## Roadmap

### Current

- [x] Platform Foundation — kernel, runtime, execution engine, scheduler
- [x] AI Gateway — 7 provider adapters with unified interface
- [x] Plugin System — lifecycle, marketplace, sandboxing
- [x] Desktop Application — Tauri-based with React frontend
- [x] Backend API — 59 REST + 2 WebSocket endpoints
- [x] Automated Test Suite — 1,200+ backend tests

### Next

- [ ] System Plugins — Filesystem, Python, Git, Terminal, FFmpeg, Ollama
- [ ] Workflow Templates — pre-built workflow starters
- [ ] Agent Marketplace — community-contributed agents
- [ ] Multi-user support — role-based access control

### Future

- [ ] Video Editing Platform — AI-powered video editing on ARKON
- [ ] Coding Platform — AI-assisted development environment
- [ ] Research Platform — automated research pipelines

---

## Testing

ARKON includes an extensive automated test suite covering all platform modules:

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific module tests
pytest tests/test_kernel.py
pytest tests/test_scheduler.py
pytest tests/test_execution.py
```

The test suite covers:
- Kernel bootstrap and service lifecycle
- Agent runtime and state machines
- Execution engine with dependency resolution
- Scheduler with priority and fairness
- Plugin lifecycle and sandboxing
- Event bus with pub-sub and dead-letter queues
- Workflow DAG compilation and execution
- Resource monitoring and allocation
- All API endpoints

---

## Contributing

1. **Fork** the repository
2. **Clone** your fork
   ```bash
   git clone https://github.com/your-user/arkon.git
   ```
3. **Create a branch** for your feature
   ```bash
   git checkout -b feature/my-feature
   ```
4. **Make changes** and write tests
5. **Run the test suite** to verify
   ```bash
   cd backend && pytest
   ```
6. **Commit** with a clear message
   ```bash
   git commit -m "feat: add new capability matcher"
   ```
7. **Push** to your fork
   ```bash
   git push origin feature/my-feature
   ```
8. **Open a Pull Request** against `main`

### Coding Standards

- **Python**: Ruff for linting, type hints required, docstrings for public APIs
- **TypeScript**: Strict mode, ESLint, Prettier
- **Rust**: `cargo fmt`, `cargo clippy`
- **Tests**: Required for all new features and bug fixes

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Karthik
```

---

<div align="center">

**Built with Python · React · Tauri**

</div>
