"""ARKON Execution Engine - WebSocket API.

Real-time task progress updates.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["execution-ws"])


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self._connections: dict[str, WebSocket] = {}
        self._task_subscribers: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new connection."""
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.debug("ws_connected", client_id=client_id)

    def disconnect(self, client_id: str) -> None:
        """Remove a connection."""
        self._connections.pop(client_id, None)
        # Remove from all task subscriptions
        for task_id, subscribers in list(self._task_subscribers.items()):
            subscribers.discard(client_id)
            if not subscribers:
                del self._task_subscribers[task_id]
        logger.debug("ws_disconnected", client_id=client_id)

    def subscribe(self, client_id: str, task_id: str) -> None:
        """Subscribe to task updates."""
        if task_id not in self._task_subscribers:
            self._task_subscribers[task_id] = set()
        self._task_subscribers[task_id].add(client_id)

    def unsubscribe(self, client_id: str, task_id: str) -> None:
        """Unsubscribe from task updates."""
        if task_id in self._task_subscribers:
            self._task_subscribers[task_id].discard(client_id)

    async def broadcast_to_task(self, task_id: str, message: dict[str, Any]) -> None:
        """Broadcast a message to all subscribers of a task."""
        subscribers = self._task_subscribers.get(task_id, set())
        disconnected = []

        for client_id in subscribers:
            ws = self._connections.get(client_id)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

    async def broadcast_all(self, message: dict[str, Any]) -> None:
        """Broadcast to all connected clients."""
        disconnected = []
        for client_id, ws in self._connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)


manager = ConnectionManager()


@router.websocket("/ws/execution/{client_id}")
async def execution_websocket(websocket: WebSocket, client_id: str) -> None:
    """WebSocket endpoint for real-time execution updates.

    Client can send:
    - {"action": "subscribe", "task_id": "..."}

    Server sends:
    - Task progress updates
    - Task state changes
    - Task results
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")

            if action == "subscribe":
                task_id = message.get("task_id")
                if task_id:
                    manager.subscribe(client_id, task_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "task_id": task_id,
                    })

            elif action == "unsubscribe":
                task_id = message.get("task_id")
                if task_id:
                    manager.unsubscribe(client_id, task_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "task_id": task_id,
                    })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error("ws_error", client_id=client_id, error=str(e))
        manager.disconnect(client_id)
