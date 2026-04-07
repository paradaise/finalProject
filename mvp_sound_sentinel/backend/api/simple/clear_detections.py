import sqlite3
from fastapi import APIRouter, HTTPException

from backend.api.simple import state

router = APIRouter()

@router.delete("/devices/{device_id}/detections")
async def clear_device_detections(device_id: str):
    """Удаление всех детекций для указанного устройства"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()
        
        # Сначала проверяем существует ли устройство
        cursor.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Удаляем все детекции для устройства
        cursor.execute("DELETE FROM sound_detections WHERE device_id = ?", (device_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"🗑️ Deleted {deleted_count} detections for device {device_id}")
        
        return {"status": "cleared", "deleted_count": deleted_count}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error clearing detections: {e}")
        raise HTTPException(status_code=500, detail=str(e))
