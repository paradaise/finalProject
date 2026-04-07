import sqlite3
from datetime import datetime, timedelta
from fastapi import APIRouter

from backend.api.simple import state


router = APIRouter()


@router.delete("/cleanup_old_devices")
async def cleanup_old_devices():
    """Удаление устройств, которые не были в сети более 1 часа"""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    # Удаляем устройства, которые не были в сети более 1 часа
    cutoff_time = (datetime.now() - timedelta(hours=1)).isoformat()

    cursor.execute(
        "DELETE FROM devices WHERE last_seen < ? AND status != 'online'", (cutoff_time,)
    )

    deleted_count = cursor.rowcount

    # Также удаляем orphaned detections (без устройств)
    cursor.execute(
        """
        DELETE FROM sound_detections 
        WHERE device_id NOT IN (SELECT id FROM devices)
        """
    )

    orphaned_detections = cursor.rowcount

    # Удаляем дубликаты устройств (с одинаковым MAC адресом)
    cursor.execute(
        """
        DELETE FROM devices 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM devices 
            GROUP BY mac_address
        )
        """
    )

    duplicates_deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "deleted_devices": deleted_count + duplicates_deleted,
        "deleted_detections": orphaned_detections,
        "message": f"Удалено {deleted_count + duplicates_deleted} устройств и {orphaned_detections} детекций",
    }


@router.get("/device_count")
async def get_device_count():
    """Получение количества устройств"""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM devices")
    device_count = cursor.fetchone()[0]

    conn.close()

    return {"device_count": device_count}
