import sqlite3
import uuid
from datetime import datetime

from fastapi import APIRouter

from backend.api.simple.schemas import DeviceRegistration
from backend.api.simple import state
from backend.api.simple.ws import broadcast_to_websockets


router = APIRouter()


@router.post("/register_device")
async def register_device(device: DeviceRegistration):
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    # Проверяем, существует ли устройство с таким MAC адресом
    cursor.execute(
        "SELECT id FROM devices WHERE mac_address = ?", (device.mac_address,)
    )
    existing_device = cursor.fetchone()

    if existing_device:
        # Устройство уже существует, обновляем его
        device_id = existing_device[0]
        cursor.execute(
            """
            UPDATE devices 
            SET ip_address = ?, name = ?, model = ?, microphone_info = ?, 
                wifi_signal = ?, status = 'online', last_seen = ?
            WHERE id = ?
            """,
            (
                device.ip_address,
                device.name,
                device.model,
                device.microphone_info,
                device.wifi_signal,
                datetime.now().isoformat(),
                device_id,
            ),
        )
        print(f"🔄 Устройство обновлено: {device.name} (ID: {device_id})")
    else:
        # Новое устройство
        device_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO devices 
            (id, name, ip_address, mac_address, model, model_image_url, microphone_info, wifi_signal, status, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'online', ?)
            """,
            (
                device_id,
                device.name,
                device.ip_address,
                device.mac_address,
                device.model,
                device.model_image_url,
                device.microphone_info,
                device.wifi_signal,
                datetime.now().isoformat(),
            ),
        )
        print(f"🆕 Новое устройство: {device.name} (ID: {device_id})")

    conn.commit()
    conn.close()

    await broadcast_to_websockets(
        {"type": "device_registered", "device": device.dict()}
    )

    return {"device_id": device_id, "status": "registered"}
