import sqlite3
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.simple import state

router = APIRouter()

class NotificationSound(BaseModel):
    name: str | None = None
    sound_name: str | None = None
    device_id: str

@router.post("/notification_sounds")
async def add_notification_sound(sound: NotificationSound):
    """Добавление важного звука для уведомлений"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()
        
        sound_id = str(uuid.uuid4())
        resolved_name = (sound.name or sound.sound_name or "").strip()
        if not resolved_name:
            raise HTTPException(status_code=400, detail="sound name is required")
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO notification_sounds (id, sound_name, device_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sound_id, resolved_name, sound.device_id, datetime.now().isoformat())
        )
        
        conn.commit()
        conn.close()
        
        print(f"🔔 Added notification sound: {resolved_name}")
        
        return {"sound_id": sound_id, "status": "added"}
        
    except Exception as e:
        print(f"❌ Error adding notification sound: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notification_sounds/{device_id}")
async def get_notification_sounds(device_id: str):
    """Получение важных звуков для устройства"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, sound_name, device_id, created_at
            FROM notification_sounds 
            WHERE device_id = ? 
            ORDER BY created_at DESC
            """,
            (device_id,)
        )
        
        sounds = []
        for row in cursor.fetchall():
            sounds.append({
                "id": row[0],
                "name": row[1],
                "device_id": row[2],
                "created_at": row[3],
            })
        
        conn.close()
        return sounds
        
    except Exception as e:
        print(f"❌ Error getting notification sounds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/notification_sounds/{sound_id}")
async def delete_notification_sound(sound_id: str):
    """Удаление важного звука"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM notification_sounds WHERE id = ?", (sound_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sound not found")
        
        conn.commit()
        conn.close()
        
        print(f"🗑️ Deleted notification sound: {sound_id}")
        
        return {"status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting notification sound: {e}")
        raise HTTPException(status_code=500, detail=str(e))
