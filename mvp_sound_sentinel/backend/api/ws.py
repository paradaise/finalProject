import json
from typing import Any, Set


async def broadcast_to_websockets(
    message: dict,
    websocket_connections: Set[Any],
) -> None:
    """Broadcast message to all connected WebSocket clients."""
    if websocket_connections:
        message_str = json.dumps(message)
        disconnected = set()

        for websocket in websocket_connections:
            try:
                await websocket.send_text(message_str)
            except Exception:
                disconnected.add(websocket)

        websocket_connections.difference_update(disconnected)

