#!/usr/bin/env python3
"""
Save Notification Settings API
Эндпоинт для сохранения настроек уведомлений
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uuid
from datetime import datetime

from backend.api.simple.state import db_path

router = APIRouter()


class NotificationSettings(BaseModel):
    notification_sounds: List[dict] = []
    excluded_sounds: List[dict] = []
    min_confidence: float = 0.3


class SoundItem(BaseModel):
    id: Optional[str] = None
    name: str


@router.post("/notification_settings/{device_id}")
async def save_notification_settings(device_id: str, settings: NotificationSettings):
    """Сохранение настроек уведомлений для устройства"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Проверяем существование устройства
        cursor.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Device not found")

        # Очищаем старые настройки
        cursor.execute(
            "DELETE FROM notification_sounds WHERE device_id = ?", (device_id,)
        )
        cursor.execute("DELETE FROM excluded_sounds WHERE device_id = ?", (device_id,))

        # Добавляем важные звуки
        for sound in settings.notification_sounds:
            sound_id = sound.get("id") or str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO notification_sounds (id, sound_name, device_id)
                VALUES (?, ?, ?)
                """,
                (sound_id, sound["name"], device_id),
            )

        # Добавляем исключенные звуки
        for sound in settings.excluded_sounds:
            sound_id = sound.get("id") or str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO excluded_sounds (id, sound_name, device_id)
                VALUES (?, ?, ?)
                """,
                (sound_id, sound["name"], device_id),
            )

        conn.commit()

        return {
            "status": "success",
            "message": "Notification settings saved successfully",
            "notification_sounds_count": len(settings.notification_sounds),
            "excluded_sounds_count": len(settings.excluded_sounds),
            "min_confidence": settings.min_confidence,
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
