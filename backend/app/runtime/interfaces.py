"""ARKON Runtime - Interfaces.

Defines the contracts for all runtime components.
Every component must implement these interfaces.

The Runtime knows NOTHING about:
- Video Editing
- Coding
- Research
- Automation
- Plugins

It only understands agents through interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


# =============================================================================
# Agent States
# =============================================================================


class AgentState(str, Enum):
    """Valid agent states.

    State transitions must be validated.
    Illegal transitions throw exceptions.
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STOPPED = "stopped"
    TERMINATED = "terminated"


# Valid state transitions
VALID_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.CREATED: {AgentState.INITIALIZING, AgentState.TERMINATED},
    AgentState.INITIALIZING: {AgentState.READY, AgentState.FAILED, AgentState.TERMINATED},
    AgentState.READY: {AgentState.RUNNING, AgentState.STOPPED, AgentState.TERMINATED},
    AgentState.RUNNING: {
        AgentState.PAUSED,
        AgentState.WAITING,
        AgentState.COMPLETED,
        AgentState.FAILED,
        AgentState.CANCELLED,
        AgentState.STOPPED,
    },
    AgentState.PAUSED: {AgentState.RUNNING, AgentState.CANCELLED, AgentState.STOPPED},
    AgentState.WAITING: {AgentState.RUNNING, AgentState.CANCELLED, AgentState.STOPPED},
    AgentState.COMPLETED: set(),
    AgentState.FAILED: {AgentState.CREATED, AgentState.TERMINATED},
    AgentState.CANCELLED: {AgentState.CREATED, AgentState.TERMINATED},
    AgentState.STOPPED: {AgentState.CREATED, AgentState.TERMINATED},
    AgentState.TERMINATED: set(),
}


# =============================================================================
# IAgent - The core agent interface
# =============================================================================


class IAgent(ABC):
    """Every agent must implement this interface.

    An Agent is NOT an LLM.
    An Agent is an execution unit.

    It may use:
    - Claude, GPT, Gemini (LLMs)
    - Python, FFmpeg, Whisper, YOLO (Tools)
    - Git, Browser, Docker (Services)
    - or no AI at all

    The Runtime should never assume an agent uses an LLM.
    """

    @abstractmethod
    async def initialize(self, context: Any = None) -> None:
        """Initialize the agent with execution context."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the agent."""
        ...

    @abstractmethod
    async def execute(self, task: dict[str, Any]) -> Any:
        """Execute a task.

        Args:
            task: Task specification dictionary.

        Returns:
            Task result.
        """
        ...

    @abstractmethod
    async def pause(self) -> None:
        """Pause the agent."""
        ...

    @abstractmethod
    async def resume(self) -> None:
        """Resume the agent."""
        ...

    @abstractmethod
    async def cancel(self) -> None:
        """Cancel the current task."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the agent gracefully."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the agent and release resources."""
        ...

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return health status."""
        ...

    @abstractmethod
    async def heartbeat(self) -> dict[str, Any]:
        """Send a heartbeat with current status."""
        ...

    @abstractmethod
    def capabilities(self) -> list[str]:
        """Return list of capabilities this agent provides."""
        ...

    @abstractmethod
    def resources(self) -> dict[str, Any]:
        """Return resource requirements."""
        ...

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Return agent metadata."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Return agent version."""
        ...


# =============================================================================
# IAgentManager - Manages all runtime agents
# =============================================================================


class IAgentManager(ABC):
    """AgentManager owns all runtime agents.

    Responsibilities:
    - Spawn, Register, Destroy
    - Pause, Resume, Cancel, Restart
    - Track, Heartbeat, Health, Recovery
    """

    @abstractmethod
    async def spawn(
        self,
        agent_type: str,
        name: str,
        config: dict[str, Any] | None = None,
        workspace_id: str | None = None,
    ) -> str:
        """Spawn a new agent instance.

        Args:
            agent_type: Type of agent to spawn (matches registry capability).
            name: Human-readable name.
            config: Optional configuration.
            workspace_id: Optional workspace to attach to.

        Returns:
            Agent instance ID.
        """
        ...

    @abstractmethod
    async def register(self, agent_id: str) -> None:
        """Register an agent in the registry."""
        ...

    @abstractmethod
    async def destroy(self, agent_id: str) -> None:
        """Destroy an agent instance."""
        ...

    @abstractmethod
    async def pause(self, agent_id: str) -> None:
        """Pause an agent."""
        ...

    @abstractmethod
    async def resume(self, agent_id: str) -> None:
        """Resume an agent."""
        ...

    @abstractmethod
    async def cancel(self, agent_id: str) -> None:
        """Cancel an agent's current task."""
        ...

    @abstractmethod
    async def restart(self, agent_id: str) -> None:
        """Restart an agent."""
        ...

    @abstractmethod
    async def start(self, agent_id: str) -> None:
        """Start an agent."""
        ...

    @abstractmethod
    async def stop(self, agent_id: str) -> None:
        """Stop an agent."""
        ...

    @abstractmethod
    async def get(self, agent_id: str) -> Any:
        """Get an agent instance."""
        ...

    @abstractmethod
    async def list_active(self) -> list[dict[str, Any]]:
        """List all active agents."""
        ...

    @abstractmethod
    async def heartbeat(self, agent_id: str) -> dict[str, Any]:
        """Get heartbeat from an agent."""
        ...

    @abstractmethod
    async def health(self, agent_id: str) -> dict[str, Any]:
        """Get health status of an agent."""
        ...

    @abstractmethod
    async def recover(self, agent_id: str) -> None:
        """Attempt to recover a failed agent."""
        ...


# =============================================================================
# IAgentRegistry - Stores agent metadata only
# =============================================================================


class IAgentRegistry(ABC):
    """Registry stores metadata only.

    The Registry does NOT execute agents.
    It stores:
    - id, name, version, author, description
    - capabilities, required resources
    - supported models, priority, dependencies, tags
    """

    @abstractmethod
    async def register(
        self,
        agent_type: str,
        metadata: dict[str, Any],
    ) -> None:
        """Register an agent type with metadata."""
        ...

    @abstractmethod
    async def unregister(self, agent_type: str) -> None:
        """Unregister an agent type."""
        ...

    @abstractmethod
    async def get(self, agent_type: str) -> dict[str, Any] | None:
        """Get metadata for an agent type."""
        ...

    @abstractmethod
    async def list_all(self) -> list[dict[str, Any]]:
        """List all registered agent types."""
        ...

    @abstractmethod
    async def find_by_capability(self, capability: str) -> list[dict[str, Any]]:
        """Find agents that provide a specific capability."""
        ...

    @abstractmethod
    async def find_by_capabilities(
        self, capabilities: list[str]
    ) -> list[dict[str, Any]]:
        """Find agents that provide all specified capabilities."""
        ...


# =============================================================================
# IExecutor - Executes agent tasks
# =============================================================================


class IExecutor(ABC):
    """Executes agent tasks within the runtime."""

    @abstractmethod
    async def execute(
        self,
        agent_id: str,
        task: dict[str, Any],
        context: Any = None,
    ) -> Any:
        """Execute a task for an agent."""
        ...

    @abstractmethod
    async def cancel(self, agent_id: str) -> None:
        """Cancel an execution."""
        ...

    @abstractmethod
    async def get_status(self, agent_id: str) -> dict[str, Any]:
        """Get execution status."""
        ...


# =============================================================================
# IContext - Execution context
# =============================================================================


class IContext(ABC):
    """Execution context provided to every agent.

    Every execution receives:
    - Workspace, Kernel Context, Memory, Storage
    - Logger, Configuration, Capabilities
    - Session, Cancellation Token

    Never use globals.
    """

    @abstractmethod
    def get_workspace(self) -> Any:
        """Get the workspace context."""
        ...

    @abstractmethod
    def get_kernel(self) -> Any:
        """Get the kernel context."""
        ...

    @abstractmethod
    def get_memory(self) -> Any:
        """Get the memory store."""
        ...

    @abstractmethod
    def get_storage(self) -> Any:
        """Get the storage interface."""
        ...

    @abstractmethod
    def get_logger(self) -> Any:
        """Get the logger."""
        ...

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Get configuration."""
        ...

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get available capabilities."""
        ...

    @abstractmethod
    def get_session(self) -> Any:
        """Get session data."""
        ...

    @abstractmethod
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        ...

    @abstractmethod
    def cancel(self) -> None:
        """Request cancellation."""
        ...


# =============================================================================
# IHeartbeat - Heartbeat management
# =============================================================================


class IHeartbeat(ABC):
    """Every running agent sends heartbeats.

    Heartbeat contains:
    - timestamp, status, cpu, memory
    - task progress, current activity

    Health automatically degrades if heartbeat expires.
    """

    @abstractmethod
    async def send(
        self,
        agent_id: str,
        status: dict[str, Any],
    ) -> None:
        """Send a heartbeat from an agent."""
        ...

    @abstractmethod
    async def check(self, agent_id: str) -> dict[str, Any]:
        """Check heartbeat status for an agent."""
        ...

    @abstractmethod
    async def check_all(self) -> dict[str, dict[str, Any]]:
        """Check heartbeats for all agents."""
        ...

    @abstractmethod
    async def start_monitoring(self, interval: float = 30.0) -> None:
        """Start heartbeat monitoring."""
        ...

    @abstractmethod
    async def stop_monitoring(self) -> None:
        """Stop heartbeat monitoring."""
        ...


# =============================================================================
# ISandbox - Execution sandbox
# =============================================================================


class ISandbox(ABC):
    """Create execution sandbox.

    Responsible for:
    - Filesystem isolation
    - Temporary storage
    - Environment variables
    - Working directory
    - Permissions
    - Cleanup

    Every agent executes inside its sandbox.
    """

    @abstractmethod
    async def create(
        self,
        agent_id: str,
        config: dict[str, Any] | None = None,
    ) -> str:
        """Create a sandbox for an agent.

        Returns:
            Sandbox ID.
        """
        ...

    @abstractmethod
    async def destroy(self, sandbox_id: str) -> None:
        """Destroy a sandbox and cleanup."""
        ...

    @abstractmethod
    def get_path(self, sandbox_id: str) -> str:
        """Get the sandbox filesystem path."""
        ...

    @abstractmethod
    def get_temp_path(self, sandbox_id: str) -> str:
        """Get the temporary storage path."""
        ...

    @abstractmethod
    async def set_env(self, sandbox_id: str, key: str, value: str) -> None:
        """Set an environment variable."""
        ...

    @abstractmethod
    async def get_env(self, sandbox_id: str, key: str) -> str | None:
        """Get an environment variable."""
        ...

    @abstractmethod
    async def list_active(self) -> list[str]:
        """List active sandbox IDs."""
        ...
