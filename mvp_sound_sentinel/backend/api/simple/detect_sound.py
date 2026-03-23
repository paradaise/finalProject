import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict

import numpy as np
from fastapi import APIRouter

from backend.api.simple.schemas import AudioData
from backend.api.simple import state
from backend.api.simple.ws import broadcast_to_websockets


router = APIRouter()


@router.post("/detect_sound")
async def detect_sound(audio_data: AudioData) -> Dict[str, Any]:
    try:
        if state.model is None:
            return {"sound_type": "unknown", "confidence": 0.0}

        # Простая детекция
        audio_np = np.array(audio_data.audio_data, dtype=np.float32)
        scores, embeddings, _spectrogram = state.model(audio_np)

        scores_np = scores.numpy()
        max_index = int(np.argmax(scores_np))
        confidence = float(scores_np[0, max_index])
        sound_type = (
            state.class_names[max_index]
            if max_index < len(state.class_names)
            else "unknown"
        )

        # Сохраняем детекцию
        detection_id = str(uuid.uuid4())
        conn = sqlite3.connect(state.db_path)
        cursor = conn.cursor()

        timestamp = audio_data.timestamp or datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO sound_detections 
            (id, device_id, sound_type, confidence, timestamp, embeddings)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                detection_id,
                audio_data.device_id,
                sound_type,
                confidence,
                timestamp,
                str(embeddings.numpy().tolist()),
            ),
        )

        conn.commit()
        conn.close()

        await broadcast_to_websockets(
            {
                "type": "sound_detected",
                "detection": {
                    "id": detection_id,
                    "device_id": audio_data.device_id,
                    "sound_type": sound_type,
                    "confidence": confidence,
                    "timestamp": timestamp,
                },
            }
        )

        return {"sound_type": sound_type, "confidence": confidence}
    except Exception as e:
        print(f"❌ Ошибка детекции: {e}")
        return {"sound_type": "error", "confidence": 0.0}

