import sqlite3
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from backend.api.simple import state

router = APIRouter()


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    last_seen: Optional[str] = None
    wifi_signal: Optional[int] = None
    cpu_usage: Optional[float] = None
    device_temperature: Optional[float] = None


@router.put("/update_device/{device_id}")
async def update_device(device_id: str, device_update: DeviceUpdate):
    """Обновление информации об устройстве"""
    try:
        print(f"📝 Updating device {device_id} with data: {device_update.dict()}")
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()

        # Определяем какие поля нужно обновить
        updates = []
        params = []

        if device_update.name is not None:
            updates.append("name = ?")
            params.append(device_update.name)

        if device_update.status is not None:
            updates.append("status = ?")
            params.append(device_update.status)

        if device_update.last_seen is not None:
            updates.append("last_seen = ?")
            params.append(device_update.last_seen)

        if device_update.wifi_signal is not None:
            updates.append("wifi_signal = ?")
            params.append(device_update.wifi_signal)

        if device_update.cpu_usage is not None:
            updates.append("cpu_usage = ?")
            params.append(device_update.cpu_usage)

        if device_update.device_temperature is not None:
            updates.append("device_temperature = ?")
            params.append(device_update.device_temperature)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Добавляем device_id в параметры
        params.append(device_id)

        # Выполняем обновление
        query = f"UPDATE devices SET {', '.join(updates)} WHERE id = ?"
        print(f"🔍 SQL Query: {query}")
        print(f"🔍 SQL Params: {params}")
        cursor.execute(query, params)

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Device not found")

        conn.commit()
        conn.close()

        print(f"✅ Device {device_id} updated successfully")
        return {"status": "updated", "device_id": device_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating device: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
