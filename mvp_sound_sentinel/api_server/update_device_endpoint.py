# Добавьте этот код в main.py API сервера


@app.put("/update_device/{device_id}")
async def update_device(device_id: str, device_update: dict):
    """Обновление информации об устройстве (WiFi, микрофон и т.д.)"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE devices 
            SET wifi_signal = ?, microphone_info = ?, last_seen = ?
            WHERE id = ?
            """,
            (
                device_update.get("wifi_signal", 0),
                device_update.get("microphone_info", "Unknown"),
                device_update.get("last_seen", datetime.now().isoformat()),
                device_id,
            ),
        )

        conn.commit()

        # Отправляем WebSocket обновление
        if websocket_connections:
            message = {
                "type": "device_updated",
                "device_id": device_id,
                "device_info": device_update,
            }
            message_str = json.dumps(message)
            for websocket in websocket_connections.copy():
                try:
                    await websocket.send_text(message_str)
                except:
                    websocket_connections.discard(websocket)

        return {"status": "success", "message": "Device updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
