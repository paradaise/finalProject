import sqlite3
from fastapi import APIRouter, HTTPException

from backend.api.simple import state


router = APIRouter()


@router.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    """Удаление устройства и всех его детекций"""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()
    
    try:
        # Сначала удаляем все детекции устройства
        cursor.execute(
            "DELETE FROM sound_detections WHERE device_id = ?",
            (device_id,)
        )
        deleted_detections = cursor.rowcount
        
        # Затем удаляем само устройство
        cursor.execute(
            "DELETE FROM devices WHERE id = ?",
            (device_id,)
        )
        deleted_device = cursor.rowcount
        
        conn.commit()
        
        if deleted_device == 0:
            raise HTTPException(status_code=404, detail="Device not found")
        
        print(f"🗑️ Удалено устройство: {device_id} ({deleted_detections} детекций)")
        
        return {
            "message": "Device and associated detections deleted successfully",
            "deleted_detections": deleted_detections
        }
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка удаления устройства: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
