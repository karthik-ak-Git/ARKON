# ARKON

Multi-agent runtime platform with AI orchestration.

![ARKON](assets/branding/banner.png)

## Features

- Multi-agent runtime with sandboxed execution
- Workflow engine with DAG-based orchestration
- AI gateway (OpenRouter, Gemini, Ollama, NVIDIA NIM, Copilot, Gemini CLI, OpenCode)
- Plugin marketplace with lifecycle management
- Resource manager with CPU, memory, disk, GPU monitoring
- Scheduler with priority, fairness, preemption
- Event bus with pub-sub and dead-letter queues
- Desktop app built with Tauri + React

## Downloads

| Platform | Link |
|----------|------|
| Windows (Installer) | [Latest Release](https://github.com/karthik-ak-Git/ARKON/releases/latest) |
| Windows (Portable) | [Latest Release](https://github.com/karthik-ak-Git/ARKON/releases/latest) |
| Linux (.deb) | [Latest Release](https://github.com/karthik-ak-Git/ARKON/releases/latest) |

## Quick Start

```bash
# Clone
git clone https://github.com/karthik-ak-Git/ARKON.git
cd ARKON

# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Frontend
cd ../apps/desktop
npm install
npm run dev
```

## Screenshots

| Welcome | Workspace | Execution |
|---------|-----------|-----------|
| ![Welcome](assets/screenshots/welcome.png) | ![Workspace](assets/screenshots/workspace.png) | ![Execution](assets/screenshots/execution.png) |

## Architecture

```
Desktop Shell (Tauri + React)
    ↓ IPC
API Layer (FastAPI, 59 REST + 2 WS endpoints)
    ↓
Core Runtime (Python 3.13)
    ├── Kernel — bootstrap, service container
    ├── Runtime — agent lifecycle, heartbeat
    ├── Execution — task dispatch, dependencies
    ├── Scheduler — priority, fairness, preemption
    ├── Capabilities — matching, ranking
    ├── Resources — CPU, memory, disk, GPU
    ├── Workflow — DAG compiler, runtime
    ├── Events — pub-sub, dead-letter, replay
    ├── Plugins — sandboxed execution, marketplace
    └── AI Gateway — 7 provider adapters
```

## API

59 REST endpoints + 2 WebSocket endpoints. See [docs/api.md](docs/api.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Backend](docs/backend.md)
- [Frontend](docs/frontend.md)
- [API Reference](docs/api.md)
- [Developer Guide](docs/developer-guide.md)
- [Workflow Runtime](docs/workflow-runtime.md)
- [Plugin Runtime](docs/plugin-runtime.md)
- [AI Gateway](docs/ai-gateway.md)
- [Scheduler](docs/scheduler.md)
- [Execution Engine](docs/execution-engine.md)

## Roadmap

- [ ] Voice input and output
- [ ] Plugin marketplace UI
- [ ] Multi-user support
- [ ] Mobile companion app
- [ ] Cloud sync

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE)

---

<p align="center">Built by Karthik</p>
