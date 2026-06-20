#!/usr/bin/env python3
"""
Update Device Info API
Эндпоинт для обновления информации об устройстве (WiFi, микрофон и т.д.)
"""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
from datetime import datetime

from backend.api.simple import state

router = APIRouter()


class DeviceInfoUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    model: Optional[str] = None
    wifi_signal: Optional[int] = None
    cpu_usage: Optional[float] = None
    device_temperature: Optional[float] = None
    microphone_info: Optional[str] = None
    last_seen: Optional[str] = None


@router.put("/update_device/{device_id}")
async def update_device_info(
    device_id: str,
    device_update: DeviceInfoUpdate,
    x_device_id: Optional[str] = Header(default=None),
):
    """Update device information (WiFi, microphone, etc.)"""
    if x_device_id and x_device_id != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")

    try:
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()

        # Проверяем существует ли устройство
        cursor.execute("SELECT COUNT(*) FROM devices WHERE id = ?", (device_id,))
        device_exists = cursor.fetchone()[0] > 0

        if not device_exists:
            # Создаем устройство если его нет
            cursor.execute(
                """
                INSERT INTO devices (id, name, ip_address, mac_address, model, wifi_signal, cpu_usage, device_temperature, microphone_info, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    device_update.name or f"Device {device_id[:8]}",
                    device_update.ip_address or "Unknown",
                    device_update.mac_address or "Unknown",
                    device_update.model or "Unknown",
                    device_update.wifi_signal or 0,
                    device_update.cpu_usage,
                    device_update.device_temperature,
                    device_update.microphone_info or "Unknown",
                    device_update.last_seen or datetime.now().isoformat(),
                ),
            )
            print(f"✅ Устройство создано: {device_id}")
        else:
            # Обновляем существующее устройство
            update_fields = []
            update_values = []

            if device_update.name is not None:
                update_fields.append("name = ?")
                update_values.append(device_update.name)

            if device_update.ip_address is not None:
                update_fields.append("ip_address = ?")
                update_values.append(device_update.ip_address)

            if device_update.mac_address is not None:
                update_fields.append("mac_address = ?")
                update_values.append(device_update.mac_address)

            if device_update.model is not None:
                update_fields.append("model = ?")
                update_values.append(device_update.model)

            if device_update.wifi_signal is not None:
                update_fields.append("wifi_signal = ?")
                update_values.append(device_update.wifi_signal)

            if device_update.cpu_usage is not None:
                update_fields.append("cpu_usage = ?")
                update_values.append(device_update.cpu_usage)

            if device_update.device_temperature is not None:
                update_fields.append("device_temperature = ?")
                update_values.append(device_update.device_temperature)

            if device_update.microphone_info is not None:
                update_fields.append("microphone_info = ?")
                update_values.append(device_update.microphone_info)

            # Всегда обновляем last_seen
            update_fields.append("last_seen = ?")
            update_values.append(device_update.last_seen or datetime.now().isoformat())

            if update_fields:
                query = f"UPDATE devices SET {', '.join(update_fields)} WHERE id = ?"
                update_values.append(device_id)
                cursor.execute(query, (*update_values,))

                # Логируем WiFi|CPU|Температуру если они есть
                log_parts = []
                if device_update.wifi_signal is not None:
                    log_parts.append(f"WiFi {device_update.wifi_signal}%")
                if device_update.cpu_usage is not None:
                    log_parts.append(f"CPU {device_update.cpu_usage:.1f}%")
                if device_update.device_temperature is not None:
                    log_parts.append(f"Temp {device_update.device_temperature:.1f}°C")

                if log_parts:
                    print(f"PUT success: {' | '.join(log_parts)}")

                print(f"Device updated: {device_id}")
            else:
                print(f"No fields to update for device: {device_id}")

        conn.commit()

        # Отправляем WebSocket обновление
        from backend.api.simple.ws import broadcast_to_websockets

        payload = device_update.model_dump(exclude_none=True)
        await broadcast_to_websockets(
            {
                "type": "device_updated",
                "device_id": device_id,
                "device_info": payload,
            }
        )

        return {"status": "success", "message": "Device info updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
