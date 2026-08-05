"""ARKON Runtime - Events.

All runtime event types.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeEvent:
    """Base runtime event."""
    timestamp: float = field(default_factory=time.time)
    event_type: str = ""
    agent_id: str = ""


@dataclass
class AgentCreated(RuntimeEvent):
    """Agent instance created."""
    event_type: str = "agent_created"
    agent_type: str = ""
    name: str = ""


@dataclass
class AgentInitialized(RuntimeEvent):
    """Agent initialized."""
    event_type: str = "agent_initialized"


@dataclass
class AgentStarted(RuntimeEvent):
    """Agent started."""
    event_type: str = "agent_started"


@dataclass
class AgentPaused(RuntimeEvent):
    """Agent paused."""
    event_type: str = "agent_paused"
    reason: str = ""


@dataclass
class AgentResumed(RuntimeEvent):
    """Agent resumed."""
    event_type: str = "agent_resumed"


@dataclass
class AgentHeartbeat(RuntimeEvent):
    """Agent heartbeat received."""
    event_type: str = "agent_heartbeat"
    status: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCompleted(RuntimeEvent):
    """Agent task completed."""
    event_type: str = "agent_completed"
    result: Any = None


@dataclass
class AgentFailed(RuntimeEvent):
    """Agent failed."""
    event_type: str = "agent_failed"
    error: str = ""
    error_type: str = ""


@dataclass
class AgentCancelled(RuntimeEvent):
    """Agent cancelled."""
    event_type: str = "agent_cancelled"


@dataclass
class AgentStopped(RuntimeEvent):
    """Agent stopped."""
    event_type: str = "agent_stopped"


@dataclass
class AgentDestroyed(RuntimeEvent):
    """Agent destroyed."""
    event_type: str = "agent_destroyed"


@dataclass
class AgentRecovered(RuntimeEvent):
    """Agent recovered from failure."""
    event_type: str = "agent_recovered"


@dataclass
class AgentStateTransition(RuntimeEvent):
    """Agent state transition."""
    event_type: str = "agent_state_transition"
    from_state: str = ""
    to_state: str = ""


# Event type registry
EVENT_TYPES: dict[str, type[RuntimeEvent]] = {
    "agent_created": AgentCreated,
    "agent_initialized": AgentInitialized,
    "agent_started": AgentStarted,
    "agent_paused": AgentPaused,
    "agent_resumed": AgentResumed,
    "agent_heartbeat": AgentHeartbeat,
    "agent_completed": AgentCompleted,
    "agent_failed": AgentFailed,
    "agent_cancelled": AgentCancelled,
    "agent_stopped": AgentStopped,
    "agent_destroyed": AgentDestroyed,
    "agent_recovered": AgentRecovered,
    "agent_state_transition": AgentStateTransition,
}

# Alias for convenience
AgentEvent = RuntimeEvent
