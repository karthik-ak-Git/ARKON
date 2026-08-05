"""ARKON Runtime - Agent Runtime Module.

The Runtime is responsible for the complete lifecycle
of every agent in the platform.

The Runtime knows NOTHING about:
- Video Editing
- Coding
- Research
- Automation
- Plugins

It only understands agents through interfaces.
"""

from app.runtime.agent import AgentConfig, AgentInstance, AgentMetadata
from app.runtime.capabilities import CapabilityRegistry
from app.runtime.context import ExecutionContext
from app.runtime.events import (
    AgentCancelled,
    AgentCompleted,
    AgentCreated,
    AgentDestroyed,
    AgentEvent,
    AgentFailed,
    AgentHeartbeat,
    AgentInitialized,
    AgentPaused,
    AgentRecovered,
    AgentResumed,
    AgentStarted,
    AgentStateTransition,
    AgentStopped,
)
from app.runtime.exceptions import (
    AgentAlreadyExistsError,
    AgentAlreadyRunningError,
    AgentCancelledError,
    AgentCreateError,
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    AgentNotPausedError,
    AgentNotRunningError,
    AgentNotReadyError,
    AgentTerminatedError,
    AgentTimeoutError,
    AgentTypeAlreadyRegisteredError,
    AgentTypeNotFoundError,
    CapabilityNotFoundError,
    ContextError,
    ContextNotInitializedError,
    ExecutionError,
    HeartbeatError,
    HeartbeatExpiredError,
    InsufficientResourcesError,
    InvalidStateTransitionError,
    ResourceError,
    RuntimeError,
    SandboxCreateError,
    SandboxError,
    SandboxNotFoundError,
    TaskValidationError,
)
from app.runtime.executor import AgentExecutor
from app.runtime.heartbeat import HeartbeatManager
from app.runtime.interfaces import (
    IAgent,
    IAgentManager,
    IAgentRegistry,
    IContext,
    IExecutor,
    IHeartbeat,
    ISandbox,
    AgentState,
    VALID_TRANSITIONS,
)
from app.runtime.manager import AgentManager
from app.runtime.registry import AgentRegistry
from app.runtime.resources import ResourceProfile, ResourceTracker
from app.runtime.sandbox import SandboxManager
from app.runtime.state_machine import AgentStateMachine

__all__ = [
    # Interfaces
    "IAgent",
    "IAgentManager",
    "IAgentRegistry",
    "IContext",
    "IExecutor",
    "IHeartbeat",
    "ISandbox",
    "AgentState",
    "VALID_TRANSITIONS",
    # Agent
    "AgentConfig",
    "AgentInstance",
    "AgentMetadata",
    # Components
    "AgentManager",
    "AgentRegistry",
    "AgentExecutor",
    "CapabilityRegistry",
    "ExecutionContext",
    "HeartbeatManager",
    "ResourceTracker",
    "ResourceProfile",
    "SandboxManager",
    "AgentStateMachine",
    # Events
    "AgentEvent",
    "AgentCreated",
    "AgentInitialized",
    "AgentStarted",
    "AgentPaused",
    "AgentResumed",
    "AgentHeartbeat",
    "AgentCompleted",
    "AgentFailed",
    "AgentCancelled",
    "AgentStopped",
    "AgentDestroyed",
    "AgentRecovered",
    "AgentStateTransition",
    # Exceptions
    "RuntimeError",
    "AgentError",
    "AgentCreateError",
    "AgentNotFoundError",
    "AgentAlreadyExistsError",
    "AgentNotRunningError",
    "AgentAlreadyRunningError",
    "AgentNotPausedError",
    "AgentNotReadyError",
    "AgentTerminatedError",
    "AgentExecutionError",
    "AgentTimeoutError",
    "AgentCancelledError",
    "InvalidStateTransitionError",
    "RegistryError",
    "AgentTypeNotFoundError",
    "AgentTypeAlreadyRegisteredError",
    "CapabilityNotFoundError",
    "SandboxError",
    "SandboxCreateError",
    "SandboxNotFoundError",
    "ResourceError",
    "InsufficientResourcesError",
    "HeartbeatError",
    "HeartbeatExpiredError",
    "ExecutionError",
    "TaskValidationError",
    "ContextError",
    "ContextNotInitializedError",
]
