"""Scheduler - central orchestrator for task scheduling."""

from __future__ import annotations

import time
from typing import Any

from app.scheduler.backpressure import BackpressureManager, SystemLoad, ThrottleConfig
from app.scheduler.balancer import TaskBalancer
from app.scheduler.constraints import ConstraintChain
from app.scheduler.dispatcher import Dispatcher, DispatchResult
from app.scheduler.events import EventEmitter, SchedulerEvent, SchedulerEventType
from app.scheduler.exceptions import SchedulerError
from app.scheduler.fairness import FairShareManager
from app.scheduler.interfaces import (
    BackpressureMode,
    LoadBalancingStrategy,
    PreemptionMode,
    SchedulerStatus,
    SchedulingDecision,
    Task,
    TaskState,
)
from app.scheduler.planner import DAGPlanner
from app.scheduler.policy import Policy, create_policy
from app.scheduler.preemption import PreemptionManager
from app.scheduler.priority import PriorityManager
from app.scheduler.queue import TaskQueue
from app.scheduler.timeline import Timeline


class Scheduler:
    """Central scheduler orchestrator integrating all components."""

    def __init__(
        self,
        policy_type: Any = None,
        load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED,
        preemption_mode: PreemptionMode = PreemptionMode.PRIORITY_BASED,
        backpressure_mode: BackpressureMode = BackpressureMode.ADAPTIVE,
        max_queue_size: int = 10000,
        fair_share_enabled: bool = False,
    ) -> None:
        self._policy = create_policy(policy_type) if policy_type else None
        self._queue = TaskQueue(max_size=max_queue_size)
        self._planner = DAGPlanner()
        self._balancer = TaskBalancer(load_balancing)
        self._dispatcher = Dispatcher(self._balancer)
        self._constraints = ConstraintChain()
        self._priority_manager = PriorityManager()
        self._preemption = PreemptionManager(preemption_mode)
        self._backpressure = BackpressureManager(backpressure_mode)
        self._fairness = FairShareManager() if fair_share_enabled else None
        self._timeline = Timeline()
        self._events = EventEmitter()

        self._running_tasks: dict[str, Task] = {}
        self._paused_tasks: dict[str, Task] = {}
        self._completed_tasks: dict[str, Task] = {}
        self._is_running: bool = True
        self._is_paused: bool = False
        self._total_scheduled: int = 0
        self._total_rejected: int = 0

        self._dispatcher.on_dispatch(self._on_task_dispatched)
        self._dispatcher.on_failure(self._on_task_failure)

    @property
    def status(self) -> SchedulerStatus:
        return SchedulerStatus(
            is_running=self._is_running,
            is_paused=self._is_paused,
            queue_size=self._queue.size(),
            active_tasks=self.running_count,
            policy=self._policy.policy_type.value if self._policy else "none",
        )

    @property
    def queue_size(self) -> int:
        return self._queue.size()

    @property
    def running_count(self) -> int:
        return len(self._running_tasks)

    def submit(self, task: Task) -> SchedulingDecision:
        """Submit a task for scheduling."""
        if self._is_paused:
            return SchedulingDecision(
                task_id=task.task_id,
                action="rejected",
                reason="Scheduler is paused",
            )

        if self._backpressure.should_reject():
            self._total_rejected += 1
            self._timeline.record(task.task_id, "rejected", {"reason": "backpressure"})
            self._events.emit(SchedulerEventType.TASK_REJECTED, task_id=task.task_id, reason="backpressure")
            return SchedulingDecision(
                task_id=task.task_id,
                action="rejected",
                reason="Backpressure: system overloaded",
            )

        result = self._constraints.check(task)
        if not result.satisfied:
            self._total_rejected += 1
            self._timeline.record(task.task_id, "rejected", {"reason": result.reason})
            self._events.emit(SchedulerEventType.TASK_REJECTED, task_id=task.task_id, reason=result.reason)
            return SchedulingDecision(
                task_id=task.task_id,
                action="rejected",
                reason=result.reason,
            )

        task.state = TaskState.QUEUED
        self._planner.add_task(task)
        enqueued = self._queue.enqueue(task)

        if not enqueued:
            self._total_rejected += 1
            return SchedulingDecision(
                task_id=task.task_id,
                action="rejected",
                reason="Queue full",
            )

        self._timeline.record(task.task_id, "submitted", {"priority": task.priority})
        self._events.emit(SchedulerEventType.TASK_SCHEDULED, task_id=task.task_id, priority=task.priority)

        self._total_scheduled += 1
        return SchedulingDecision(
            task_id=task.task_id,
            action="scheduled",
            reason="Accepted into queue",
        )

    def schedule_next(self) -> DispatchResult | None:
        """Schedule the next task."""
        if self._backpressure.should_throttle():
            return None

        self._apply_preemption()
        self._apply_aging()

        ready = self._planner.get_ready_tasks()
        queued_ready = [t for t in ready if t.state == TaskState.QUEUED]

        if not queued_ready:
            return None

        if self._policy:
            task = self._policy.select(queued_ready)
        else:
            task = queued_ready[0]

        if not task:
            return None

        task.state = TaskState.DISPATCHING
        self._queue.remove(task.task_id)

        if self._fairness and task.group_id:
            self._fairness.allocate(task.group_id, 1.0)

        result = self._dispatcher.dispatch(task)
        self._timeline.record(task.task_id, "dispatched", {"target": result.target_id})
        return result

    def complete_task(self, task_id: str, success: bool = True) -> None:
        """Mark a task as completed."""
        task = self._running_tasks.pop(task_id, None)
        if not task:
            task = self._paused_tasks.pop(task_id, None)
        if not task:
            return

        task.state = TaskState.COMPLETED if success else TaskState.FAILED
        task.completed_at = time.time()
        self._completed_tasks[task_id] = task

        if task.group_id and self._fairness:
            self._fairness.release(task.group_id, 1.0)

        self._timeline.record(task_id, "completed" if success else "failed")
        self._preemption.reset_aging(task_id)

        event_type = SchedulerEventType.TASK_COMPLETED if success else SchedulerEventType.TASK_FAILED
        self._events.emit(event_type, task_id=task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self._queue.remove(task_id)
        if not task:
            task = self._running_tasks.pop(task_id, None)
        if not task:
            task = self._paused_tasks.pop(task_id, None)
        if not task:
            return False

        task.state = TaskState.CANCELLED
        task.completed_at = time.time()
        self._completed_tasks[task_id] = task
        self._timeline.record(task_id, "cancelled")
        return True

    def pause_scheduler(self) -> None:
        self._is_paused = True
        self._events.emit(SchedulerEventType.SCHEDULER_PAUSED)
        self._timeline.record("__scheduler__", "paused")

    def resume_scheduler(self) -> None:
        self._is_paused = False
        self._events.emit(SchedulerEventType.SCHEDULER_RESUMED)
        self._timeline.record("__scheduler__", "resumed")

    def update_task_priority(self, task_id: str, new_priority: int) -> bool:
        success = self._queue.update_priority(task_id, new_priority)
        if success:
            self._events.emit(SchedulerEventType.PRIORITY_CHANGED, task_id=task_id, new_priority=new_priority)
        return success

    def get_task(self, task_id: str) -> Task | None:
        return (
            self._queue.get(task_id)
            or self._running_tasks.get(task_id)
            or self._paused_tasks.get(task_id)
            or self._completed_tasks.get(task_id)
        )

    def get_scheduled_tasks(self) -> list[Task]:
        return self._queue.get_all()

    def get_running_tasks(self) -> list[Task]:
        return list(self._running_tasks.values())

    def is_paused(self) -> bool:
        return self._is_paused

    def get_load(self) -> SystemLoad:
        return SystemLoad(
            queue_size=self._queue.size(),
            running_count=self.running_count,
        )

    def get_events(self, event_type: SchedulerEventType | None = None) -> list[SchedulerEvent]:
        return self._events.get_events(event_type)

    def get_timeline(self) -> Timeline:
        return self._timeline

    def to_dict(self) -> dict:
        return {
            "is_running": self._is_running,
            "is_paused": self._is_paused,
            "queue_size": self._queue.size(),
            "running_count": self.running_count,
            "total_scheduled": self._total_scheduled,
            "total_rejected": self._total_rejected,
            "balancer": self._balancer.to_dict(),
            "backpressure": self._backpressure.to_dict(),
            "preemption": self._preemption.to_dict(),
            "timeline": self._timeline.to_dict(),
        }

    def _apply_preemption(self) -> None:
        if not self._running_tasks:
            return
        queued = self._queue.get_all()
        for running in list(self._running_tasks.values()):
            for queued_task in queued:
                event = self._preemption.preempt(running, queued_task)
                if event:
                    self._paused_tasks[running.task_id] = running
                    self._running_tasks.pop(running.task_id, None)
                    self._timeline.record(running.task_id, "preempted")
                    break

    def _apply_aging(self) -> None:
        queued = self._queue.get_all()
        aged = self._preemption.apply_aging(queued)
        for task in aged:
            self._queue.update_priority(task.task_id, task.priority)

    def _on_task_dispatched(self, task: Task, target: Any) -> None:
        self._running_tasks[task.task_id] = task

    def _on_task_failure(self, task: Task, reason: str) -> None:
        self._timeline.record(task.task_id, "dispatch_failed", {"reason": reason})
