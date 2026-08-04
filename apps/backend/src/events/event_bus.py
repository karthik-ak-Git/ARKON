import asyncio
from typing import Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


class EventType(str, Enum):
    AGENT_REGISTERED = "agent.registered"
    AGENT_INITIALIZED = "agent.initialized"
    AGENT_STARTED = "agent.started"
    AGENT_PAUSED = "agent.paused"
    AGENT_RESUMED = "agent.resumed"
    AGENT_COMPLETED = "agent.completed"
    AGENT_CANCELLED = "agent.cancelled"
    AGENT_ERROR = "agent.error"
    AGENT_SHUTDOWN = "agent.shutdown"
    AGENT_DEREGISTERED = "agent.deregistered"
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    PLUGIN_INSTALLED = "plugin.installed"
    PLUGIN_UNINSTALLED = "plugin.uninstalled"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_ERROR = "plugin.error"
    HEARTBEAT = "agent.heartbeat"
    METRIC = "metric"


@dataclass
class Event:
    type: EventType
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str | None = None


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Callable[[Event], Any]]] = defaultdict(list)
        self._middleware: list[Callable[[Event], Any]] = []

    def subscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def add_middleware(self, middleware: Callable[[Event], Any]) -> None:
        self._middleware.append(middleware)

    async def publish(self, event: Event) -> None:
        for middleware in self._middleware:
            await middleware(event)

        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception:
                pass

    def get_handlers(self, event_type: EventType) -> list[Callable[[Event], Any]]:
        return list(self._handlers.get(event_type, []))