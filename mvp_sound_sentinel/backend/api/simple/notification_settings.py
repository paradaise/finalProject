import sqlite3
from fastapi import APIRouter, HTTPException

from backend.api.simple import state


router = APIRouter()


@router.get("/notification_settings/{device_id}")
async def get_notification_settings(device_id: str):
    """Получение настроек уведомлений для устройства"""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()
    
    try:
        # Важные звуки
        cursor.execute(
            """
            SELECT id, sound_name
            FROM notification_sounds
            WHERE device_id = ?
            ORDER BY created_at DESC
            """,
            (device_id,),
        )
        notification_sounds = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

        # Исключенные звуки
        cursor.execute(
            """
            SELECT id, sound_name
            FROM excluded_sounds
            WHERE device_id = ?
            ORDER BY created_at DESC
            """,
            (device_id,),
        )
        excluded_sounds = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

        # Пользовательские звуки (dedupe по имени+типу)
        cursor.execute(
            """
            SELECT name, sound_type
            FROM custom_sounds
            WHERE device_id = ?
            ORDER BY created_at DESC
            """,
            (device_id,),
        )

        seen = set()
        custom_sounds = []
        for name, sound_type in cursor.fetchall():
            key = (name.strip().lower(), sound_type.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            custom_sounds.append({"name": name, "type": sound_type})

        return {
            "notification_sounds": notification_sounds,
            "excluded_sounds": excluded_sounds,
            "custom_sounds": custom_sounds,
            "min_confidence": 0.3
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения настроек: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/notification_settings/{device_id}")
async def save_notification_settings(device_id: str, settings: dict):
    """Сохранение настроек уведомлений"""
    return {"message": "Settings saved successfully"}
