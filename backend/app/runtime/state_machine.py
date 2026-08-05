"""ARKON Runtime - State Machine.

Manages agent state transitions with validation.
Only valid transitions are allowed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.runtime.exceptions import InvalidStateTransitionError
from app.runtime.interfaces import AgentState, VALID_TRANSITIONS

logger = structlog.get_logger(__name__)


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: AgentState
    to_state: AgentState
    timestamp: float = field(default_factory=time.time)
    reason: str = ""


class AgentStateMachine:
    """Manages agent state transitions.

    State transitions must be validated.
    Illegal transitions throw exceptions.
    """

    def __init__(self, initial_state: AgentState = AgentState.CREATED):
        """Initialize state machine."""
        self._state = initial_state
        self._history: list[StateTransition] = []
        self._transition_count = 0

    @property
    def state(self) -> AgentState:
        """Get current state."""
        return self._state

    @property
    def history(self) -> list[StateTransition]:
        """Get transition history."""
        return self._history.copy()

    @property
    def transition_count(self) -> int:
        """Get total transition count."""
        return self._transition_count

    def can_transition(self, to_state: AgentState) -> bool:
        """Check if transition to target state is valid."""
        valid_targets = VALID_TRANSITIONS.get(self._state, set())
        return to_state in valid_targets

    def transition(
        self,
        to_state: AgentState,
        reason: str = "",
    ) -> StateTransition:
        """Perform a state transition.

        Args:
            to_state: Target state.
            reason: Optional reason for transition.

        Returns:
            The transition record.

        Raises:
            InvalidStateTransitionError: If transition is invalid.
        """
        if not self.can_transition(to_state):
            raise InvalidStateTransitionError(
                self._state.value, to_state.value
            )

        from_state = self._state
        self._state = to_state
        self._transition_count += 1

        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            reason=reason,
        )
        self._history.append(transition)

        logger.debug(
            "agent_state_transition",
            from_state=from_state.value,
            to_state=to_state.value,
            reason=reason,
        )

        return transition

    def force_state(
        self,
        state: AgentState,
        reason: str = "forced",
    ) -> StateTransition:
        """Force a state without validation (for recovery).

        Args:
            state: Target state.
            reason: Reason for forced transition.

        Returns:
            The transition record.
        """
        from_state = self._state
        self._state = state
        self._transition_count += 1

        transition = StateTransition(
            from_state=from_state,
            to_state=state,
            reason=reason,
        )
        self._history.append(transition)

        logger.warning(
            "agent_state_forced",
            from_state=from_state.value,
            to_state=state.value,
            reason=reason,
        )

        return transition

    def reset(self) -> None:
        """Reset state machine to initial state."""
        self._state = AgentState.CREATED
        self._history.clear()
        self._transition_count = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self._state.value,
            "transition_count": self._transition_count,
            "history": [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "timestamp": t.timestamp,
                    "reason": t.reason,
                }
                for t in self._history
            ],
        }
