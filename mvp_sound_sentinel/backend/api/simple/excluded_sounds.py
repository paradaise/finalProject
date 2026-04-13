import sqlite3
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.simple import state

router = APIRouter()


class ExcludedSound(BaseModel):
    name: str | None = None
    sound_name: str | None = None
    device_id: str


@router.post("/excluded_sounds")
async def add_excluded_sound(sound: ExcludedSound):
    """Добавление исключенного звука"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()

        sound_id = str(uuid.uuid4())
        resolved_name = (sound.name or sound.sound_name or "").strip()
        if not resolved_name:
            raise HTTPException(status_code=400, detail="sound name is required")

        cursor.execute(
            """
            INSERT OR REPLACE INTO excluded_sounds (id, sound_name, device_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (sound_id, resolved_name, sound.device_id, datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()

        print(f"🔇 Added excluded sound: {resolved_name}")

        return {"sound_id": sound_id, "status": "added"}

    except Exception as e:
        print(f"❌ Error adding excluded sound: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/excluded_sounds/{device_id}")
async def get_excluded_sounds(device_id: str):
    """Получение исключенных звуков для устройства"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, sound_name, device_id, created_at
            FROM excluded_sounds 
            WHERE device_id = ? 
            ORDER BY created_at DESC
            """,
            (device_id,),
        )

        sounds = []
        for row in cursor.fetchall():
            sounds.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "device_id": row[2],
                    "created_at": row[3],
                }
            )

        conn.close()
        return sounds

    except Exception as e:
        print(f"❌ Error getting excluded sounds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/excluded_sounds/{sound_id}")
async def delete_excluded_sound(sound_id: str):
    """Удаление исключенного звука"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM excluded_sounds WHERE id = ?", (sound_id,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sound not found")

        conn.commit()
        conn.close()

        print(f"🗑️ Deleted excluded sound: {sound_id}")

        return {"status": "deleted"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting excluded sound: {e}")
        raise HTTPException(status_code=500, detail=str(e))
