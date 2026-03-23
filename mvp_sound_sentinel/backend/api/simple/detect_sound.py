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

        # Конвертируем аудио в numpy array
        audio_np = np.array(audio_data.audio_data, dtype=np.float32)

        # Простой ресемплинг без librosa
        if audio_data.sample_rate != 16000:
            if audio_data.sample_rate == 44100:
                # Даунсэмплинг с 44100 до 16000
                step = audio_data.sample_rate // 16000  # 44100 // 16000 = 2
                audio_np = audio_np[::step]
                # Корректируем длину
                target_length = int(len(audio_np) * 16000 / audio_data.sample_rate)
                audio_np = audio_np[:target_length]
                print(f"🔄 Ресемплинг: {audio_data.sample_rate} -> 16000 Hz")
            else:
                print(f"⚠️ Несовместимая частота {audio_data.sample_rate} Hz")
                return {"sound_type": "error", "confidence": 0.0}

        # YAMNet ожидает аудио длиной 0.96 секунды (15300 сэмплов)
        # Если аудио короче, дополняем нулями
        target_length = 15300  # 0.96s * 16000Hz
        if len(audio_np) < target_length:
            audio_np = np.pad(
                audio_np, (0, target_length - len(audio_np)), mode="constant"
            )
        elif len(audio_np) > target_length:
            audio_np = audio_np[:target_length]

        # Детекция
        scores, embeddings, _spectrogram = state.model(audio_np)

        scores_np = scores.numpy()
        print(f"🔍 Размер scores: {scores_np.shape}")

        # Проверяем размер scores
        if len(scores_np.shape) > 1:
            scores_np = scores_np.flatten()

        if len(scores_np) == 0:
            print("❌ Пустой массив scores")
            return {"sound_type": "error", "confidence": 0.0}

        max_index = int(np.argmax(scores_np))
        confidence = float(scores_np[max_index])

        # Проверяем индекс
        if max_index >= len(state.class_names):
            print(
                f"❌ Индекс {max_index} больше количества классов {len(state.class_names)}"
            )
            max_index = 0

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
