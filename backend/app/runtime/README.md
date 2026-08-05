# ARKON Runtime — Agent Runtime

## Overview

The Agent Runtime is part of the ARKON Kernel. It is responsible for the complete lifecycle of every agent in the platform.

The Runtime knows **NOTHING** about:
- Video Editing
- Coding
- Research
- Automation
- Plugins

It only understands agents through interfaces.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   ARKON Kernel                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌─────────────┐   ┌─────────────┐               │
│   │   Registry   │   │ Capabilities│               │
│   │   (metadata) │   │  (matching) │               │
│   └──────┬──────┘   └──────┬──────┘               │
│          │                  │                       │
│   ┌──────▼──────────────────▼──────┐               │
│   │         AgentManager           │               │
│   │  (lifecycle orchestration)     │               │
│   └──────┬─────────────────────────┘               │
│          │                                         │
│   ┌──────▼──────┐   ┌─────────────┐               │
│   │   Executor   │   │  Heartbeat  │               │
│   │  (task exec) │   │  (health)   │               │
│   └──────┬──────┘   └──────┬──────┘               │
│          │                  │                       │
│   ┌──────▼──────┐   ┌──────▼──────┐               │
│   │   Sandbox    │   │  Resources  │               │
│   │ (isolation)  │   │  (tracking) │               │
│   └─────────────┘   └─────────────┘               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Core Concepts

### Agent = Execution Unit

An Agent is **NOT** an LLM.

An Agent is an execution unit. It may use:
- LLMs (Claude, GPT, Gemini)
- Tools (Python, FFmpeg, Whisper, YOLO)
- Services (Git, Browser, Docker)
- Or no AI at all

### Capability System

Every agent registers capabilities. The scheduler queries:
```
"Who can perform capability X?"
```

Never:
```
"Run CaptionAgent"
```

Example capabilities:
- `filesystem`, `reasoning`, `vision`, `speech`
- `rendering`, `caption_generation`, `transcription`
- `browser`, `python_execution`, `video_encoding`
- `image_generation`, `workflow_planning`, `search`

### State Machine

Agents follow a strict state machine:

```
CREATED → INITIALIZING → READY → RUNNING
                                    ↓
                              PAUSED ↔ RUNNING
                                    ↓
                              WAITING → RUNNING
                                    ↓
                              COMPLETED
                              FAILED → CREATED (retry)
                              CANCELLED
                              STOPPED
                              TERMINATED
```

## Components

### IAgent Interface

Every agent must implement:
- `initialize(context)` — Initialize with execution context
- `start()` — Start the agent
- `execute(task)` — Execute a task
- `pause()` / `resume()` — Pause/resume
- `cancel()` — Cancel current task
- `stop()` / `shutdown()` — Stop and cleanup
- `health()` / `heartbeat()` — Health monitoring
- `capabilities()` / `resources()` — Declare requirements

### AgentManager

Orchestrates all agent lifecycle:
- `spawn(agent_type, name, config)` — Create agent
- `initialize(agent_id)` — Initialize agent
- `start(agent_id)` — Start agent
- `pause(agent_id)` / `resume(agent_id)` — Control
- `cancel(agent_id)` — Cancel task
- `stop(agent_id)` — Stop agent
- `destroy(agent_id)` — Destroy agent
- `execute(agent_id, task)` — Execute task
- `heartbeat(agent_id)` — Get heartbeat
- `health(agent_id)` — Get health
- `recover(agent_id)` — Recover failed agent

### AgentRegistry

Stores agent metadata only (no execution):
- `register(agent_type, metadata)` — Register type
- `get(agent_type)` — Get metadata
- `list_all()` — List all types
- `find_by_capability(cap)` — Find by capability

### CapabilityRegistry

Mandatory capability matching:
- `register(capability, agent_type)` — Register
- `find(capability)` — Find agents
- `find_agents_with_all(caps)` — Find with ALL caps
- `find_agents_with_any(caps)` — Find with ANY caps

### HeartbeatManager

Monitors agent health:
- `send(agent_id, status)` — Send heartbeat
- `check(agent_id)` — Check health
- `start_monitoring()` — Start auto-check
- Expired heartbeats trigger health degradation

### SandboxManager

Isolated execution environments:
- `create(agent_id)` — Create sandbox
- `destroy(sandbox_id)` — Cleanup
- `get_path(sandbox_id)` — Get filesystem path
- `set_env(sandbox_id, key, val)` — Set env var

### ResourceTracker

Tracks resource usage:
- `register_profile(agent_id, profile)` — Declare needs
- `update_usage(usage)` — Track actual usage
- `can_allocate(profile)` — Check if possible
- `get_available()` — Get free resources

### AgentExecutor

Executes tasks:
- `execute(agent_id, task, agent, context)` — Run task
- `cancel(agent_id)` — Cancel execution
- `get_status(agent_id)` — Get status

## Exceptions

- `AgentCreateError` — Creation failed
- `AgentNotFoundError` — Agent not found
- `AgentAlreadyRunningError` — Already running
- `AgentNotRunningError` — Not running
- `AgentExecutionError` — Execution failed
- `AgentTimeoutError` — Execution timed out
- `InvalidStateTransitionError` — Illegal state change
- `CapabilityNotFoundError` — No agent has capability
- `SandboxCreateError` — Sandbox creation failed
- `HeartbeatExpiredError` — Heartbeat timeout

## Events

- `AgentCreated`, `AgentInitialized`, `AgentStarted`
- `AgentPaused`, `AgentResumed`, `AgentCancelled`
- `AgentHeartbeat`, `AgentCompleted`, `AgentFailed`
- `AgentStopped`, `AgentDestroyed`, `AgentRecovered`
- `AgentStateTransition`

## Usage

```python
from app.runtime import AgentManager, CapabilityRegistry

# Initialize
manager = AgentManager(base_path="/tmp/runtime")

# Register agent type
await manager.register_agent_type("caption_agent", {
    "name": "Caption Generator",
    "capabilities": ["caption_generation", "vision"],
    "required_resources": {"cpu": 1.0, "ram": 512.0},
})

# Spawn agent
agent_id = await manager.spawn(
    "caption_agent",
    "My Caption Agent",
    config={"model": "gpt-4"},
)

# Initialize and start
await manager.initialize(agent_id)
await manager.start(agent_id)

# Execute task
result = await manager.execute(agent_id, {
    "type": "generate_caption",
    "payload": {"image": "photo.jpg"},
})

# Health check
health = await manager.health(agent_id)

# Cleanup
await manager.destroy(agent_id)
```

## File Structure

```
app/runtime/
├── __init__.py         # Module exports
├── interfaces.py       # IAgent, IAgentManager, etc.
├── exceptions.py       # All runtime exceptions
├── events.py           # Event types
├── state_machine.py    # Agent state machine
├── agent.py            # Agent data models
├── context.py          # Execution context
├── capabilities.py     # Capability registry
├── resources.py        # Resource management
├── heartbeat.py        # Heartbeat monitoring
├── sandbox.py          # Execution sandbox
├── executor.py         # Task execution
├── registry.py         # Agent registry
├── manager.py          # Agent manager
└── README.md           # This file
```
