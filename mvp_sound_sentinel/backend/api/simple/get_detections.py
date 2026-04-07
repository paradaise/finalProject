import sqlite3
import json
from fastapi import APIRouter, HTTPException, Query

from backend.api.simple import state

router = APIRouter()

@router.get("/detections/{device_id}")
async def get_detections(device_id: str, limit: int = Query(default=1000, le=10000)):
    """Получение детекций для устройства"""
    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()
        
        # Проверяем существует ли устройство
        cursor.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Получаем детекции
        cursor.execute(
            """
            SELECT id, device_id, sound_type, confidence, timestamp, embeddings
            FROM sound_detections 
            WHERE device_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """,
            (device_id, limit)
        )
        
        detections = []
        for row in cursor.fetchall():
            detections.append({
                "id": row[0],
                "device_id": row[1],
                "sound_type": row[2],
                "confidence": row[3],
                "timestamp": row[4],
                "embeddings": json.loads(row[5]) if row[5] else [],
            })
        
        # Получаем общее количество
        cursor.execute(
            "SELECT COUNT(*) FROM sound_detections WHERE device_id = ?",
            (device_id,)
        )
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {"detections": detections, "total_count": total_count}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting detections: {e}")
        raise HTTPException(status_code=500, detail=str(e))
