"""ARKON Execution Engine Tests.

Comprehensive tests for the execution pipeline.
"""

from __future__ import annotations

import asyncio
import os

import pytest

os.environ.setdefault("ARKON_ENV", "test")

from app.execution.interfaces import (
    TaskState,
    TASK_TRANSITIONS,
    RetryPolicy,
    CheckpointPolicy,
)
from app.execution.exceptions import (
    TaskAlreadyExistsError,
    TaskNotFoundError,
    DispatchError,
    CircularDependencyError,
)
from app.execution.task import Task, RetryConfig, CheckpointConfig
from app.execution.task_context import TaskContext
from app.execution.dependency_graph import DependencyGraph
from app.execution.queue import TaskQueue
from app.execution.dispatcher import TaskDispatcher
from app.execution.executor import TaskExecutor
from app.execution.engine import ExecutionEngine
from app.execution.cancellation import CancellationManager
from app.execution.progress import ProgressTracker
from app.execution.results import ResultStore, TaskResult
from app.execution.checkpoint import CheckpointManager
from app.execution.recovery import RecoveryManager
from app.execution.retry import RetryManager


# =============================================================================
# TaskState Tests
# =============================================================================


class TestTaskState:
    """Tests for TaskState enum."""

    def test_all_states_exist(self):
        expected = [
            "created", "queued", "dispatched", "executing", "waiting",
            "completed", "failed", "cancelled", "timed_out",
            "recovering", "paused",
        ]
        actual = [s.value for s in TaskState]
        assert sorted(actual) == sorted(expected)

    def test_state_count(self):
        assert len(TaskState) == 11

    def test_transitions_defined_for_all_states(self):
        for state in TaskState:
            assert state in TASK_TRANSITIONS

    def test_valid_transition(self):
        assert "queued" in TASK_TRANSITIONS[TaskState.CREATED]
        assert "executing" in TASK_TRANSITIONS[TaskState.DISPATCHED]
        assert "completed" in TASK_TRANSITIONS[TaskState.EXECUTING]

    def test_invalid_transition_not_in_map(self):
        # COMPLETED has no outgoing transitions
        assert TASK_TRANSITIONS[TaskState.COMPLETED] == set()


# =============================================================================
# Task Tests
# =============================================================================


class TestTask:
    """Tests for Task dataclass."""

    def test_create_task(self):
        task = Task(capability="test")
        assert task.get_id() is not None
        assert task.get_capability() == "test"
        assert task.get_state() == TaskState.CREATED
        assert task.get_priority() == 0

    def test_task_with_priority(self):
        task = Task(capability="test", priority=5)
        assert task.get_priority() == 5

    def test_task_with_payload(self):
        task = Task(capability="test", payload={"key": "value"})
        assert task.get_payload() == {"key": "value"}

    def test_task_set_state(self):
        task = Task(capability="test")
        task.state = TaskState.QUEUED
        assert task.get_state() == TaskState.QUEUED

    def test_task_dependencies(self):
        task = Task(capability="test", dependencies=["dep1", "dep2"])
        deps = task.get_dependencies()
        assert "dep1" in deps
        assert "dep2" in deps

    def test_task_timeout(self):
        task = Task(capability="test", timeout=30.0)
        assert task.get_timeout() == 30.0

    def test_task_is_terminal(self):
        task = Task(capability="test")
        assert task.is_terminal() is False
        task.state = TaskState.COMPLETED
        assert task.is_terminal() is True

    def test_task_duration(self):
        task = Task(capability="test")
        assert task.duration() is None
        task.started_at = 100.0
        task.completed_at = 105.0
        assert task.duration() == 5.0

    def test_task_roundtrip(self):
        task = Task(
            capability="test",
            payload={"key": "value"},
            priority=3,
            dependencies=["dep1"],
            timeout=30.0,
        )
        d = task.to_dict()
        restored = Task.from_dict(d)
        assert restored.capability == "test"
        assert restored.payload == {"key": "value"}
        assert restored.priority == 3
        assert restored.dependencies == ["dep1"]
        assert restored.timeout == 30.0


# =============================================================================
# RetryConfig / CheckpointConfig Tests
# =============================================================================


class TestConfigs:
    """Tests for configuration dataclasses."""

    def test_retry_config_defaults(self):
        cfg = RetryConfig()
        assert cfg.policy == RetryPolicy.IMMEDIATE
        assert cfg.max_retries == 3

    def test_retry_config_roundtrip(self):
        cfg = RetryConfig(policy=RetryPolicy.EXPONENTIAL_BACKOFF, max_retries=5)
        d = cfg.to_dict()
        restored = RetryConfig.from_dict(d)
        assert restored.policy == RetryPolicy.EXPONENTIAL_BACKOFF
        assert restored.max_retries == 5

    def test_checkpoint_config_defaults(self):
        cfg = CheckpointConfig()
        assert cfg.policy == CheckpointPolicy.MANUAL

    def test_checkpoint_config_roundtrip(self):
        cfg = CheckpointConfig(policy=CheckpointPolicy.PERIODIC, interval=60.0)
        d = cfg.to_dict()
        restored = CheckpointConfig.from_dict(d)
        assert restored.policy == CheckpointPolicy.PERIODIC
        assert restored.interval == 60.0


# =============================================================================
# TaskContext Tests
# =============================================================================


class TestTaskContext:
    """Tests for TaskContext."""

    def test_create_context(self):
        ctx = TaskContext(task_id="t1")
        assert ctx.task_id == "t1"
        assert ctx.is_cancelled() is False

    def test_cancel(self):
        ctx = TaskContext(task_id="t1")
        ctx.cancel()
        assert ctx.is_cancelled() is True

    def test_progress(self):
        ctx = TaskContext(task_id="t1")
        ctx.update_progress(50.0, "step1")
        progress = ctx.get_progress()
        assert progress["progress"] == 50.0
        assert progress["current_step"] == "step1"

    def test_intermediate_results(self):
        ctx = TaskContext(task_id="t1")
        ctx.set_result("key1", "value1")
        ctx.set_result("key2", "value2")
        assert ctx.get_result("key1") == "value1"
        assert ctx.get_result("key2") == "value2"

    def test_to_dict(self):
        ctx = TaskContext(task_id="t1")
        d = ctx.to_dict()
        assert d["task_id"] == "t1"

    def test_from_dict(self):
        ctx = TaskContext(task_id="t1")
        ctx._cancelled = True
        d = ctx.to_dict()
        restored = TaskContext.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.is_cancelled() is True


# =============================================================================
# DependencyGraph Tests
# =============================================================================


class TestDependencyGraph:
    """Tests for DependencyGraph."""

    def test_add_node(self):
        graph = DependencyGraph()
        graph.add_node("t1")
        assert "t1" in graph.to_dict()["nodes"]

    def test_add_dependency(self):
        graph = DependencyGraph()
        graph.add_dependency("t1", "t2")  # t1 depends on t2
        deps = graph.get_dependencies("t1")
        assert "t2" in deps

    def test_cycle_detection(self):
        graph = DependencyGraph()
        graph.add_dependency("t1", "t2")
        with pytest.raises(CircularDependencyError):
            graph.add_dependency("t2", "t1")

    def test_ready_tasks(self):
        graph = DependencyGraph()
        graph.add_dependency("t1", "t2")  # t1 depends on t2
        ready = graph.get_ready_tasks(completed=set())
        assert "t2" in ready
        assert "t1" not in ready

    def test_ready_tasks_after_completion(self):
        graph = DependencyGraph()
        graph.add_dependency("t1", "t2")
        ready = graph.get_ready_tasks(completed={"t2"})
        assert "t1" in ready

    def test_topological_sort(self):
        graph = DependencyGraph()
        graph.add_dependency("t1", "t2")
        graph.add_dependency("t2", "t3")
        order = graph.topological_sort()
        assert order.index("t3") < order.index("t2")
        assert order.index("t2") < order.index("t1")

    def test_size(self):
        graph = DependencyGraph()
        graph.add_node("t1")
        graph.add_node("t2")
        assert graph.size() == 2

    def test_remove_node(self):
        graph = DependencyGraph()
        graph.add_dependency("t1", "t2")
        graph.remove_node("t2")
        assert "t2" not in graph.to_dict()["nodes"]

    def test_validate(self):
        graph = DependencyGraph()
        graph.add_dependency("t1", "t2")
        errors = graph.validate()
        assert len(errors) == 0

    def test_has_cycle(self):
        graph = DependencyGraph()
        assert graph.has_cycle() is False
        graph.add_dependency("t1", "t2")
        assert graph.has_cycle() is False


# =============================================================================
# TaskQueue Tests
# =============================================================================


class TestTaskQueue:
    """Tests for TaskQueue."""

    @pytest.fixture
    def queue(self):
        return TaskQueue()

    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self, queue):
        task = Task(capability="test")
        await queue.enqueue(task)
        assert await queue.size() == 1

        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.get_id() == task.get_id()
        assert await queue.size() == 0

    @pytest.mark.asyncio
    async def test_priority_ordering(self, queue):
        t1 = Task(capability="test", priority=5)
        t2 = Task(capability="test", priority=1)
        await queue.enqueue(t1)
        await queue.enqueue(t2)

        first = await queue.dequeue()
        assert first.get_priority() == 1  # Higher priority (lower number)

    @pytest.mark.asyncio
    async def test_peek(self, queue):
        task = Task(capability="test")
        await queue.enqueue(task)
        peeked = await queue.peek()
        assert peeked.get_id() == task.get_id()
        assert await queue.size() == 1  # Still in queue

    @pytest.mark.asyncio
    async def test_remove(self, queue):
        task = Task(capability="test")
        await queue.enqueue(task)
        removed = await queue.remove(task.get_id())
        assert removed is True
        assert await queue.size() == 0

    @pytest.mark.asyncio
    async def test_is_empty(self, queue):
        assert await queue.is_empty() is True
        await queue.enqueue(Task(capability="test"))
        assert await queue.is_empty() is False


# =============================================================================
# TaskDispatcher Tests
# =============================================================================


class TestTaskDispatcher:
    """Tests for TaskDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        return TaskDispatcher()

    @pytest.mark.asyncio
    async def test_register_and_dispatch(self, dispatcher):
        async def handler(task):
            return {"result": "ok"}

        dispatcher.register_handler("test", handler)
        assert dispatcher.has_handler("test")

        task = Task(capability="test")
        result = await dispatcher.dispatch(task)
        assert result["result"] == "ok"

    @pytest.mark.asyncio
    async def test_dispatch_no_handler(self, dispatcher):
        task = Task(capability="unknown")
        with pytest.raises(DispatchError):
            await dispatcher.dispatch(task)

    @pytest.mark.asyncio
    async def test_dispatch_handler_error(self, dispatcher):
        async def bad_handler(task):
            raise ValueError("boom")

        dispatcher.register_handler("bad", bad_handler)
        task = Task(capability="bad")
        with pytest.raises(DispatchError):
            await dispatcher.dispatch(task)

    def test_unregister_handler(self, dispatcher):
        async def handler(task):
            return {}

        dispatcher.register_handler("test", handler)
        assert dispatcher.unregister_handler("test") is True
        assert dispatcher.has_handler("test") is False

    def test_get_registered_capabilities(self, dispatcher):
        async def h1(task): return {}
        async def h2(task): return {}
        dispatcher.register_handler("cap1", h1)
        dispatcher.register_handler("cap2", h2)
        caps = dispatcher.get_registered_capabilities()
        assert "cap1" in caps
        assert "cap2" in caps


# =============================================================================
# TaskExecutor Tests
# =============================================================================


class TestTaskExecutor:
    """Tests for TaskExecutor."""

    @pytest.fixture
    def executor(self):
        return TaskExecutor()

    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        task = Task(capability="test")

        async def handler(t):
            return {"done": True}

        result = await executor.execute(task, handler)
        assert result["success"] is True
        assert result["output"]["done"] is True
        assert task.get_state() == TaskState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_failure(self, executor):
        task = Task(capability="test")

        async def handler(t):
            raise RuntimeError("failed")

        with pytest.raises(RuntimeError):
            await executor.execute(task, handler)
        assert task.get_state() == TaskState.FAILED

    def test_is_executing(self, executor):
        assert executor.is_executing("nonexistent") is False


# =============================================================================
# CancellationManager Tests
# =============================================================================


class TestCancellationManager:
    """Tests for CancellationManager."""

    @pytest.fixture
    def cancellation(self):
        return CancellationManager()

    def test_request_cancellation(self, cancellation):
        record = cancellation.request_cancellation("t1", "test reason")
        assert record["task_id"] == "t1"
        assert record["reason"] == "test reason"
        assert cancellation.is_cancelled("t1") is True

    def test_acknowledge_cancellation(self, cancellation):
        cancellation.request_cancellation("t1")
        cancellation.acknowledge_cancellation("t1")
        assert cancellation.is_cancelled("t1") is False

    def test_get_cancelled_tasks(self, cancellation):
        cancellation.request_cancellation("t1")
        cancellation.request_cancellation("t2")
        cancelled = cancellation.get_cancelled_tasks()
        assert "t1" in cancelled
        assert "t2" in cancelled

    @pytest.mark.asyncio
    async def test_cleanup_callbacks(self, cancellation):
        called = []

        def cleanup():
            called.append(True)

        cancellation.register_cleanup("t1", cleanup)
        await cancellation.execute_cleanup("t1")
        assert len(called) == 1

    def test_get_history(self, cancellation):
        cancellation.request_cancellation("t1", "reason1")
        cancellation.request_cancellation("t2", "reason2")
        history = cancellation.get_history()
        assert len(history) == 2

        t1_history = cancellation.get_history(task_id="t1")
        assert len(t1_history) == 1


# =============================================================================
# ProgressTracker Tests
# =============================================================================


class TestProgressTracker:
    """Tests for ProgressTracker."""

    @pytest.fixture
    def tracker(self):
        return ProgressTracker()

    def test_start_tracking(self, tracker):
        tracker.start_tracking("t1")
        assert tracker.is_tracking("t1") is True

    def test_update_progress(self, tracker):
        tracker.start_tracking("t1")
        update = tracker.update("t1", 50.0, "step1", "Halfway")
        assert update.progress == 50.0
        assert update.current_step == "step1"

    def test_get_progress(self, tracker):
        tracker.start_tracking("t1")
        tracker.update("t1", 75.0, "step2", "Almost done")
        progress = tracker.get_progress("t1")
        assert progress["progress"] == 75.0
        assert progress["current_step"] == "step2"

    def test_progress_clamped(self, tracker):
        tracker.start_tracking("t1")
        tracker.update("t1", 150.0)
        progress = tracker.get_progress("t1")
        assert progress["progress"] == 100.0

    def test_stop_tracking(self, tracker):
        tracker.start_tracking("t1")
        tracker.stop_tracking("t1")
        assert tracker.is_tracking("t1") is False

    def test_get_history(self, tracker):
        tracker.start_tracking("t1")
        tracker.update("t1", 25.0)
        tracker.update("t1", 50.0)
        tracker.update("t1", 75.0)
        history = tracker.get_history("t1")
        assert len(history) == 3


# =============================================================================
# ResultStore Tests
# =============================================================================


class TestResultStore:
    """Tests for ResultStore."""

    @pytest.fixture
    def store(self):
        return ResultStore()

    def test_store_and_get(self, store):
        result = TaskResult(task_id="t1", success=True, output={"key": "value"})
        store.store(result)
        retrieved = store.get("t1")
        assert retrieved is not None
        assert retrieved.output == {"key": "value"}

    def test_exists(self, store):
        result = TaskResult(task_id="t1", success=True)
        store.store(result)
        assert store.exists("t1") is True
        assert store.exists("t2") is False

    def test_delete(self, store):
        result = TaskResult(task_id="t1", success=True)
        store.store(result)
        assert store.delete("t1") is True
        assert store.get("t1") is None

    def test_list_all(self, store):
        store.store(TaskResult(task_id="t1"))
        store.store(TaskResult(task_id="t2"))
        ids = store.list_all()
        assert "t1" in ids
        assert "t2" in ids

    def test_count(self, store):
        assert store.count() == 0
        store.store(TaskResult(task_id="t1"))
        assert store.count() == 1


# =============================================================================
# CheckpointManager Tests
# =============================================================================


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    @pytest.fixture
    def checkpoint_mgr(self):
        return CheckpointManager()

    def test_create_checkpoint(self, checkpoint_mgr):
        checkpoint = checkpoint_mgr.create_checkpoint("t1", state="executing")
        assert checkpoint.task_id == "t1"
        assert checkpoint.state == "executing"

    def test_get_checkpoint(self, checkpoint_mgr):
        cp = checkpoint_mgr.create_checkpoint("t1", state="executing")
        retrieved = checkpoint_mgr.get_checkpoint("t1", cp.checkpoint_id)
        assert retrieved is not None
        assert retrieved.state == "executing"

    def test_get_latest(self, checkpoint_mgr):
        checkpoint_mgr.create_checkpoint("t1", state="step1")
        checkpoint_mgr.create_checkpoint("t1", state="step2")
        latest = checkpoint_mgr.get_latest("t1")
        assert latest.state == "step2"

    def test_list_checkpoints(self, checkpoint_mgr):
        checkpoint_mgr.create_checkpoint("t1", state="step1")
        checkpoint_mgr.create_checkpoint("t1", state="step2")
        checkpoints = checkpoint_mgr.get_all("t1")
        assert len(checkpoints) == 2

    def test_delete_checkpoints(self, checkpoint_mgr):
        checkpoint_mgr.create_checkpoint("t1", state="step1")
        checkpoint_mgr.create_checkpoint("t1", state="step2")
        deleted = checkpoint_mgr.delete("t1")
        assert deleted == 2
        assert checkpoint_mgr.get_latest("t1") is None

    def test_should_checkpoint(self, checkpoint_mgr):
        # Manual policy never auto-checkpoints
        assert checkpoint_mgr.should_checkpoint(100.0) is False


# =============================================================================
# RecoveryManager Tests
# =============================================================================


class TestRecoveryManager:
    """Tests for RecoveryManager."""

    @pytest.fixture
    def recovery_mgr(self):
        checkpoint_mgr = CheckpointManager()
        return RecoveryManager(checkpoint_mgr)

    @pytest.mark.asyncio
    async def test_can_recover(self, recovery_mgr):
        can = await recovery_mgr.can_recover("t1")
        assert can is False

    @pytest.mark.asyncio
    async def test_recover_with_checkpoint(self, recovery_mgr):
        recovery_mgr._checkpoints.create_checkpoint("t1", state="executing")
        can = await recovery_mgr.can_recover("t1")
        assert can is True

        result = await recovery_mgr.recover("t1")
        assert result["task_id"] == "t1"
        assert result["restored_state"] == "executing"

    @pytest.mark.asyncio
    async def test_rollback(self, recovery_mgr):
        recovery_mgr._checkpoints.create_checkpoint("t1", state="step1")
        recovery_mgr._checkpoints.create_checkpoint("t1", state="step2")
        result = await recovery_mgr.rollback("t1")
        assert result["strategy"] == "rollback"

    def test_get_recovery_history(self, recovery_mgr):
        history = recovery_mgr.get_recovery_history()
        assert len(history) == 0


# =============================================================================
# RetryManager Tests
# =============================================================================


class TestRetryManager:
    """Tests for RetryManager."""

    @pytest.fixture
    def retry_mgr(self):
        return RetryManager()

    def test_should_retry(self, retry_mgr):
        should = retry_mgr.should_retry("t1", attempt=0, max_retries=3)
        assert should is True

    def test_max_retries_exceeded(self, retry_mgr):
        should = retry_mgr.should_retry("t1", attempt=3, max_retries=3)
        assert should is False

    def test_get_delay_immediate(self, retry_mgr):
        delay = retry_mgr.get_delay(RetryPolicy.IMMEDIATE, attempt=0)
        assert delay == 0.0

    def test_get_delay_fixed(self, retry_mgr):
        delay = retry_mgr.get_delay(RetryPolicy.FIXED_DELAY, attempt=0, base_delay=2.0)
        assert delay == 2.0

    def test_get_delay_exponential(self, retry_mgr):
        d0 = retry_mgr.get_delay(RetryPolicy.EXPONENTIAL_BACKOFF, attempt=0)
        d1 = retry_mgr.get_delay(RetryPolicy.EXPONENTIAL_BACKOFF, attempt=1)
        d2 = retry_mgr.get_delay(RetryPolicy.EXPONENTIAL_BACKOFF, attempt=2)
        assert d0 == 1.0
        assert d1 == 2.0
        assert d2 == 4.0

    def test_record_retry(self, retry_mgr):
        retry_mgr.record_retry("t1", attempt=1, error="timeout", delay=2.0)
        history = retry_mgr.get_history("t1")
        assert len(history) == 1
        assert history[0]["attempt"] == 1

    def test_clear_history(self, retry_mgr):
        retry_mgr.record_retry("t1", attempt=1, error="timeout", delay=2.0)
        retry_mgr.clear_history("t1")
        assert len(retry_mgr.get_history("t1")) == 0

    def test_custom_predicate(self, retry_mgr):
        def is_timeout(e):
            return isinstance(e, TimeoutError)

        retry_mgr.register_predicate("t1", is_timeout)
        should = retry_mgr.should_retry("t1", 0, 3, TimeoutError("timed out"))
        assert should is True
        should = retry_mgr.should_retry("t1", 0, 3, ValueError("other"))
        assert should is False


# =============================================================================
# ExecutionEngine Integration Tests
# =============================================================================


class TestExecutionEngine:
    """Integration tests for the full execution engine."""

    @pytest.fixture
    def engine(self):
        return ExecutionEngine()

    @pytest.mark.asyncio
    async def test_create_task(self, engine):
        task_id = await engine.create_task("test", {"key": "value"})
        assert task_id is not None
        task = await engine.get_task(task_id)
        assert task is not None
        assert task.get_capability() == "test"

    @pytest.mark.asyncio
    async def test_create_duplicate_task(self, engine):
        await engine.create_task("test", {}, task_id="dup1")
        with pytest.raises(TaskAlreadyExistsError):
            await engine.create_task("test", {}, task_id="dup1")

    @pytest.mark.asyncio
    async def test_cancel_task(self, engine):
        task_id = await engine.create_task("test", {})
        await engine.cancel(task_id)
        task = await engine.get_task(task_id)
        assert task.get_state() == TaskState.CANCELLED

    @pytest.mark.asyncio
    async def test_list_tasks(self, engine):
        await engine.create_task("test", {})
        await engine.create_task("test", {})
        tasks = await engine.list_tasks()
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_by_state(self, engine):
        t1_id = await engine.create_task("test", {})
        t2_id = await engine.create_task("test", {})
        await engine.cancel(t1_id)
        cancelled = await engine.list_tasks(state=TaskState.CANCELLED)
        assert len(cancelled) == 1

    @pytest.mark.asyncio
    async def test_register_handler_and_dispatch(self, engine):
        results = []

        async def handler(task):
            results.append(task.get_id())
            return {"done": True}

        engine.register_handler("test", handler)
        task_id = await engine.create_task("test", {})
        await engine.dispatch(task_id)

        task = await engine.get_task(task_id)
        assert task.get_state() == TaskState.QUEUED

    @pytest.mark.asyncio
    async def test_get_execution_summary(self, engine):
        await engine.create_task("test", {})
        await engine.create_task("test", {})
        summary = engine.get_execution_summary()
        assert summary["total_tasks"] == 2
        assert "by_state" in summary

    @pytest.mark.asyncio
    async def test_shutdown(self, engine):
        await engine.create_task("test", {})
        await engine.shutdown()
        # Should not raise


# =============================================================================
# Serialization Tests
# =============================================================================


class TestSerialization:
    """Tests for to_dict/from_dict conversions."""

    def test_task_result_roundtrip(self):
        result = TaskResult(
            task_id="t1",
            success=True,
            output={"key": "value"},
            duration=1.5,
            errors=["e1"],
            warnings=["w1"],
        )
        d = result.to_dict()
        restored = TaskResult.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.output == {"key": "value"}
        assert restored.duration == 1.5
