import sqlite3
import json
import uuid
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.api.simple import state
from backend.utils.yamnet import extract_embeddings as extract_yamnet_embeddings


router = APIRouter()


class TrainSoundRequest(BaseModel):
    name: str
    sound_type: str
    device_id: str
    audio_recordings: list[list[float]]
    sample_rate: Optional[int] = 16000
    threshold: Optional[float] = None


def _resample_audio_linear(audio: List[float], original_rate: int, target_rate: int) -> List[float]:
    """Lightweight resample without librosa/scipy."""
    if original_rate == target_rate:
        return audio

    import numpy as np

    x = np.asarray(audio, dtype=np.float32)
    if x.size == 0:
        return []

    ratio = float(target_rate) / float(original_rate)
    new_len = max(1, int(round(x.size * ratio)))
    xp = np.arange(x.size, dtype=np.float32)
    fp = x
    x_new = np.linspace(0, x.size - 1, new_len, dtype=np.float32)
    y_new = np.interp(x_new, xp, fp).astype(np.float32)
    return y_new.tolist()


@router.post("/custom_sounds/train")
async def train_custom_sound(request: TrainSoundRequest):
    """Тренировка и добавление нового кастомного звука из аудио записей"""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    try:
        print(f"🎵 Обучение звука: {request.name}")

        if state.model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")

        import numpy as np

        sample_rate = request.sample_rate or 16000
        default_threshold = float(os.getenv("CUSTOM_MATCH_DEFAULT_THRESHOLD", "0.75"))
        resolved_threshold = (
            float(request.threshold) if request.threshold is not None else default_threshold
        )

        all_embeddings = []
        for recording in request.audio_recordings:
            try:
                audio_16k = (
                    _resample_audio_linear(recording, sample_rate, 16000)
                    if sample_rate != 16000
                    else recording
                )
                embedding = extract_yamnet_embeddings(audio_16k, state.model)
                if embedding:
                    all_embeddings.append(embedding)
            except Exception as e:
                print(f"⚠️ Ошибка извлечения embeddings: {e}")
                continue

        if not all_embeddings:
            raise HTTPException(
                status_code=400, detail="Failed to extract embeddings from audio"
            )

        centroid = np.mean(all_embeddings, axis=0).tolist()

        sound_id = str(uuid.uuid4())

        # Не плодим дубли одинакового имени/типа для одного устройства.
        cursor.execute(
            """
            DELETE FROM custom_sounds
            WHERE device_id = ? AND LOWER(name) = LOWER(?) AND LOWER(sound_type) = LOWER(?)
            """,
            (request.device_id, request.name, request.sound_type),
        )

        cursor.execute(
            """
            INSERT INTO custom_sounds 
            (id, name, sound_type, embeddings, centroid, threshold, device_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sound_id,
                request.name,
                request.sound_type,
                json.dumps(all_embeddings),
                json.dumps(centroid),
                resolved_threshold,
                request.device_id,
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        print(f"✅ Звук обучен и добавлен: {request.name}")

        return {
            "id": sound_id,
            "name": request.name,
            "sound_type": request.sound_type,
            "centroid": centroid,
            "message": "Sound trained and added successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка обучения звука: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/custom_sounds/{sound_id}")
async def delete_custom_sound(sound_id: str):
    """Удаление кастомного звука"""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM custom_sounds WHERE id = ?", (sound_id,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sound not found")

        conn.commit()
        print(f"🗑️ Удален кастомный звук: {sound_id}")

        return {"message": "Sound deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка удаления звука: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/custom_sounds")
async def get_custom_sounds():
    """Получение всех кастомных звуков"""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name, sound_type, embeddings, centroid, threshold, device_id, created_at
            FROM custom_sounds
            ORDER BY created_at DESC
            """
        )

        sounds = []
        seen = set()
        for row in cursor.fetchall():
            key = (row[1].strip().lower(), row[2].strip().lower(), (row[6] or "").strip().lower())
            if key in seen:
                continue
            seen.add(key)
            sounds.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "sound_type": row[2],
                    "embeddings": json.loads(row[3]) if row[3] else [],
                    "centroid": json.loads(row[4]) if row[4] else [],
                    "threshold": row[5],
                    "device_id": row[6],
                    "created_at": row[7],
                }
            )

        return sounds

    except Exception as e:
        print(f"❌ Ошибка получения звуков: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
