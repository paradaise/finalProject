import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.simple import state


router = APIRouter()


async def broadcast_to_websockets(data: dict) -> None:
    if state.websocket_connections:
        print(
            f"📡 Broadcasting: {data.get('type', 'unknown')} to {len(state.websocket_connections)} clients"
        )
        await asyncio.gather(
            *[ws.send_json(data) for ws in state.websocket_connections],
            return_exceptions=True,
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    state.websocket_connections.add(websocket)
    print(f"🔗 WebSocket подключен: {len(state.websocket_connections)} клиентов")

    try:
        while True:
            # Ждем данные с таймаутом
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
                    print("🏓 Ping/Pong")
            except asyncio.TimeoutError:
                # Отправляем keep-alive
                try:
                    await websocket.send_json({"type": "keepalive"})
                except:
                    break
    except WebSocketDisconnect:
        print(f"❌ WebSocket отключен")
        state.websocket_connections.discard(websocket)
    except Exception as e:
        print(f"❌ WebSocket ошибка: {e}")
        state.websocket_connections.discard(websocket)
