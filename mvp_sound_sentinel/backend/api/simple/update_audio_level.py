from fastapi import APIRouter
from pydantic import BaseModel
from backend.api.simple import state
from backend.api.simple.ws import broadcast_to_websockets

router = APIRouter()

class AudioLevel(BaseModel):
    device_id: str
    db_level: float
    timestamp: str

@router.post("/update_audio_level")
async def update_audio_level(data: AudioLevel):
    """Обновление только уровня звука без детекции"""
    await broadcast_to_websockets(
        {
            "type": "audio_level_updated",
            "device_id": data.device_id,
            "db_level": data.db_level,
            "timestamp": data.timestamp,
        }
    )
    return {"status": "updated"}
