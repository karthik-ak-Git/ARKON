"""ARKON Runtime - WebSocket Endpoint.

Real-time runtime event streaming.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.runtime.events import EVENT_TYPES

router = APIRouter(tags=["runtime-ws"])


class RuntimeWebSocketManager:
    """Manages WebSocket connections for runtime events."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._subscriptions: dict[str, set[str]] = {}

    async def connect(self, ws: WebSocket, client_id: str) -> None:
        await ws.accept()
        if client_id not in self._connections:
            self._connections[client_id] = []
        self._connections[client_id].append(ws)

    async def disconnect(self, ws: WebSocket, client_id: str) -> None:
        if client_id in self._connections:
            self._connections[client_id] = [
                c for c in self._connections[client_id] if c != ws
            ]
            if not self._connections[client_id]:
                del self._connections[client_id]

    async def broadcast(self, event: dict[str, Any]) -> None:
        dead: list[tuple[str, WebSocket]] = []
        for cid, conns in self._connections.items():
            for ws in conns:
                try:
                    if ws.client_state == WebSocketState.CONNECTED:
                        await ws.send_json(event)
                except Exception:
                    dead.append((cid, ws))
        for cid, ws in dead:
            await self.disconnect(ws, cid)

    async def subscribe(self, client_id: str, event_types: list[str]) -> None:
        for et in event_types:
            if et not in self._subscriptions:
                self._subscriptions[et] = set()
            self._subscriptions[et].add(client_id)

    async def unsubscribe(self, client_id: str, event_types: list[str]) -> None:
        for et in event_types:
            if et in self._subscriptions:
                self._subscriptions[et].discard(client_id)
                if not self._subscriptions[et]:
                    del self._subscriptions[et]

    def is_subscribed(self, client_id: str, event_type: str) -> bool:
        if event_type not in self._subscriptions:
            return True
        return client_id in self._subscriptions[event_type]


# Singleton
ws_manager = RuntimeWebSocketManager()


@router.websocket("/ws/runtime/{client_id}")
async def runtime_websocket(websocket: WebSocket, client_id: str) -> None:
    """WebSocket endpoint for runtime events.

    Protocol:
      - Server sends JSON events
      - Client can send:
        - {"action": "subscribe", "event_types": ["agent.created", "agent.heartbeat"]}
        - {"action": "unsubscribe", "event_types": ["agent.heartbeat"]}
        - {"action": "ping"} → server responds {"type": "pong"}
    """
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action", "")

                if action == "subscribe":
                    event_types = msg.get("event_types", list(EVENT_TYPES.keys()))
                    await ws_manager.subscribe(client_id, event_types)
                    await websocket.send_json({
                        "type": "subscribed",
                        "event_types": event_types,
                    })

                elif action == "unsubscribe":
                    event_types = msg.get("event_types", [])
                    await ws_manager.unsubscribe(client_id, event_types)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "event_types": event_types,
                    })

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, client_id)
    except Exception:
        await ws_manager.disconnect(websocket, client_id)
