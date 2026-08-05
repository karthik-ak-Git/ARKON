"""ARKON Runtime - Agent Manager.

The AgentManager owns all runtime agents.
It orchestrates all agent lifecycle operations.

Lifecycle:
    spawn → initialize → start → [running] → stop → [stopped]
                            ↓
                      pause → [paused] → resume → [running]
                            ↓
                      cancel → [cancelled]
                            ↓
                      destroy → [terminated]
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

import structlog

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
    AgentCreateError,
    AgentNotFoundError,
    AgentNotPausedError,
    AgentNotRunningError,
    AgentTerminatedError,
    InvalidStateTransitionError,
)
from app.runtime.executor import AgentExecutor
from app.runtime.heartbeat import HeartbeatManager
from app.runtime.interfaces import AgentState
from app.runtime.registry import AgentRegistry
from app.runtime.resources import ResourceProfile, ResourceTracker
from app.runtime.sandbox import SandboxManager
from app.runtime.state_machine import AgentStateMachine

logger = structlog.get_logger(__name__)


class AgentManager:
    """AgentManager owns all runtime agents.

    Responsibilities:
    - Spawn, Register, Destroy
    - Pause, Resume, Cancel, Restart
    - Track, Heartbeat, Health, Recovery
    """

    def __init__(
        self,
        base_path: str = "/tmp/arkon_runtime",
        event_handler: Callable[[AgentEvent], Any] | None = None,
    ) -> None:
        """Initialize agent manager.

        Args:
            base_path: Base path for runtime data.
            event_handler: Optional event handler callback.
        """
        self._base_path = base_path
        self._event_handler = event_handler

        # Component managers
        self._registry = AgentRegistry()
        self._capabilities = CapabilityRegistry()
        self._heartbeat = HeartbeatManager(event_handler=self._emit_event)
        self._sandbox = SandboxManager(base_path)
        self._executor = AgentExecutor(event_handler=self._emit_event)
        self._resources = ResourceTracker()

        # Active agents: agent_id → AgentInstance
        self._agents: dict[str, AgentInstance] = {}

        # State machines: agent_id → AgentStateMachine
        self._state_machines: dict[str, AgentStateMachine] = {}

        # Agent implementations: agent_id → IAgent
        self._implementations: dict[str, Any] = {}

        # Agent factory functions: agent_type → factory
        self._factories: dict[str, Callable] = {}

    def register_factory(
        self,
        agent_type: str,
        factory: Callable[..., Any],
    ) -> None:
        """Register a factory function for creating agent implementations.

        Args:
            agent_type: The agent type identifier.
            factory: Async callable that returns an IAgent instance.
        """
        self._factories[agent_type] = factory
        logger.debug("agent_factory_registered", agent_type=agent_type)

    async def register_agent_type(
        self,
        agent_type: str,
        metadata: dict[str, Any],
    ) -> None:
        """Register an agent type in the registry and capabilities."""
        await self._registry.register(agent_type, metadata)

        # Register capabilities
        for cap in metadata.get("capabilities", []):
            self._capabilities.register(
                cap, agent_type,
                description=metadata.get("description", ""),
            )

    async def spawn(
        self,
        agent_type: str,
        name: str,
        config: dict[str, Any] | None = None,
        workspace_id: str | None = None,
    ) -> str:
        """Spawn a new agent instance.

        Args:
            agent_type: Type of agent to spawn.
            name: Human-readable name.
            config: Optional configuration.
            workspace_id: Optional workspace to attach to.

        Returns:
            Agent instance ID.

        Raises:
            AgentCreateError: If creation fails.
        """
        # Get registry metadata
        metadata_dict = await self._registry.get(agent_type)
        if not metadata_dict:
            metadata = AgentMetadata(agent_type=agent_type, name=name)
        else:
            metadata = AgentMetadata.from_dict(metadata_dict)

        # Create agent config
        agent_config = AgentConfig.from_dict(config or {})

        # Create instance
        instance = AgentInstance(
            agent_type=agent_type,
            name=name,
            config=agent_config,
            metadata=metadata,
            workspace_id=workspace_id,
        )

        # Create state machine
        sm = AgentStateMachine(AgentState.CREATED)

        # Create sandbox
        sandbox_id = await self._sandbox.create(instance.id)
        instance.sandbox_id = sandbox_id

        # Register resource profile
        resource_profile = ResourceProfile(
            cpu=metadata.required_resources.get("cpu", 0.5),
            ram=metadata.required_resources.get("ram", 256.0),
            vram=metadata.required_resources.get("vram", 0.0),
            gpu_required=metadata.required_resources.get("gpu_required", False),
            network=metadata.required_resources.get("network", False),
            disk=metadata.required_resources.get("disk", 100.0),
            priority=metadata.priority,
        )
        self._resources.register_profile(instance.id, resource_profile)

        # Store
        self._agents[instance.id] = instance
        self._state_machines[instance.id] = sm

        # Emit event
        await self._emit(AgentCreated(
            agent_id=instance.id,
            agent_type=agent_type,
            name=name,
        ))

        logger.info(
            "agent_spawned",
            agent_id=instance.id,
            agent_type=agent_type,
            name=name,
        )

        return instance.id

    async def initialize(self, agent_id: str) -> None:
        """Initialize an agent."""
        instance = self._get_agent(agent_id)
        sm = self._get_state_machine(agent_id)

        # Create implementation if factory exists
        if instance.agent_type in self._factories:
            factory = self._factories[instance.agent_type]
            try:
                impl = await factory()
                self._implementations[agent_id] = impl
            except Exception as e:
                sm.force_state(AgentState.FAILED, str(e))
                instance.error = str(e)
                raise AgentCreateError(agent_id, str(e)) from e

        # Transition state
        sm.transition(AgentState.INITIALIZING, "initializing")
        await self._emit(AgentStateTransition(
            agent_id=agent_id,
            from_state=AgentState.CREATED.value,
            to_state=AgentState.INITIALIZING.value,
        ))

        # Initialize if implementation exists
        if agent_id in self._implementations:
            try:
                context = await self._create_context(instance)
                await self._implementations[agent_id].initialize(context)
            except Exception as e:
                sm.force_state(AgentState.FAILED, str(e))
                instance.error = str(e)
                raise

        # Transition to ready
        sm.transition(AgentState.READY, "initialized")
        await self._emit(AgentInitialized(agent_id=agent_id))

    async def start(self, agent_id: str) -> None:
        """Start an agent."""
        instance = self._get_agent(agent_id)
        sm = self._get_state_machine(agent_id)

        if instance.state == AgentState.RUNNING:
            raise AgentAlreadyRunningError(agent_id)

        sm.transition(AgentState.RUNNING, "started")
        instance.state = AgentState.RUNNING
        instance.started_at = time.time()

        # Start heartbeat monitoring
        await self._heartbeat.start_monitoring()

        # Start implementation if exists
        if agent_id in self._implementations:
            try:
                await self._implementations[agent_id].start()
            except Exception as e:
                sm.force_state(AgentState.FAILED, str(e))
                instance.error = str(e)
                raise

        await self._emit(AgentStarted(agent_id=agent_id))
        logger.info("agent_started", agent_id=agent_id)

    async def stop(self, agent_id: str) -> None:
        """Stop an agent."""
        instance = self._get_agent(agent_id)
        sm = self._get_state_machine(agent_id)

        # Stop implementation if exists
        if agent_id in self._implementations:
            try:
                await self._implementations[agent_id].stop()
            except Exception:
                pass

        sm.transition(AgentState.STOPPED, "stopped")
        instance.state = AgentState.STOPPED

        await self._emit(AgentStopped(agent_id=agent_id))
        logger.info("agent_stopped", agent_id=agent_id)

    async def pause(self, agent_id: str) -> None:
        """Pause an agent."""
        instance = self._get_agent(agent_id)
        sm = self._get_state_machine(agent_id)

        if instance.state != AgentState.RUNNING:
            raise AgentNotRunningError(agent_id)

        # Pause implementation if exists
        if agent_id in self._implementations:
            try:
                await self._implementations[agent_id].pause()
            except Exception:
                pass

        sm.transition(AgentState.PAUSED, "paused")
        instance.state = AgentState.PAUSED

        await self._emit(AgentPaused(agent_id=agent_id))
        logger.info("agent_paused", agent_id=agent_id)

    async def resume(self, agent_id: str) -> None:
        """Resume a paused agent."""
        instance = self._get_agent(agent_id)
        sm = self._get_state_machine(agent_id)

        if instance.state != AgentState.PAUSED:
            raise AgentNotPausedError(agent_id)

        # Resume implementation if exists
        if agent_id in self._implementations:
            try:
                await self._implementations[agent_id].resume()
            except Exception:
                pass

        sm.transition(AgentState.RUNNING, "resumed")
        instance.state = AgentState.RUNNING

        await self._emit(AgentResumed(agent_id=agent_id))
        logger.info("agent_resumed", agent_id=agent_id)

    async def cancel(self, agent_id: str) -> None:
        """Cancel an agent's current task."""
        instance = self._get_agent(agent_id)
        sm = self._get_state_machine(agent_id)

        # Cancel execution
        await self._executor.cancel(agent_id)

        # Cancel implementation if exists
        if agent_id in self._implementations:
            try:
                await self._implementations[agent_id].cancel()
            except Exception:
                pass

        sm.transition(AgentState.CANCELLED, "cancelled")
        instance.state = AgentState.CANCELLED

        await self._emit(AgentCancelled(agent_id=agent_id))
        logger.info("agent_cancelled", agent_id=agent_id)

    async def restart(self, agent_id: str) -> None:
        """Restart an agent."""
        await self.stop(agent_id)
        await self.start(agent_id)

    async def destroy(self, agent_id: str) -> None:
        """Destroy an agent instance."""
        instance = self._get_agent(agent_id)

        # Shutdown implementation if exists
        if agent_id in self._implementations:
            try:
                await self._implementations[agent_id].shutdown()
            except Exception:
                pass
            del self._implementations[agent_id]

        # Cleanup sandbox
        if instance.sandbox_id:
            try:
                await self._sandbox.destroy(instance.sandbox_id)
            except Exception:
                pass

        # Cleanup resources
        self._resources.remove_usage(agent_id)
        self._resources.unregister_profile(agent_id)

        # Cleanup heartbeat
        await self._heartbeat.remove(agent_id)

        # Force terminal state
        sm = self._get_state_machine(agent_id)
        sm.force_state(AgentState.TERMINATED, "destroyed")
        instance.state = AgentState.TERMINATED

        # Remove from tracking
        del self._agents[agent_id]
        del self._state_machines[agent_id]

        await self._emit(AgentDestroyed(agent_id=agent_id))
        logger.info("agent_destroyed", agent_id=agent_id)

    async def execute(
        self, agent_id: str, task: dict[str, Any]
    ) -> Any:
        """Execute a task for an agent."""
        instance = self._get_agent(agent_id)

        if instance.state != AgentState.RUNNING:
            raise AgentNotRunningError(agent_id)

        impl = self._implementations.get(agent_id)
        context = await self._create_context(instance)

        return await self._executor.execute(
            agent_id, task, agent=impl, context=context,
        )

    async def heartbeat(
        self, agent_id: str, status: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send heartbeat for an agent."""
        if status is None:
            status = {
                "status": "running",
                "cpu": 0.0,
                "memory": 0.0,
                "task_progress": 0.0,
                "current_activity": "idle",
            }

        await self._heartbeat.send(agent_id, status)

        instance = self._get_agent(agent_id)
        instance.last_heartbeat = time.time()

        return await self._heartbeat.check(agent_id)

    async def health(self, agent_id: str) -> dict[str, Any]:
        """Get health status of an agent."""
        instance = self._get_agent(agent_id)
        hb = await self._heartbeat.check(agent_id)

        # Get implementation health
        impl_health = {}
        if agent_id in self._implementations:
            try:
                impl_health = await self._implementations[agent_id].health()
            except Exception:
                impl_health = {"status": "error"}

        return {
            "agent_id": agent_id,
            "state": instance.state.value,
            "heartbeat": hb,
            "implementation_health": impl_health,
            "uptime": time.time() - (instance.started_at or instance.created_at),
        }

    async def recover(self, agent_id: str) -> None:
        """Attempt to recover a failed agent."""
        instance = self._get_agent(agent_id)
        sm = self._get_state_machine(agent_id)

        if instance.state != AgentState.FAILED:
            return

        logger.info("agent_recovery_attempt", agent_id=agent_id)

        # Force state to created for retry
        sm.force_state(AgentState.CREATED, "recovery")
        instance.state = AgentState.CREATED
        instance.error = None

        # Re-initialize
        await self.initialize(agent_id)

        await self._emit(AgentRecovered(agent_id=agent_id))
        logger.info("agent_recovered", agent_id=agent_id)

    async def get(self, agent_id: str) -> AgentInstance | None:
        """Get an agent instance."""
        return self._agents.get(agent_id)

    async def list_active(self) -> list[dict[str, Any]]:
        """List all active agents."""
        return [
            inst.to_dict()
            for inst in self._agents.values()
        ]

    async def find_agents_for_capability(
        self, capability: str
    ) -> list[dict[str, Any]]:
        """Find agents that can perform a capability."""
        agent_types = self._capabilities.find(capability)
        result = []
        for inst in self._agents.values():
            if inst.agent_type in agent_types:
                result.append(inst.to_dict())
        return result

    def get_registry(self) -> AgentRegistry:
        """Get the agent registry."""
        return self._registry

    def get_capabilities(self) -> CapabilityRegistry:
        """Get the capability registry."""
        return self._capabilities

    def get_resources(self) -> ResourceTracker:
        """Get the resource tracker."""
        return self._resources

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _get_agent(self, agent_id: str) -> AgentInstance:
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        return self._agents[agent_id]

    def _get_state_machine(self, agent_id: str) -> AgentStateMachine:
        if agent_id not in self._state_machines:
            raise AgentNotFoundError(agent_id)
        return self._state_machines[agent_id]

    async def _create_context(
        self, instance: AgentInstance
    ) -> ExecutionContext:
        caps = instance.metadata.capabilities or []
        return ExecutionContext(
            config=instance.config.settings,
            capabilities=caps,
        )

    async def _emit(self, event: AgentEvent) -> None:
        if self._event_handler:
            try:
                result = self._event_handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(
                    "agent_event_error",
                    error=str(e),
                    event_type=type(event).__name__,
                )

    async def _emit_event(self, event: AgentEvent) -> None:
        await self._emit(event)

    async def shutdown(self) -> None:
        """Shutdown all agents."""
        agent_ids = list(self._agents.keys())
        for agent_id in agent_ids:
            try:
                await self.destroy(agent_id)
            except Exception as e:
                logger.error(
                    "agent_shutdown_error",
                    agent_id=agent_id,
                    error=str(e),
                )

        await self._heartbeat.stop_monitoring()
        logger.info("agent_manager_shutdown")
