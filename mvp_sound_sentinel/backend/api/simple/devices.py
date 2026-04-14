import sqlite3

from fastapi import APIRouter

from backend.api.simple import state


router = APIRouter()


@router.get("/devices")
async def get_devices():
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM devices ORDER BY created_at DESC")
    devices = []

    for row in cursor.fetchall():
        devices.append(
            {
                "id": row[0],
                "name": row[1],
                "ip_address": row[2],
                "mac_address": row[3],
                "model": row[4],
                "model_image_url": row[5],
                "microphone_info": row[6],
                "wifi_signal": row[7],
                "status": row[8],
                "last_seen": row[9],
                "created_at": row[10],
                "cpu_usage": row[11] if len(row) > 11 else None,
                "device_temperature": row[12] if len(row) > 12 else None,
            }
        )

    conn.close()
    return {"devices": devices}
