import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class HopMessage(BaseModel):
    probe_id: uuid.UUID
    ttl: int
    ip: str | None
    rtt_ms: float | None
    lat: float | None
    lon: float | None
    country: str | None = None
    city: str | None = None


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws) if hasattr(self._connections, "discard") else (
            self._connections.remove(ws) if ws in self._connections else None
        )

    async def broadcast(self, message: HopMessage) -> None:
        data = message.model_dump_json()
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self._connections:
                self._connections.remove(ws)


manager = ConnectionManager()

router = APIRouter()


@router.websocket("/live")
async def live(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)