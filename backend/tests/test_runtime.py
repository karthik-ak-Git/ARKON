"""ARKON Runtime Tests.

Comprehensive tests for the Agent Runtime system.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import time

import pytest

os.environ.setdefault("ARKON_ENV", "test")

from app.runtime.agent import AgentConfig, AgentInstance, AgentMetadata
from app.runtime.capabilities import CapabilityRegistry
from app.runtime.events import AgentCreated, AgentHeartbeat, EVENT_TYPES
from app.runtime.exceptions import (
    AgentAlreadyRunningError,
    AgentCreateError,
    AgentExecutionError,
    AgentNotFoundError,
    AgentNotRunningError,
    AgentTimeoutError,
    InvalidStateTransitionError,
)
from app.runtime.executor import AgentExecutor
from app.runtime.heartbeat import HeartbeatManager
from app.runtime.interfaces import AgentState, VALID_TRANSITIONS
from app.runtime.manager import AgentManager
from app.runtime.registry import AgentRegistry
from app.runtime.resources import ResourceProfile, ResourceTracker, ResourceUsage
from app.runtime.sandbox import SandboxManager
from app.runtime.state_machine import AgentStateMachine


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def state_machine() -> AgentStateMachine:
    return AgentStateMachine()


@pytest.fixture
def agent_config() -> AgentConfig:
    return AgentConfig(
        max_retries=3,
        timeout=30.0,
        heartbeat_interval=5.0,
        auto_restart=True,
        priority=0,
        settings={},
    )


@pytest.fixture
def agent_metadata() -> AgentMetadata:
    return AgentMetadata(
        agent_type="test_agent",
        name="Test Agent",
        version="1.0.0",
        author="Test",
        capabilities=["test"],
        required_resources={"cpu": 1.0, "ram": 256.0},
        supported_models=["gpt-4"],
        priority=0,
        dependencies=[],
        tags=["test"],
    )


@pytest.fixture
def capability_registry() -> CapabilityRegistry:
    return CapabilityRegistry()


@pytest.fixture
def resource_tracker() -> ResourceTracker:
    return ResourceTracker()


@pytest.fixture
def heartbeat_manager() -> HeartbeatManager:
    return HeartbeatManager(timeout=5.0)


@pytest.fixture
def agent_executor() -> AgentExecutor:
    return AgentExecutor()


@pytest.fixture
def agent_registry() -> AgentRegistry:
    return AgentRegistry()


@pytest.fixture
def tmp_sandbox() -> str:
    path = tempfile.mkdtemp(prefix="arkon_runtime_test_")
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def sandbox_manager(tmp_sandbox: str) -> SandboxManager:
    return SandboxManager(base_path=tmp_sandbox)


@pytest.fixture
async def agent_manager(tmp_sandbox: str) -> AgentManager:
    mgr = AgentManager(base_path=tmp_sandbox)
    yield mgr
    await mgr.shutdown()


# =============================================================================
# State Machine Tests
# =============================================================================


class TestStateMachine:
    """Agent state machine tests."""

    def test_initial_state(self, state_machine: AgentStateMachine) -> None:
        assert state_machine.state.value == "created"

    def test_valid_transitions(self, state_machine: AgentStateMachine) -> None:
        state_machine.transition(AgentState.INITIALIZING)
        assert state_machine.state.value == "initializing"

        state_machine.transition(AgentState.READY)
        assert state_machine.state.value == "ready"

        state_machine.transition(AgentState.RUNNING)
        assert state_machine.state.value == "running"

        state_machine.transition(AgentState.PAUSED)
        assert state_machine.state.value == "paused"

        state_machine.transition(AgentState.RUNNING)
        assert state_machine.state.value == "running"

        state_machine.transition(AgentState.COMPLETED)
        assert state_machine.state.value == "completed"

    def test_invalid_transition(self, state_machine: AgentStateMachine) -> None:
        with pytest.raises(InvalidStateTransitionError):
            state_machine.transition(AgentState.COMPLETED)

    def test_force_state(self, state_machine: AgentStateMachine) -> None:
        state_machine.force_state(AgentState.RUNNING)
        assert state_machine.state.value == "running"

    def test_can_transition(self, state_machine: AgentStateMachine) -> None:
        assert state_machine.can_transition(AgentState.INITIALIZING) is True
        assert state_machine.can_transition(AgentState.RUNNING) is False

    def test_history(self, state_machine: AgentStateMachine) -> None:
        state_machine.transition(AgentState.INITIALIZING)
        state_machine.transition(AgentState.READY)
        history = state_machine.history
        assert len(history) == 2
        assert history[0].to_state.value == "initializing"
        assert history[1].to_state.value == "ready"

    def test_reset(self, state_machine: AgentStateMachine) -> None:
        state_machine.transition(AgentState.INITIALIZING)
        state_machine.reset()
        assert state_machine.state.value == "created"

    def test_transition_count(self, state_machine: AgentStateMachine) -> None:
        state_machine.transition(AgentState.INITIALIZING)
        state_machine.transition(AgentState.READY)
        assert state_machine.transition_count == 2

    def test_to_dict(self, state_machine: AgentStateMachine) -> None:
        state_machine.transition(AgentState.INITIALIZING)
        d = state_machine.to_dict()
        assert d["state"] == "initializing"
        assert d["transition_count"] == 1


# =============================================================================
# Agent Data Model Tests
# =============================================================================


class TestAgentData:
    """Agent data model tests."""

    def test_create_config(self, agent_config: AgentConfig) -> None:
        assert agent_config.max_retries == 3
        assert agent_config.timeout == 30.0

    def test_config_from_dict(self) -> None:
        config = AgentConfig.from_dict({"max_retries": 5, "timeout": 60.0})
        assert config.max_retries == 5
        assert config.timeout == 60.0

    def test_create_metadata(self, agent_metadata: AgentMetadata) -> None:
        assert agent_metadata.agent_type == "test_agent"
        assert "test" in agent_metadata.capabilities

    def test_metadata_from_dict(self) -> None:
        meta = AgentMetadata.from_dict({"agent_type": "x", "name": "X"})
        assert meta.agent_type == "x"

    def test_agent_to_dict(self, agent_config: AgentConfig, agent_metadata: AgentMetadata) -> None:
        agent = AgentInstance(
            agent_type="test_agent",
            name="Test",
            config=agent_config,
            metadata=agent_metadata,
        )
        d = agent.to_dict()
        assert "id" in d
        assert d["state"] == "created"
        assert d["agent_type"] == "test_agent"

    def test_agent_from_dict(self) -> None:
        agent = AgentInstance.from_dict({
            "id": "test-1",
            "agent_type": "x",
            "name": "X",
            "state": "running",
        })
        assert agent.id == "test-1"
        assert agent.state == AgentState.RUNNING


# =============================================================================
# Capability Registry Tests
# =============================================================================


class TestCapabilityRegistry:
    """Capability registry tests."""

    def test_register(self, capability_registry: CapabilityRegistry) -> None:
        capability_registry.register("test_cap", "agent_1")
        assert capability_registry.find("test_cap") == ["agent_1"]

    def test_find_unknown(self, capability_registry: CapabilityRegistry) -> None:
        assert capability_registry.find("unknown") == []

    def test_find_by_any(self, capability_registry: CapabilityRegistry) -> None:
        capability_registry.register("cap_a", "a")
        capability_registry.register("cap_b", "b")
        result = capability_registry.find_agents_with_any(["cap_a", "cap_c"])
        assert "a" in result

    def test_find_by_all(self, capability_registry: CapabilityRegistry) -> None:
        capability_registry.register("cap_a", "a")
        capability_registry.register("cap_a", "b")
        capability_registry.register("cap_b", "b")
        result = capability_registry.find_agents_with_all(["cap_a", "cap_b"])
        assert result == ["b"]

    def test_unregister(self, capability_registry: CapabilityRegistry) -> None:
        capability_registry.register("test", "a")
        capability_registry.unregister("test", "a")
        assert capability_registry.find("test") == []

    def test_to_dict(self, capability_registry: CapabilityRegistry) -> None:
        capability_registry.register("c", "x")
        d = capability_registry.to_dict()
        assert "c" in d


# =============================================================================
# Resource Tracker Tests
# =============================================================================


class TestResourceTracker:
    """Resource tracker tests."""

    def test_register_profile(self, resource_tracker: ResourceTracker) -> None:
        profile = ResourceProfile(cpu=2.0, ram=512.0)
        resource_tracker.register_profile("agent-1", profile)
        assert resource_tracker._profiles["agent-1"] == profile

    def test_update_usage(self, resource_tracker: ResourceTracker) -> None:
        usage = ResourceUsage(agent_id="agent-1", cpu=1.0, ram=256.0)
        resource_tracker.update_usage(usage)
        assert resource_tracker._usage["agent-1"].cpu == 1.0

    def test_can_allocate(self, resource_tracker: ResourceTracker) -> None:
        profile = ResourceProfile(cpu=1.0, ram=256.0)
        assert resource_tracker.can_allocate(profile) is True

    def test_cannot_allocate(self, resource_tracker: ResourceTracker) -> None:
        resource_tracker.update_usage(ResourceUsage(agent_id="a", cpu=8.0, ram=16384.0))
        profile = ResourceProfile(cpu=1.0, ram=256.0)
        assert resource_tracker.can_allocate(profile) is False

    def test_get_available(self, resource_tracker: ResourceTracker) -> None:
        avail = resource_tracker.get_available()
        assert avail["cpu"] > 0
        assert avail["ram"] > 0

    def test_to_dict(self, resource_tracker: ResourceTracker) -> None:
        d = resource_tracker.to_dict()
        assert "total" in d
        assert "available" in d
        assert "allocated" in d

    def test_remove_usage(self, resource_tracker: ResourceTracker) -> None:
        resource_tracker.update_usage(ResourceUsage(agent_id="a", cpu=1.0))
        resource_tracker.remove_usage("a")
        assert resource_tracker.get_usage("a") is None

    def test_get_total_usage(self, resource_tracker: ResourceTracker) -> None:
        resource_tracker.update_usage(ResourceUsage(agent_id="a", cpu=1.0, ram=100.0))
        resource_tracker.update_usage(ResourceUsage(agent_id="b", cpu=2.0, ram=200.0))
        total = resource_tracker.get_total_usage()
        assert total.cpu == 3.0
        assert total.ram == 300.0


# =============================================================================
# Heartbeat Tests
# =============================================================================


class TestHeartbeat:
    """Heartbeat manager tests."""

    @pytest.mark.asyncio
    async def test_send_heartbeat(self, heartbeat_manager: HeartbeatManager) -> None:
        await heartbeat_manager.send("agent-1", {"status": "running"})
        hb = await heartbeat_manager.check("agent-1")
        assert hb is not None
        assert hb["status"] == "running"
        assert hb["has_heartbeat"] is True

    @pytest.mark.asyncio
    async def test_check_no_heartbeat(self, heartbeat_manager: HeartbeatManager) -> None:
        hb = await heartbeat_manager.check("nonexistent")
        assert hb["has_heartbeat"] is False
        assert hb["expired"] is True

    @pytest.mark.asyncio
    async def test_expired_heartbeat(self, heartbeat_manager: HeartbeatManager) -> None:
        heartbeat_manager._timeout = 0.01
        await heartbeat_manager.send("agent-1", {"status": "running"})
        await asyncio.sleep(0.02)
        hb = await heartbeat_manager.check("agent-1")
        assert hb["expired"] is True
        assert hb["healthy"] is False

    @pytest.mark.asyncio
    async def test_remove_heartbeat(self, heartbeat_manager: HeartbeatManager) -> None:
        await heartbeat_manager.send("agent-1", {"status": "running"})
        await heartbeat_manager.remove("agent-1")
        hb = await heartbeat_manager.check("agent-1")
        assert hb["has_heartbeat"] is False

    @pytest.mark.asyncio
    async def test_check_all(self, heartbeat_manager: HeartbeatManager) -> None:
        await heartbeat_manager.send("a", {"status": "running"})
        await heartbeat_manager.send("b", {"status": "running"})
        results = await heartbeat_manager.check_all()
        assert len(results) == 2

    def test_to_dict(self, heartbeat_manager: HeartbeatManager) -> None:
        d = heartbeat_manager.to_dict()
        assert "timeout" in d
        assert "monitoring" in d


# =============================================================================
# Sandbox Tests
# =============================================================================


class TestSandbox:
    """Sandbox manager tests."""

    @pytest.mark.asyncio
    async def test_create_sandbox(self, sandbox_manager: SandboxManager) -> None:
        sandbox_id = await sandbox_manager.create("agent-1")
        assert sandbox_id is not None
        path = sandbox_manager.get_path(sandbox_id)
        assert os.path.exists(path)

    @pytest.mark.asyncio
    async def test_set_env(self, sandbox_manager: SandboxManager) -> None:
        sandbox_id = await sandbox_manager.create("agent-1")
        await sandbox_manager.set_env(sandbox_id, "MY_VAR", "value")
        val = await sandbox_manager.get_env(sandbox_id, "MY_VAR")
        assert val == "value"

    @pytest.mark.asyncio
    async def test_destroy_sandbox(self, sandbox_manager: SandboxManager) -> None:
        sandbox_id = await sandbox_manager.create("agent-1")
        await sandbox_manager.destroy(sandbox_id)
        assert sandbox_manager.get_sandbox(sandbox_id) is None

    @pytest.mark.asyncio
    async def test_list_active(self, sandbox_manager: SandboxManager) -> None:
        await sandbox_manager.create("a")
        await sandbox_manager.create("b")
        active = await sandbox_manager.list_active()
        assert len(active) == 2

    def test_to_dict(self, sandbox_manager: SandboxManager) -> None:
        d = sandbox_manager.to_dict()
        assert "base_path" in d
        assert "active_count" in d

    @pytest.mark.asyncio
    async def test_get_temp_path(self, sandbox_manager: SandboxManager) -> None:
        sandbox_id = await sandbox_manager.create("agent-1")
        temp = sandbox_manager.get_temp_path(sandbox_id)
        assert os.path.exists(temp)


# =============================================================================
# Executor Tests
# =============================================================================


class TestExecutor:
    """Agent executor tests."""

    @pytest.mark.asyncio
    async def test_execute_no_agent(self, agent_executor: AgentExecutor) -> None:
        with pytest.raises(AgentExecutionError):
            await agent_executor.execute("agent-1", {"type": "test", "payload": {}})

    @pytest.mark.asyncio
    async def test_execute_with_mock_agent(self, agent_executor: AgentExecutor) -> None:
        from unittest.mock import AsyncMock

        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {"result": "ok"}

        result = await agent_executor.execute(
            "agent-1",
            {"type": "test", "payload": {}},
            agent=mock_agent,
        )
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_get_status(self, agent_executor: AgentExecutor) -> None:
        status = await agent_executor.get_status("nonexistent")
        assert status["total_tasks"] == 0


# =============================================================================
# Registry Tests
# =============================================================================


class TestRegistry:
    """Agent registry tests."""

    @pytest.mark.asyncio
    async def test_register(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register("test_agent", {"name": "Test", "capabilities": ["test"]})
        entry = await agent_registry.get("test_agent")
        assert entry is not None
        assert entry["name"] == "Test"

    @pytest.mark.asyncio
    async def test_get_unknown(self, agent_registry: AgentRegistry) -> None:
        entry = await agent_registry.get("unknown")
        assert entry is None

    @pytest.mark.asyncio
    async def test_list_all(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register("a", {"name": "A"})
        await agent_registry.register("b", {"name": "B"})
        all_agents = await agent_registry.list_all()
        assert len(all_agents) >= 2

    @pytest.mark.asyncio
    async def test_unregister(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register("c", {"name": "C"})
        await agent_registry.unregister("c")
        entry = await agent_registry.get("c")
        assert entry is None

    def test_count(self, agent_registry: AgentRegistry) -> None:
        assert agent_registry.count() == 0

    def test_exists(self, agent_registry: AgentRegistry) -> None:
        assert agent_registry.exists("x") is False

    @pytest.mark.asyncio
    async def test_find_by_capability(self, agent_registry: AgentRegistry) -> None:
        await agent_registry.register("a", {"capabilities": ["vision"]})
        result = await agent_registry.find_by_capability("vision")
        assert len(result) == 1


# =============================================================================
# Manager Integration Tests
# =============================================================================


class TestManager:
    """AgentManager integration tests."""

    @pytest.mark.asyncio
    async def test_spawn(self, agent_manager: AgentManager) -> None:
        agent_id = await agent_manager.spawn("test_agent", "Test", config={"key": "value"})
        assert agent_id is not None
        agent = await agent_manager.get(agent_id)
        assert agent is not None
        assert agent.name == "Test"

    @pytest.mark.asyncio
    async def test_initialize_start_stop(self, agent_manager: AgentManager) -> None:
        agent_id = await agent_manager.spawn("test_agent", "Test")
        await agent_manager.initialize(agent_id)
        await agent_manager.start(agent_id)

        agent = await agent_manager.get(agent_id)
        assert agent.state.value == "running"

        await agent_manager.stop(agent_id)
        agent = await agent_manager.get(agent_id)
        assert agent.state.value == "stopped"

    @pytest.mark.asyncio
    async def test_pause_resume(self, agent_manager: AgentManager) -> None:
        agent_id = await agent_manager.spawn("test_agent", "Test")
        await agent_manager.initialize(agent_id)
        await agent_manager.start(agent_id)

        await agent_manager.pause(agent_id)
        agent = await agent_manager.get(agent_id)
        assert agent.state.value == "paused"

        await agent_manager.resume(agent_id)
        agent = await agent_manager.get(agent_id)
        assert agent.state.value == "running"

    @pytest.mark.asyncio
    async def test_destroy(self, agent_manager: AgentManager) -> None:
        agent_id = await agent_manager.spawn("test_agent", "Test")
        await agent_manager.destroy(agent_id)
        agent = await agent_manager.get(agent_id)
        assert agent is None

    @pytest.mark.asyncio
    async def test_list_active(self, agent_manager: AgentManager) -> None:
        await agent_manager.spawn("test_agent", "A")
        await agent_manager.spawn("test_agent", "B")
        active = await agent_manager.list_active()
        assert len(active) >= 2

    @pytest.mark.asyncio
    async def test_health(self, agent_manager: AgentManager) -> None:
        agent_id = await agent_manager.spawn("test_agent", "Test")
        await agent_manager.initialize(agent_id)
        await agent_manager.start(agent_id)
        health = await agent_manager.health(agent_id)
        assert "state" in health
        assert "uptime" in health

    @pytest.mark.asyncio
    async def test_heartbeat(self, agent_manager: AgentManager) -> None:
        agent_id = await agent_manager.spawn("test_agent", "Test")
        await agent_manager.initialize(agent_id)
        await agent_manager.start(agent_id)
        hb = await agent_manager.heartbeat(agent_id)
        assert "status" in hb
        assert hb["has_heartbeat"] is True

    @pytest.mark.asyncio
    async def test_register_agent_type(self, agent_manager: AgentManager) -> None:
        await agent_manager.register_agent_type("typed_agent", {
            "name": "Typed Agent",
            "capabilities": ["vision"],
        })
        entry = await agent_manager.get_registry().get("typed_agent")
        assert entry is not None
