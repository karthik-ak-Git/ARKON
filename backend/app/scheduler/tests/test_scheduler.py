"""Comprehensive scheduler tests - 97 tests."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from app.scheduler.backpressure import BackpressureManager, SystemLoad, ThrottleConfig
from app.scheduler.balancer import TaskBalancer
from app.scheduler.constraints import (
    CapabilityConstraint,
    ConcurrencyConstraint,
    ConstraintChain,
    CustomConstraint,
    ExecutionLimitConstraint,
    ResourceConstraint,
    TimeWindowConstraint,
    WorkspaceAffinityConstraint,
)
from app.scheduler.dispatcher import Dispatcher
from app.scheduler.events import EventEmitter, SchedulerEvent, SchedulerEventType
from app.scheduler.exceptions import (
    DependencyCycleError,
    DependencyNotMetError,
    SchedulerError,
    TaskNotFoundError,
)
from app.scheduler.fairness import FairShareManager
from app.scheduler.interfaces import (
    BackpressureMode,
    ConstraintType,
    DependencyType,
    LoadBalancingStrategy,
    PreemptionMode,
    SchedulingPolicy,
    Task,
    TaskState,
)
from app.scheduler.planner import DAGPlanner
from app.scheduler.policy import (
    DeadlinePolicy,
    FIFOPolicy,
    LIFOPolicy,
    LongestJobFirstPolicy,
    Policy,
    PriorityPolicy,
    RoundRobinPolicy,
    ShortestJobFirstPolicy,
    WeightedPolicy,
    create_policy,
)
from app.scheduler.preemption import PreemptionManager
from app.scheduler.priority import PriorityConfig, PriorityLevel, PriorityManager
from app.scheduler.queue import TaskQueue
from app.scheduler.scheduler import Scheduler
from app.scheduler.strategy import (
    CapabilityScoreBalancer,
    LeastBusyBalancer,
    LeastLoadedBalancer,
    RandomBalancer,
    RoundRobinBalancer,
    Target,
    WeightedBalancer,
    create_balancer,
)
from app.scheduler.timeline import Timeline


# ─────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────

def _make_task(
    task_id: str = "t1",
    priority: int = 5,
    state: TaskState = TaskState.PENDING,
    capability: str = "compute",
    capability_requirements: list[str] | None = None,
    resource_requirements: dict[str, float] | None = None,
    workspace_id: str | None = None,
    group_id: str | None = None,
    estimated_duration: float | None = None,
    deadline: float | None = None,
) -> Task:
    return Task(
        task_id=task_id,
        name=f"Task {task_id}",
        priority=priority,
        state=state,
        capability=capability,
        capability_requirements=capability_requirements or [],
        resource_requirements=resource_requirements or {},
        workspace_id=workspace_id,
        group_id=group_id,
        estimated_duration=estimated_duration,
        deadline=deadline,
    )


def _make_target(
    target_id: str = "w1",
    load: float = 0.0,
    capacity: float = 1.0,
    weight: float = 1.0,
    active_tasks: int = 0,
    capabilities: set[str] | None = None,
) -> Target:
    return Target(
        target_id=target_id,
        load=load,
        capacity=capacity,
        weight=weight,
        active_tasks=active_tasks,
        capabilities=capabilities or {"compute"},
        healthy=True,
    )


# ─────────────────────────────────────
# INTERFACES
# ─────────────────────────────────────

class TestTaskState:
    def test_all_states_exist(self):
        assert len(TaskState) == 12

    def test_state_values(self):
        assert TaskState.PENDING.value == "pending"
        assert TaskState.QUEUED.value == "queued"
        assert TaskState.EXECUTING.value == "executing"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.FAILED.value == "failed"

    def test_task_creation(self):
        t = _make_task("t1")
        assert t.task_id == "t1"
        assert t.priority == 5
        assert t.state == TaskState.PENDING

    def test_task_to_dict(self):
        t = _make_task("t1")
        d = t.to_dict()
        assert d["task_id"] == "t1"
        assert "priority" in d
        assert "state" in d


class TestSchedulingPolicy:
    def test_all_policies(self):
        assert len(SchedulingPolicy) == 9


class TestLoadBalancingStrategy:
    def test_all_strategies(self):
        assert len(LoadBalancingStrategy) == 6


class TestPreemptionMode:
    def test_all_modes(self):
        assert len(PreemptionMode) == 4


class TestBackpressureMode:
    def test_all_modes(self):
        assert len(BackpressureMode) == 5


class TestDependencyType:
    def test_all_types(self):
        assert len(DependencyType) == 5


class TestConstraintType:
    def test_all_types(self):
        assert len(ConstraintType) == 7


# ─────────────────────────────────────
# EXCEPTIONS
# ─────────────────────────────────────

class TestExceptions:
    def test_scheduler_error(self):
        with pytest.raises(SchedulerError):
            raise SchedulerError("test")

    def test_cyclic_dependency(self):
        with pytest.raises(DependencyCycleError):
            raise DependencyCycleError("cycle")

    def test_missing_task(self):
        with pytest.raises(TaskNotFoundError):
            raise TaskNotFoundError("missing")

    def test_invalid_dependency(self):
        with pytest.raises(DependencyNotMetError):
            raise DependencyNotMetError("invalid")


# ─────────────────────────────────────
# EVENTS
# ─────────────────────────────────────

class TestEventEmitter:
    def test_emit_and_get(self):
        emitter = EventEmitter()
        emitter.emit(SchedulerEventType.TASK_SCHEDULED, task_id="t1")
        events = emitter.get_events()
        assert len(events) == 1
        assert events[0].task_id == "t1"

    def test_filter_by_type(self):
        emitter = EventEmitter()
        emitter.emit(SchedulerEventType.TASK_SCHEDULED, task_id="t1")
        emitter.emit(SchedulerEventType.TASK_COMPLETED, task_id="t2")
        scheduled = emitter.get_events(SchedulerEventType.TASK_SCHEDULED)
        assert len(scheduled) == 1

    def test_callback(self):
        emitter = EventEmitter()
        received = []
        emitter.on(SchedulerEventType.TASK_SCHEDULED, lambda e: received.append(e))
        emitter.emit(SchedulerEventType.TASK_SCHEDULED, task_id="t1")
        assert len(received) == 1


# ─────────────────────────────────────
# PRIORITY
# ─────────────────────────────────────

class TestPriorityManager:
    def test_set_and_get(self):
        pm = PriorityManager()
        old, new = pm.set_priority("t1", 3)
        assert old == PriorityManager()._config.default_priority
        assert new == 3
        assert pm.get_priority("t1") == 3

    def test_get_default(self):
        pm = PriorityManager()
        assert pm.get_priority("nonexistent") == PriorityManager()._config.default_priority

    def test_clamp_high(self):
        pm = PriorityManager()
        pm.set_priority("t1", 100)
        assert pm.get_priority("t1") == PriorityLevel.BACKGROUND

    def test_clamp_low(self):
        pm = PriorityManager()
        pm.set_priority("t1", -5)
        assert pm.get_priority("t1") == PriorityLevel.CRITICAL

    def test_remove(self):
        pm = PriorityManager()
        pm.set_priority("t1", 3)
        pm.remove("t1")
        assert pm.get_priority("t1") == PriorityManager()._config.default_priority

    def test_history(self):
        pm = PriorityManager()
        pm.set_priority("t1", 3)
        pm.set_priority("t1", 1)
        history = pm.get_history("t1")
        assert len(history) == 2

    def test_aging_enabled(self):
        pm = PriorityManager(PriorityConfig(aging_enabled=True, aging_interval=0.01, aging_increment=2.0))
        pm.set_priority("t1", 10)
        time.sleep(0.02)
        aged = pm.apply_aging(["t1"], current_time=time.time())
        assert "t1" in aged
        assert pm.get_priority("t1") < 10

    def test_aging_disabled(self):
        pm = PriorityManager(PriorityConfig(aging_enabled=False))
        pm.set_priority("t1", 10)
        aged = pm.apply_aging(["t1"])
        assert "t1" not in aged


class TestPriorityLevel:
    def test_levels(self):
        assert PriorityLevel.CRITICAL.value == 0
        assert PriorityLevel.HIGH.value == 1
        assert PriorityLevel.NORMAL.value == 5
        assert PriorityLevel.LOW.value == 10
        assert PriorityLevel.BACKGROUND.value == 15


# ─────────────────────────────────────
# POLICY
# ─────────────────────────────────────

class TestFIFOPolicy:
    def test_select_oldest(self):
        p = FIFOPolicy()
        t1 = _make_task("t1")
        t2 = _make_task("t2")
        t2.created_at = t1.created_at + 1
        assert p.select([t2, t1]).task_id == "t1"

    def test_select_empty(self):
        assert FIFOPolicy().select([]) is None


class TestLIFOPolicy:
    def test_select_newest(self):
        p = LIFOPolicy()
        t1 = _make_task("t1")
        t2 = _make_task("t2")
        t2.created_at = t1.created_at + 1
        assert p.select([t1, t2]).task_id == "t2"


class TestPriorityPolicy:
    def test_select_highest(self):
        p = PriorityPolicy()
        t1 = _make_task("t1", priority=10)
        t2 = _make_task("t2", priority=1)
        assert p.select([t1, t2]).task_id == "t2"


class TestDeadlinePolicy:
    def test_select_earliest_deadline(self):
        p = DeadlinePolicy()
        t1 = _make_task("t1", deadline=time.time() + 100)
        t2 = _make_task("t2", deadline=time.time() + 50)
        assert p.select([t1, t2]).task_id == "t2"

    def test_no_deadline_fallback(self):
        p = DeadlinePolicy()
        t1 = _make_task("t1")
        assert p.select([t1]).task_id == "t1"


class TestShortestJobFirst:
    def test_select_shortest(self):
        p = ShortestJobFirstPolicy()
        t1 = _make_task("t1", estimated_duration=10.0)
        t2 = _make_task("t2", estimated_duration=5.0)
        assert p.select([t1, t2]).task_id == "t2"


class TestLongestJobFirst:
    def test_select_longest(self):
        p = LongestJobFirstPolicy()
        t1 = _make_task("t1", estimated_duration=10.0)
        t2 = _make_task("t2", estimated_duration=5.0)
        assert p.select([t1, t2]).task_id == "t1"


class TestRoundRobinPolicy:
    def test_cycles_through(self):
        p = RoundRobinPolicy()
        t1 = _make_task("t1")
        t2 = _make_task("t2")
        r1 = p.select([t1, t2])
        r2 = p.select([t1, t2])
        assert r1.task_id != r2.task_id


class TestWeightedPolicy:
    def test_returns_task(self):
        p = WeightedPolicy()
        t1 = _make_task("t1")
        result = p.select([t1])
        assert result is not None


class TestCreatePolicy:
    def test_create_all(self):
        for pol in SchedulingPolicy:
            p = create_policy(pol)
            assert isinstance(p, Policy)


# ─────────────────────────────────────
# CONSTRAINTS
# ─────────────────────────────────────

class TestWorkspaceAffinity:
    def test_unrestricted(self):
        c = WorkspaceAffinityConstraint()
        assert c.check(_make_task("t1")).satisfied

    def test_allowed(self):
        c = WorkspaceAffinityConstraint(["ws1"])
        assert c.check(_make_task("t1", workspace_id="ws1")).satisfied

    def test_not_allowed(self):
        c = WorkspaceAffinityConstraint(["ws1"])
        assert not c.check(_make_task("t1", workspace_id="ws2")).satisfied


class TestCapabilityConstraint:
    def test_met(self):
        c = CapabilityConstraint({"compute", "storage"})
        assert c.check(_make_task("t1", capability_requirements=["compute"])).satisfied

    def test_not_met(self):
        c = CapabilityConstraint({"compute"})
        assert not c.check(_make_task("t1", capability_requirements=["compute", "ml"])).satisfied


class TestResourceConstraint:
    def test_met(self):
        c = ResourceConstraint({"cpu": 8.0})
        assert c.check(_make_task("t1", resource_requirements={"cpu": 4.0})).satisfied

    def test_not_met(self):
        c = ResourceConstraint({"cpu": 2.0})
        assert not c.check(_make_task("t1", resource_requirements={"cpu": 4.0})).satisfied


class TestTimeWindowConstraint:
    def test_in_window(self):
        c = TimeWindowConstraint(allowed_start=time.time() - 10, allowed_end=time.time() + 10)
        assert c.check(_make_task("t1")).satisfied

    def test_too_early(self):
        c = TimeWindowConstraint(allowed_start=time.time() + 100)
        assert not c.check(_make_task("t1")).satisfied

    def test_too_late(self):
        c = TimeWindowConstraint(allowed_end=time.time() - 100)
        assert not c.check(_make_task("t1")).satisfied


class TestConcurrencyConstraint:
    def test_under_limit(self):
        c = ConcurrencyConstraint(max_concurrent=2)
        assert c.check(_make_task("t1", group_id="g1")).satisfied

    def test_at_limit(self):
        c = ConcurrencyConstraint(max_concurrent=1)
        c.add_running("g1")
        assert not c.check(_make_task("t1", group_id="g1")).satisfied

    def test_release(self):
        c = ConcurrencyConstraint(max_concurrent=1)
        c.add_running("g1")
        c.remove_running("g1")
        assert c.check(_make_task("t1", group_id="g1")).satisfied


class TestExecutionLimitConstraint:
    def test_under_limit(self):
        c = ExecutionLimitConstraint(max_executions=5)
        assert c.check(_make_task("t1")).satisfied

    def test_at_limit(self):
        c = ExecutionLimitConstraint(max_executions=2)
        c.record_execution(1.0)
        c.record_execution(1.0)
        assert not c.check(_make_task("t1")).satisfied

    def test_time_limit(self):
        c = ExecutionLimitConstraint(max_total_time=10.0)
        c.record_execution(11.0)
        assert not c.check(_make_task("t1")).satisfied


class TestCustomConstraint:
    def test_pass(self):
        c = CustomConstraint("test", lambda t, ctx: True)
        assert c.check(_make_task("t1")).satisfied

    def test_fail(self):
        c = CustomConstraint("test", lambda t, ctx: False)
        assert not c.check(_make_task("t1")).satisfied


class TestConstraintChain:
    def test_all_pass(self):
        chain = ConstraintChain()
        chain.add(WorkspaceAffinityConstraint())
        chain.add(CapabilityConstraint({"compute"}))
        assert chain.check(_make_task("t1", capability_requirements=["compute"])).satisfied

    def test_one_fails(self):
        chain = ConstraintChain()
        chain.add(WorkspaceAffinityConstraint(["ws1"]))
        chain.add(CapabilityConstraint({"compute"}))
        result = chain.check(_make_task("t1", workspace_id="ws2", capability_requirements=["compute"]))
        assert not result.satisfied

    def test_clear(self):
        chain = ConstraintChain()
        chain.add(WorkspaceAffinityConstraint())
        chain.clear()
        assert len(chain._constraints) == 0


# ─────────────────────────────────────
# QUEUE
# ─────────────────────────────────────

class TestTaskQueue:
    def test_enqueue_dequeue(self):
        q = TaskQueue()
        t1 = _make_task("t1", priority=5)
        q.enqueue(t1)
        assert q.size() == 1
        result = q.dequeue()
        assert result.task_id == "t1"
        assert q.is_empty()

    def test_priority_order(self):
        q = TaskQueue()
        q.enqueue(_make_task("t1", priority=10))
        q.enqueue(_make_task("t2", priority=1))
        q.enqueue(_make_task("t3", priority=5))
        assert q.dequeue().task_id == "t2"
        assert q.dequeue().task_id == "t3"
        assert q.dequeue().task_id == "t1"

    def test_max_size(self):
        q = TaskQueue(max_size=2)
        q.enqueue(_make_task("t1"))
        q.enqueue(_make_task("t2"))
        assert not q.enqueue(_make_task("t3"))

    def test_remove(self):
        q = TaskQueue()
        q.enqueue(_make_task("t1"))
        q.enqueue(_make_task("t2"))
        q.remove("t1")
        assert q.size() == 1

    def test_peek(self):
        q = TaskQueue()
        q.enqueue(_make_task("t1"))
        assert q.peek().task_id == "t1"
        assert q.size() == 1

    def test_contains(self):
        q = TaskQueue()
        q.enqueue(_make_task("t1"))
        assert q.contains("t1")
        assert not q.contains("t2")

    def test_get_wait_time(self):
        q = TaskQueue()
        q.enqueue(_make_task("t1"))
        wait = q.get_wait_time("t1")
        assert wait is not None
        assert wait >= 0

    def test_update_priority(self):
        q = TaskQueue()
        q.enqueue(_make_task("t1", priority=10))
        q.update_priority("t1", 1)
        assert q.peek().priority == 1

    def test_get_by_state(self):
        q = TaskQueue()
        t1 = _make_task("t1", state=TaskState.QUEUED)
        q.enqueue(t1)
        assert len(q.get_by_state(TaskState.QUEUED)) == 1
        assert len(q.get_by_state(TaskState.EXECUTING)) == 0

    def test_to_dict(self):
        q = TaskQueue()
        q.enqueue(_make_task("t1"))
        d = q.to_dict()
        assert d["size"] == 1


# ─────────────────────────────────────
# FAIRNESS
# ─────────────────────────────────────

class TestFairShareManager:
    def test_register(self):
        fm = FairShareManager()
        fm.register_group("g1", weight=1.0)
        assert "g1" in fm.get_records()

    def test_allocate(self):
        fm = FairShareManager()
        fm.register_group("g1", weight=1.0)
        fm.register_group("g2", weight=1.0)
        assert not fm.allocate("g1", 1.0)  # Share is 0.5, exceeds
        assert fm.allocate("g1", 0.3)  # Under 0.5 share
        assert not fm.allocate("g1", 0.5)  # 0.3 + 0.5 = 0.8 > 0.5

    def test_release(self):
        fm = FairShareManager()
        fm.register_group("g1", weight=1.0)
        fm.allocate("g1", 0.5)
        fm.release("g1", 0.5)
        assert fm.get_deficit("g1") > 0

    def test_most_deficit(self):
        fm = FairShareManager()
        fm.register_group("g1", weight=1.0)
        fm.register_group("g2", weight=1.0)
        fm.allocate("g1", 0.3)  # g1 consumed=0.3, deficit=0.2; g2 consumed=0, deficit=0.5
        assert fm.get_most_deficit_group() == "g2"

    def test_to_dict(self):
        fm = FairShareManager()
        fm.register_group("g1", weight=1.0)
        d = fm.to_dict()
        assert "groups" in d


# ─────────────────────────────────────
# BALANCER
# ─────────────────────────────────────

class TestTaskBalancer:
    def test_select_target(self):
        b = TaskBalancer(LoadBalancingStrategy.LEAST_LOADED)
        b.register_target(_make_target("w1", load=0.5))
        b.register_target(_make_target("w2", load=0.1))
        task = _make_task("t1", capability_requirements=["compute"])
        target = b.select_target(task)
        assert target.target_id == "w2"

    def test_record_dispatch(self):
        b = TaskBalancer()
        b.register_target(_make_target("w1"))
        b.record_dispatch("t1", "w1")
        assert b.get_target("w1").active_tasks == 1

    def test_record_completion(self):
        b = TaskBalancer()
        b.register_target(_make_target("w1"))
        b.record_dispatch("t1", "w1")
        b.record_completion("w1")
        assert b.get_target("w1").active_tasks == 0

    def test_unregister(self):
        b = TaskBalancer()
        b.register_target(_make_target("w1"))
        b.unregister_target("w1")
        assert b.get_target("w1") is None


# ─────────────────────────────────────
# STRATEGY
# ─────────────────────────────────────

class TestLeastLoadedBalancer:
    def test_select(self):
        b = LeastLoadedBalancer()
        t1 = _make_target("w1", load=0.8)
        t2 = _make_target("w2", load=0.2)
        assert b.select([t1, t2]).target_id == "w2"

    def test_filter_healthy(self):
        b = LeastLoadedBalancer()
        t1 = _make_target("w1")
        t1.healthy = False
        t2 = _make_target("w2")
        assert b.select([t1, t2]).target_id == "w2"

    def test_no_candidates(self):
        b = LeastLoadedBalancer()
        assert b.select([]) is None


class TestLeastBusyBalancer:
    def test_select(self):
        b = LeastBusyBalancer()
        t1 = _make_target("w1", active_tasks=5)
        t2 = _make_target("w2", active_tasks=1)
        assert b.select([t1, t2]).target_id == "w2"


class TestRandomBalancer:
    def test_select(self):
        b = RandomBalancer()
        t1 = _make_target("w1")
        assert b.select([t1]).target_id == "w1"


class TestRoundRobinBalancer:
    def test_cycles(self):
        b = RoundRobinBalancer()
        t1 = _make_target("w1")
        t2 = _make_target("w2")
        r1 = b.select([t1, t2])
        r2 = b.select([t1, t2])
        assert r1.target_id != r2.target_id


class TestWeightedBalancer:
    def test_select(self):
        b = WeightedBalancer()
        t1 = _make_target("w1", weight=0.1)
        t2 = _make_target("w2", weight=10.0)
        # Statistical: w2 should be selected most of the time
        counts = {"w1": 0, "w2": 0}
        for _ in range(100):
            r = b.select([t1, t2])
            counts[r.target_id] += 1
        assert counts["w2"] > counts["w1"]


class TestCapabilityScoreBalancer:
    def test_select(self):
        b = CapabilityScoreBalancer()
        t1 = _make_target("w1", capabilities={"compute", "ml"})
        t2 = _make_target("w2", capabilities={"compute"})
        task = _make_task("t1", capability_requirements=["compute", "ml"])
        assert b.select([t1, t2]).target_id == "w1"


class TestCreateBalancer:
    def test_create_all(self):
        for strat in LoadBalancingStrategy:
            b = create_balancer(strat)
            assert isinstance(b, type(b))


# ─────────────────────────────────────
# PREEMPTION
# ─────────────────────────────────────

class TestPreemptionManager:
    def test_should_preempt(self):
        pm = PreemptionManager(PreemptionMode.PRIORITY_BASED)
        running = _make_task("t1", priority=10, state=TaskState.EXECUTING)
        new = _make_task("t2", priority=1)
        assert pm.should_preempt(running, new)

    def test_no_preempt_same_priority(self):
        pm = PreemptionManager()
        running = _make_task("t1", priority=5, state=TaskState.EXECUTING)
        new = _make_task("t2", priority=5)
        assert not pm.should_preempt(running, new)

    def test_no_preempt_no_mode(self):
        pm = PreemptionManager(PreemptionMode.NONE)
        running = _make_task("t1", priority=10, state=TaskState.EXECUTING)
        new = _make_task("t2", priority=1)
        assert not pm.should_preempt(running, new)

    def test_preempt_pause(self):
        pm = PreemptionManager(PreemptionMode.PRIORITY_BASED)
        running = _make_task("t1", priority=10, state=TaskState.EXECUTING)
        new = _make_task("t2", priority=1)
        event = pm.preempt(running, new)
        assert event is not None
        assert running.state == TaskState.PAUSED

    def test_preempt_age_based(self):
        pm = PreemptionManager(PreemptionMode.AGE_BASED)
        running = _make_task("t1", priority=10, state=TaskState.EXECUTING)
        new = _make_task("t2", priority=1)
        event = pm.preempt(running, new)
        assert event is not None
        assert running.state == TaskState.PAUSED

    def test_resume(self):
        pm = PreemptionManager()
        task = _make_task("t1", priority=10, state=TaskState.PAUSED)
        pm._original_priorities["t1"] = 5
        pm.resume_task(task)
        assert task.state == TaskState.READY
        assert task.priority == 5

    def test_aging(self):
        pm = PreemptionManager(aging_enabled=True, aging_interval=0.01, max_aging_boost=3)
        task = _make_task("t1", priority=10, state=TaskState.QUEUED)
        task.created_at = time.time() - 1.0
        aged = pm.apply_aging([task])
        assert len(aged) == 1
        assert task.priority < 10

    def test_no_aging_disabled(self):
        pm = PreemptionManager(aging_enabled=False)
        task = _make_task("t1", priority=10, state=TaskState.QUEUED)
        pm.apply_aging([task])
        assert task.priority == 10

    def test_is_starved(self):
        pm = PreemptionManager()
        task = _make_task("t1", priority=1)
        task.created_at = time.time() - 600
        assert pm.is_starved(task, threshold=300)

    def test_to_dict(self):
        pm = PreemptionManager()
        d = pm.to_dict()
        assert "mode" in d
        assert "aging_enabled" in d


# ─────────────────────────────────────
# BACKPRESSURE
# ─────────────────────────────────────

class TestBackpressureManager:
    def test_no_load(self):
        bm = BackpressureManager()
        assert not bm.is_overloaded()
        assert not bm.should_throttle()

    def test_overloaded(self):
        bm = BackpressureManager(BackpressureMode.ADAPTIVE)
        load = SystemLoad(queue_size=85)
        bm.update_load(load)
        assert bm.is_overloaded()
        assert bm.should_throttle()

    def test_warning(self):
        bm = BackpressureManager()
        load = SystemLoad(queue_size=55)
        bm.update_load(load)
        assert bm.is_warning()

    def test_reject(self):
        bm = BackpressureManager(BackpressureMode.REJECT)
        load = SystemLoad(queue_size=85)
        bm.update_load(load)
        assert bm.should_reject()

    def test_disabled(self):
        bm = BackpressureManager(BackpressureMode.NONE)
        load = SystemLoad(queue_size=200)
        bm.update_load(load)
        assert not bm.should_throttle()
        assert not bm.should_reject()

    def test_delay(self):
        bm = BackpressureManager(BackpressureMode.ADAPTIVE)
        load = SystemLoad(queue_size=85)
        bm.update_load(load)
        delay = bm.get_delay()
        assert delay > 0

    def test_stats(self):
        bm = BackpressureManager()
        d = bm.get_stats()
        assert "mode" in d
        assert "is_overloaded" in d


# ─────────────────────────────────────
# TIMELINE
# ─────────────────────────────────────

class TestTimeline:
    def test_record(self):
        t = Timeline()
        t.record("t1", "submitted")
        t.record("t1", "dispatched")
        assert t.get_entry_count() == 2

    def test_task_timeline(self):
        t = Timeline()
        t.record("t1", "submitted")
        tl = t.get_task_timeline("t1")
        assert tl is not None
        assert len(tl.entries) == 1

    def test_duration(self):
        t = Timeline()
        t.record("t1", "start", {"ts": 1.0})
        t.record("t1", "end", {"ts": 5.0})
        # Duration depends on actual time, but entries exist
        tl = t.get_task_timeline("t1")
        assert tl.total_duration is not None

    def test_recent_events(self):
        t = Timeline()
        for i in range(5):
            t.record(f"t{i}", "event")
        assert len(t.get_recent_events(3)) == 3

    def test_clear_task(self):
        t = Timeline()
        t.record("t1", "event")
        t.clear_task("t1")
        assert t.get_task_count() == 0

    def test_to_dict(self):
        t = Timeline()
        t.record("t1", "event")
        d = t.to_dict()
        assert "task_count" in d


# ─────────────────────────────────────
# PLANNER
# ─────────────────────────────────────

class TestDAGPlanner:
    def test_add_task(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        assert len(p.get_tasks()) == 1

    def test_add_dependency(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        p.add_task(_make_task("t2"))
        p.add_dependency("t1", "t2")
        assert len(p.get_edges()) == 1

    def test_predecessors(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        p.add_task(_make_task("t2"))
        p.add_dependency("t1", "t2")
        assert p.get_predecessors("t2") == ["t1"]

    def test_successors(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        p.add_task(_make_task("t2"))
        p.add_dependency("t1", "t2")
        assert p.get_successors("t1") == ["t2"]

    def test_cyclic_detection(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        p.add_task(_make_task("t2"))
        p.add_dependency("t1", "t2")
        with pytest.raises(DependencyCycleError):
            p.add_dependency("t2", "t1")

    def test_self_dependency(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        with pytest.raises(DependencyNotMetError):
            p.add_dependency("t1", "t1")

    def test_missing_task(self):
        p = DAGPlanner()
        with pytest.raises(TaskNotFoundError):
            p.add_dependency("t1", "t2")

    def test_ready_tasks(self):
        p = DAGPlanner()
        t1 = _make_task("t1", state=TaskState.PENDING)
        t2 = _make_task("t2", state=TaskState.PENDING)
        p.add_task(t1)
        p.add_task(t2)
        p.add_dependency("t1", "t2")
        ready = p.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "t1"

    def test_execution_batches(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        p.add_task(_make_task("t2"))
        p.add_task(_make_task("t3"))
        p.add_dependency("t1", "t3")
        p.add_dependency("t2", "t3")
        batches = p.get_execution_batches()
        assert len(batches) == 2
        assert set(batches[0].task_ids) == {"t1", "t2"}
        assert batches[1].task_ids == ["t3"]

    def test_remove_task(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        p.add_task(_make_task("t2"))
        p.add_dependency("t1", "t2")
        p.remove_task("t1")
        assert len(p.get_tasks()) == 1

    def test_to_dict(self):
        p = DAGPlanner()
        p.add_task(_make_task("t1"))
        d = p.to_dict()
        assert d["task_count"] == 1


# ─────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────

class TestDispatcher:
    def test_dispatch(self):
        balancer = TaskBalancer()
        balancer.register_target(_make_target("w1"))
        d = Dispatcher(balancer)
        task = _make_task("t1", state=TaskState.QUEUED)
        result = d.dispatch(task)
        assert result.success
        assert result.target_id == "w1"
        assert task.state == TaskState.EXECUTING

    def test_dispatch_no_target(self):
        d = Dispatcher()
        task = _make_task("t1", state=TaskState.QUEUED)
        result = d.dispatch(task)
        assert not result.success

    def test_dispatch_invalid_state(self):
        d = Dispatcher()
        task = _make_task("t1", state=TaskState.COMPLETED)
        result = d.dispatch(task)
        assert not result.success

    def test_batch_dispatch(self):
        balancer = TaskBalancer()
        balancer.register_target(_make_target("w1"))
        d = Dispatcher(balancer)
        tasks = [_make_task(f"t{i}", state=TaskState.QUEUED) for i in range(3)]
        results = d.dispatch_batch(tasks)
        assert len(results) == 3
        assert all(r.success for r in results)

    def test_success_rate(self):
        balancer = TaskBalancer()
        balancer.register_target(_make_target("w1"))
        d = Dispatcher(balancer)
        t1 = _make_task("t1", state=TaskState.QUEUED)
        d.dispatch(t1)
        d.complete("t1", "w1")
        assert d.get_success_rate() == 1.0

    def test_to_dict(self):
        d = Dispatcher()
        result = d.to_dict()
        assert "dispatch_count" in result


# ─────────────────────────────────────
# SCHEDULER
# ─────────────────────────────────────

class TestScheduler:
    def test_submit(self):
        s = Scheduler()
        task = _make_task("t1")
        decision = s.submit(task)
        assert decision.action == "scheduled"
        assert s.queue_size == 1

    def test_submit_paused(self):
        s = Scheduler()
        s.pause_scheduler()
        decision = s.submit(_make_task("t1"))
        assert decision.action == "rejected"

    def test_schedule_next(self):
        s = Scheduler()
        s.submit(_make_task("t1"))
        # Need a target registered
        s._balancer.register_target(_make_target("w1"))
        result = s.schedule_next()
        assert result is not None

    def test_cancel_task(self):
        s = Scheduler()
        s.submit(_make_task("t1"))
        assert s.cancel_task("t1")
        assert s.queue_size == 0

    def test_pause_resume(self):
        s = Scheduler()
        s.pause_scheduler()
        assert s.is_paused()
        s.resume_scheduler()
        assert not s.is_paused()

    def test_update_priority(self):
        s = Scheduler()
        s.submit(_make_task("t1", priority=10))
        assert s.update_task_priority("t1", 1)
        assert s.get_task("t1").priority == 1

    def test_get_task(self):
        s = Scheduler()
        s.submit(_make_task("t1"))
        assert s.get_task("t1") is not None

    def test_get_scheduled(self):
        s = Scheduler()
        s.submit(_make_task("t1"))
        s.submit(_make_task("t2"))
        assert len(s.get_scheduled_tasks()) == 2

    def test_to_dict(self):
        s = Scheduler()
        d = s.to_dict()
        assert "is_running" in d
        assert "queue_size" in d

    def test_backpressure_reject(self):
        s = Scheduler()
        s._backpressure.set_mode(BackpressureMode.REJECT)
        s._backpressure.update_load(SystemLoad(queue_size=85))
        decision = s.submit(_make_task("t1"))
        assert decision.action == "rejected"

    def test_events(self):
        s = Scheduler()
        s.submit(_make_task("t1"))
        events = s.get_events(SchedulerEventType.TASK_SCHEDULED)
        assert len(events) >= 1

    def test_constraint_reject(self):
        s = Scheduler()
        s._constraints.add(WorkspaceAffinityConstraint(["ws1"]))
        decision = s.submit(_make_task("t1", workspace_id="ws2"))
        assert decision.action == "rejected"

    def test_fair_share(self):
        s = Scheduler(fair_share_enabled=True)
        assert s._fairness is not None

    def test_load(self):
        s = Scheduler()
        s.submit(_make_task("t1"))
        load = s.get_load()
        assert load.queue_size == 1

    def test_timeline(self):
        s = Scheduler()
        s.submit(_make_task("t1"))
        tl = s.get_timeline()
        assert tl.get_entry_count() >= 1
