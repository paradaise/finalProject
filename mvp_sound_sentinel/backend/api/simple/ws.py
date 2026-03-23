import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.simple import state


router = APIRouter()


async def broadcast_to_websockets(data: dict) -> None:
    if state.websocket_connections:
        await asyncio.gather(
            *[ws.send_json(data) for ws in state.websocket_connections],
            return_exceptions=True,
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    state.websocket_connections.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.websocket_connections.discard(websocket)
    except Exception:
        # Keep server alive if the websocket is in a bad state
        state.websocket_connections.discard(websocket)

