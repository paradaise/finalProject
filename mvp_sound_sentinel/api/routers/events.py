import uuid
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..database import get_db_connection
from ..models.schemas import AudioData
from ..services.sound_detection import (
    extract_embeddings,
    find_best_custom_match,
    detect_sound_from_audio_data,
    should_send_notification,
)
from ..websocket.connection_manager import manager
from ..core import config

router = APIRouter()


@router.post("/detect_sound")
async def detect_sound_endpoint(audio: AudioData):
    """Детекция звука с поддержкой custom sounds через YAMNet embeddings"""
    if config.MODEL is None:
        raise HTTPException(status_code=503, detail="Модель не загружена")

    embedding = extract_embeddings(audio.audio_data)
    if not embedding:
        raise HTTPException(status_code=400, detail="Не удалось извлечь embeddings")

    detection_id = str(uuid.uuid4())
    custom_match = find_best_custom_match(embedding, audio.device_id)

    final_result = {
        "detection_id": detection_id,
        "device_id": audio.device_id,
        "timestamp": datetime.now().isoformat(),
        "is_custom": False,
        "custom_sound_type": None,
        "sound_type": None,
        "confidence": 0.0,
        "should_notify": False,
    }

    if custom_match and custom_match.get("similarity", 0) > custom_match.get(
        "threshold", 0.75
    ):
        sound_type = custom_match["sound_type"]
        final_result.update(
            {
                "is_custom": True,
                "custom_sound_type": sound_type,
                "sound_type": custom_match["name"],
                "confidence": custom_match["similarity"],
                "should_notify": sound_type == "specific",
            }
        )
    else:
        detection_result = detect_sound_from_audio_data(audio.audio_data)
        if detection_result["predictions"]:
            top_prediction = detection_result["predictions"][0]
            final_result.update(
                {
                    "sound_type": top_prediction["sound_type"],
                    "confidence": top_prediction["confidence"],
                    "should_notify": should_send_notification(
                        audio.device_id, top_prediction["sound_type"]
                    ),
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Не удалось детектировать звук")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sound_detections (id, device_id, sound_type, confidence, timestamp, embeddings) VALUES (?, ?, ?, ?, ?, ?)",
        (
            detection_id,
            audio.device_id,
            final_result["sound_type"],
            final_result["confidence"],
            final_result["timestamp"],
            json.dumps(embedding),
        ),
    )
    conn.commit()
    conn.close()

    await manager.broadcast(
        {
            "type": "sound_detected",
            "detection_id": detection_id,
            "device_id": audio.device_id,
            "sound_type": final_result["sound_type"],
            "confidence": final_result["confidence"],
            "timestamp": final_result["timestamp"],
            "should_notify": final_result["should_notify"],
            "is_custom": final_result["is_custom"],
            "custom_sound_type": final_result["custom_sound_type"],
        }
    )

    return {
        "detection_id": detection_id,
        "sound_type": final_result["sound_type"],
        "confidence": final_result["confidence"],
    }


@router.get("/detections/{device_id}")
async def get_device_detections(device_id: str, limit: int = 1000):
    """Получение всех детекций для указанного устройства"""
    conn = get_db_connection()
    try:
        detections = conn.execute(
            "SELECT * FROM sound_detections WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?",
            (device_id, limit),
        ).fetchall()
        return [dict(row) for row in detections]
    finally:
        conn.close()


@router.delete("/devices/{device_id}/detections")
async def clear_device_detections(device_id: str):
    """Удаление всех детекций для указанного устройства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Device not found")
        cursor.execute("DELETE FROM sound_detections WHERE device_id = ?", (device_id,))
        conn.commit()
        await manager.broadcast({"type": "detections_cleared", "device_id": device_id})
        return {"status": "success"}
    finally:
        conn.close()


@router.get("/yamnet_sounds")
async def get_yamnet_sounds():
    """Получение полного списка звуков YAMNet"""
    return config.CLASS_NAMES


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
