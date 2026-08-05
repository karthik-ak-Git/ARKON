"""ARKON Runtime - Heartbeat Management.

Every running agent sends heartbeats.
Health automatically degrades if heartbeat expires.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import structlog

from app.runtime.events import AgentHeartbeat
from app.runtime.exceptions import HeartbeatExpiredError

logger = structlog.get_logger(__name__)


@dataclass
class HeartbeatData:
    """Heartbeat data from an agent."""
    agent_id: str
    timestamp: float = field(default_factory=time.time)
    status: str = "running"
    cpu: float = 0.0
    memory: float = 0.0
    task_progress: float = 0.0
    current_activity: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "cpu": self.cpu,
            "memory": self.memory,
            "task_progress": self.task_progress,
            "current_activity": self.current_activity,
            "metadata": self.metadata,
        }


class HeartbeatManager:
    """Manages agent heartbeats.

    Every running agent sends heartbeats.
    Health automatically degrades if heartbeat expires.
    """

    def __init__(
        self,
        timeout: float = 90.0,
        event_handler: Callable[[AgentHeartbeat], Any] | None = None,
    ) -> None:
        """Initialize heartbeat manager.

        Args:
            timeout: Heartbeat timeout in seconds.
            event_handler: Optional event handler.
        """
        self._timeout = timeout
        self._event_handler = event_handler
        self._heartbeats: dict[str, HeartbeatData] = {}
        self._monitoring = False
        self._monitor_task: asyncio.Task | None = None

    async def send(
        self,
        agent_id: str,
        status: dict[str, Any],
    ) -> None:
        """Send a heartbeat from an agent."""
        heartbeat = HeartbeatData(
            agent_id=agent_id,
            timestamp=time.time(),
            status=status.get("status", "running"),
            cpu=status.get("cpu", 0.0),
            memory=status.get("memory", 0.0),
            task_progress=status.get("task_progress", 0.0),
            current_activity=status.get("current_activity", ""),
            metadata=status.get("metadata", {}),
        )
        self._heartbeats[agent_id] = heartbeat

        if self._event_handler:
            event = AgentHeartbeat(
                agent_id=agent_id,
                status=status,
            )
            try:
                result = self._event_handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(
                    "heartbeat_event_error",
                    agent_id=agent_id,
                    error=str(e),
                )

    async def check(self, agent_id: str) -> dict[str, Any]:
        """Check heartbeat status for an agent."""
        if agent_id not in self._heartbeats:
            return {
                "agent_id": agent_id,
                "has_heartbeat": False,
                "healthy": False,
                "expired": True,
                "last_beat": None,
                "age": None,
            }

        heartbeat = self._heartbeats[agent_id]
        age = time.time() - heartbeat.timestamp
        expired = age > self._timeout

        return {
            "agent_id": agent_id,
            "has_heartbeat": True,
            "healthy": not expired,
            "expired": expired,
            "last_beat": heartbeat.timestamp,
            "age": age,
            "timeout": self._timeout,
            "status": heartbeat.status,
            "cpu": heartbeat.cpu,
            "memory": heartbeat.memory,
            "task_progress": heartbeat.task_progress,
            "current_activity": heartbeat.current_activity,
        }

    async def check_all(self) -> dict[str, dict[str, Any]]:
        """Check heartbeats for all agents."""
        results = {}
        for agent_id in list(self._heartbeats.keys()):
            results[agent_id] = await self.check(agent_id)
        return results

    async def remove(self, agent_id: str) -> None:
        """Remove heartbeat tracking for an agent."""
        self._heartbeats.pop(agent_id, None)

    async def start_monitoring(self, interval: float = 10.0) -> None:
        """Start heartbeat monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(interval)
        )
        logger.info("heartbeat_monitoring_started", interval=interval)

    async def stop_monitoring(self) -> None:
        """Stop heartbeat monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("heartbeat_monitoring_stopped")

    async def _monitor_loop(self, interval: float) -> None:
        """Monitor loop for checking heartbeats."""
        while self._monitoring:
            try:
                await asyncio.sleep(interval)
                expired = []
                for agent_id in list(self._heartbeats.keys()):
                    check = await self.check(agent_id)
                    if check["expired"]:
                        expired.append(agent_id)
                        logger.warning(
                            "heartbeat_expired",
                            agent_id=agent_id,
                            age=check["age"],
                        )

                for agent_id in expired:
                    if self._event_handler:
                        event = AgentHeartbeat(
                            agent_id=agent_id,
                            status={"status": "expired"},
                        )
                        try:
                            result = self._event_handler(event)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception:
                            pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("heartbeat_monitor_error", error=str(e))

    def get_all(self) -> dict[str, HeartbeatData]:
        """Get all heartbeats."""
        return self._heartbeats.copy()

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout": self._timeout,
            "monitoring": self._monitoring,
            "heartbeats": {
                aid: hb.to_dict()
                for aid, hb in self._heartbeats.items()
            },
        }
