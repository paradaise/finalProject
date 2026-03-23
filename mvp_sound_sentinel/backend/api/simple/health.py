from datetime import datetime

from fastapi import APIRouter

from backend.api.simple import state


router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": state.model is not None,
        "devices_connected": len(state.websocket_connections),
        "timestamp": datetime.now().isoformat(),
    }

