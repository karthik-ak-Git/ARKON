"""ARKON Runtime - Exceptions.

All runtime-specific exceptions.
"""

from __future__ import annotations

from typing import Any


class RuntimeError(Exception):
    """Base runtime error."""
    pass


class AgentError(RuntimeError):
    """Base agent error."""
    pass


class AgentCreateError(AgentError):
    """Failed to create agent."""
    def __init__(self, agent_id: str, reason: str = ""):
        self.agent_id = agent_id
        self.reason = reason
        super().__init__(f"Failed to create agent '{agent_id}': {reason}")


class AgentNotFoundError(AgentError):
    """Agent not found."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: '{agent_id}'")


class AgentAlreadyExistsError(AgentError):
    """Agent already exists."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent already exists: '{agent_id}'")


class AgentNotRunningError(AgentError):
    """Agent is not running."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent is not running: '{agent_id}'")


class AgentAlreadyRunningError(AgentError):
    """Agent is already running."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent is already running: '{agent_id}'")


class AgentNotPausedError(AgentError):
    """Agent is not paused."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent is not paused: '{agent_id}'")


class AgentNotReadyError(AgentError):
    """Agent is not ready."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent is not ready: '{agent_id}'")


class AgentTerminatedError(AgentError):
    """Agent is terminated."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent is terminated: '{agent_id}'")


class AgentExecutionError(AgentError):
    """Agent execution failed."""
    def __init__(self, agent_id: str, reason: str = ""):
        self.agent_id = agent_id
        self.reason = reason
        super().__init__(f"Agent execution failed '{agent_id}': {reason}")


class AgentTimeoutError(AgentError):
    """Agent execution timed out."""
    def __init__(self, agent_id: str, timeout: float = 0):
        self.agent_id = agent_id
        self.timeout = timeout
        super().__init__(f"Agent timed out '{agent_id}' after {timeout}s")


class AgentCancelledError(AgentError):
    """Agent was cancelled."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent cancelled: '{agent_id}'")


# State machine errors


class InvalidStateTransitionError(RuntimeError):
    """Invalid state transition attempted."""
    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid state transition: '{from_state}' -> '{to_state}'"
        )


# Registry errors


class RegistryError(RuntimeError):
    """Base registry error."""
    pass


class AgentTypeNotFoundError(RegistryError):
    """Agent type not found in registry."""
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        super().__init__(f"Agent type not found: '{agent_type}'")


class AgentTypeAlreadyRegisteredError(RegistryError):
    """Agent type already registered."""
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        super().__init__(f"Agent type already registered: '{agent_type}'")


class CapabilityNotFoundError(RegistryError):
    """No agent provides the requested capability."""
    def __init__(self, capability: str):
        self.capability = capability
        super().__init__(f"No agent provides capability: '{capability}'")


# Sandbox errors


class SandboxError(RuntimeError):
    """Base sandbox error."""
    pass


class SandboxCreateError(SandboxError):
    """Failed to create sandbox."""
    def __init__(self, agent_id: str, reason: str = ""):
        self.agent_id = agent_id
        self.reason = reason
        super().__init__(f"Failed to create sandbox for '{agent_id}': {reason}")


class SandboxNotFoundError(SandboxError):
    """Sandbox not found."""
    def __init__(self, sandbox_id: str):
        self.sandbox_id = sandbox_id
        super().__init__(f"Sandbox not found: '{sandbox_id}'")


# Resource errors


class ResourceError(RuntimeError):
    """Base resource error."""
    pass


class InsufficientResourcesError(ResourceError):
    """Insufficient resources available."""
    def __init__(self, required: dict[str, Any], available: dict[str, Any]):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient resources: required={required}, available={available}"
        )


# Heartbeat errors


class HeartbeatError(RuntimeError):
    """Base heartbeat error."""
    pass


class HeartbeatExpiredError(HeartbeatError):
    """Heartbeat expired - agent may be dead."""
    def __init__(self, agent_id: str, last_beat: float = 0):
        self.agent_id = agent_id
        self.last_beat = last_beat
        super().__init__(f"Heartbeat expired for agent '{agent_id}'")


# Execution errors


class ExecutionError(RuntimeError):
    """Base execution error."""
    pass


class TaskValidationError(ExecutionError):
    """Task validation failed."""
    def __init__(self, reason: str = ""):
        self.reason = reason
        super().__init__(f"Task validation failed: {reason}")


class ContextError(RuntimeError):
    """Context error."""
    pass


class ContextNotInitializedError(ContextError):
    """Context not initialized."""
    def __init__(self, component: str = ""):
        self.component = component
        super().__init__(f"Context not initialized: {component}")


# Required for type hints
from typing import Any  # noqa: E402
