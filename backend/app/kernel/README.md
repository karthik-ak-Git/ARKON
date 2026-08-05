# ARKON Kernel

The operating core of the ARKON platform.

## What Is the Kernel?

The Kernel is **NOT** an agent.
It is **NOT** a scheduler.
It is **NOT** a workflow engine.

It is the **operating core**.

Think of it like:

- Linux Kernel
- Windows NT Kernel
- Docker Engine
- Kubernetes Control Plane

Every subsystem communicates through the Kernel.
Nothing bypasses it.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    KERNEL                           │
├──────────────┬──────────────┬───────────────────────┤
│   Service    │    Module    │     Lifecycle         │
│  Container   │   Registry   │     Manager           │
├──────────────┴──────────────┴───────────────────────┤
│              Application Context                    │
├─────────────────────────────────────────────────────┤
│  Runtime │ Scheduler │ EventBus │ Plugin Loader     │
│  Storage │ Memory    │ Monitor  │ Workflow Engine   │
└─────────────────────────────────────────────────────┘
```

## Core Components

### Kernel (`kernel.py`)

The central hub. Manages modules, services, and lifecycle.

```python
from app.kernel import Kernel

kernel = Kernel()
await kernel.bootstrap(config)
# ... application runs ...
await kernel.shutdown()
```

### Service Container (`service_container.py`)

Lightweight dependency injection container.

```python
from app.kernel import ServiceContainer

container = ServiceContainer()
container.register(Database, db_instance)
container.register(Cache, cache_factory, singleton=False)

db = container.resolve(Database)
```

### Module Registry (`registry.py`)

Tracks all registered modules.

```python
from app.kernel import ModuleRegistry

registry = ModuleRegistry()
registry.register(runtime_module)
registry.register(scheduler_module)
```

### Lifecycle Manager (`lifecycle.py`)

Coordinates startup/shutdown order via topological sort.

```python
from app.kernel import LifecycleManager

lm = LifecycleManager(registry)
await lm.startup(context)
await lm.shutdown()
```

### Application Context (`context.py`)

Immutable context passed to all modules.

```python
from app.kernel import Context, create_context

ctx = create_context(
    config=config,
    database=db,
    redis=redis,
)
```

### Bootstrap (`bootstrap.py`)

Orchestrates the complete startup sequence.

```python
from app.kernel import bootstrap_kernel

kernel = await bootstrap_kernel()
```

## Interfaces

All kernel components implement strict interfaces:

| Interface | Purpose |
|-----------|---------|
| `IInitializable` | Components that need init/shutdown |
| `IStartable` | Components that can be started/stopped |
| `IHealthCheckable` | Components that expose health status |
| `IConfigurable` | Components that accept configuration |
| `IModule` | All kernel modules must implement this |
| `IServiceContainer` | Dependency injection container |
| `IContext` | Application context |

## Module Registration

Every subsystem registers itself:

```python
from app.kernel import Kernel, IModule

class Runtime(IModule):
    @property
    def name(self) -> str:
        return "runtime"

    @property
    def version(self) -> str:
        return "0.1.0"

    def dependencies(self) -> list[str]:
        return []  # No dependencies

    async def initialize(self, ctx) -> None:
        # Initialize runtime
        pass

    async def start(self) -> None:
        # Start runtime
        pass

    async def stop(self) -> None:
        # Stop runtime
        pass

    async def health_check(self) -> dict:
        return {"status": "ok"}

    @property
    def is_healthy(self) -> bool:
        return True

# Register with kernel
kernel = Kernel()
kernel.register(Runtime())
kernel.register(Scheduler())
kernel.register(EventBus())
```

## Bootstrap Sequence

```
Application starts
       │
       ▼
┌─────────────┐
│   Config    │  pydantic-settings
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Logger    │  structlog
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │  async SQLAlchemy
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Redis    │  async connection pool
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    NATS     │  async client
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Kernel    │  create + register modules
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FastAPI   │  start HTTP server
└─────────────┘
```

## Lifecycle States

```
CREATED ──► INITIALIZING ──► INITIALIZED ──► STARTING ──► RUNNING
                                                         │
                                                         ▼
                                                     STOPPING ──► STOPPED
                                                         │
                                                         ▼
                                                      FAILED
```

## Health Checks

Every module registers a health check:

```python
async def health_check(self) -> dict:
    return {
        "status": "ok",
        "connections": self._pool.size(),
    }
```

The Kernel aggregates all health checks:

```python
health = await kernel.health_check()
# {
#     "kernel": {"state": "running", "module_count": 5},
#     "modules": {
#         "runtime": {"status": "healthy", "details": {...}},
#         "scheduler": {"status": "healthy", "details": {...}},
#     },
#     "overall": "healthy"
# }
```

## Exceptions

| Exception | When |
|-----------|------|
| `KernelError` | Base exception |
| `ServiceNotFoundError` | Service not registered |
| `DuplicateServiceError` | Service already registered |
| `ModuleNotFoundError` | Module not found |
| `DuplicateModuleError` | Module already registered |
| `CircularDependencyError` | Dependencies form a cycle |
| `DependencyNotSatisfiedError` | Required module missing |
| `LifecycleError` | Lifecycle transition error |
| `StartupError` | Startup failed |
| `ShutdownError` | Shutdown failed |
| `ContextNotInitializedError` | Context accessed before init |

## What the Kernel Does NOT Do

- ❌ No Workspace logic
- ❌ No Project logic
- ❌ No Agent logic
- ❌ No Video logic
- ❌ No AI logic
- ❌ No Workflow logic
- ❌ No business logic of any kind

The Kernel is pure platform infrastructure.

## File Structure

```
backend/app/kernel/
├── __init__.py          # Package exports
├── interfaces.py        # Interface contracts
├── exceptions.py        # Domain exceptions
├── service_container.py # DI container
├── context.py           # Application context
├── registry.py          # Module registry
├── lifecycle.py         # Startup/shutdown coordinator
├── kernel.py            # Core kernel class
├── bootstrap.py         # Startup orchestration
└── README.md            # This file
```
