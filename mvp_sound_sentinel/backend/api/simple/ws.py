import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.simple import state


router = APIRouter()


async def broadcast_to_websockets(data: dict) -> None:
    if state.websocket_connections:
        # Skip logging for audio_level_updated and device_updated to reduce noise
        if data.get("type") not in ["audio_level_updated", "device_updated"]:
            print(
                f"Broadcasting: {data.get('type', 'unknown')} to {len(state.websocket_connections)} clients"
            )
        await asyncio.gather(
            *[ws.send_json(data) for ws in state.websocket_connections],
            return_exceptions=True,
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    state.websocket_connections.add(websocket)
    print(f"WebSocket connected: {len(state.websocket_connections)} clients")

    try:
        while True:
            # Ждем данные с таймаутом
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
                    # Skip ping/pong logging to reduce noise
            except asyncio.TimeoutError:
                # Отправляем keep-alive
                try:
                    await websocket.send_json({"type": "keepalive"})
                except:
                    break
    except WebSocketDisconnect:
        print(f"WebSocket disconnected")
        state.websocket_connections.discard(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        state.websocket_connections.discard(websocket)
