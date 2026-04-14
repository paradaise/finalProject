import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict

import numpy as np
from fastapi import APIRouter

from backend.api.simple.schemas import AudioData
from backend.api.simple import state
from backend.api.simple.ws import broadcast_to_websockets
from backend.utils.custom_matching import find_best_custom_match
from backend.utils.notifications import should_send_notification
from backend.utils.yamnet_cached import extract_embeddings as extract_yamnet_embeddings


router = APIRouter()


def _resample_audio_linear(
    audio: np.ndarray, original_rate: int, target_rate: int
) -> np.ndarray:
    """Lightweight resample without librosa/scipy."""
    if original_rate == target_rate:
        return audio
    if audio.size == 0:
        return audio
    ratio = float(target_rate) / float(original_rate)
    new_len = max(1, int(round(audio.size * ratio)))
    xp = np.arange(audio.size, dtype=np.float32)
    x_new = np.linspace(0, audio.size - 1, new_len, dtype=np.float32)
    return np.interp(x_new, xp, audio).astype(np.float32)


@router.post("/detect_sound")
async def detect_sound(audio_data: AudioData) -> Dict[str, Any]:
    try:
        if state.model is None:
            return {"sound_type": "unknown", "confidence": 0.0}

        # Конвертируем аудио в numpy array
        audio_np = np.array(audio_data.audio_data, dtype=np.float32)

        if audio_data.sample_rate != 16000:
            audio_np = _resample_audio_linear(audio_np, audio_data.sample_rate, 16000)
            print(f"🔄 Ресемплинг: {audio_data.sample_rate} -> 16000 Hz")

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

        # Custom sounds matching using embeddings centroid similarity.
        embedding_mean = np.mean(embeddings.numpy(), axis=0).tolist()
        custom_match = find_best_custom_match(
            embedding_mean, audio_data.device_id, state.db_path
        )

        is_custom = False
        custom_sound_type = None
        if custom_match:
            similarity = float(custom_match.get("similarity", 0.0) or 0.0)
            threshold = float(custom_match.get("threshold", 0.7) or 0.7)

            # Additional validation: require minimum similarity for specific sounds
            if custom_match.get("sound_type") == "specific" and similarity >= threshold:
                is_custom = True
                custom_sound_type = custom_match.get("sound_type")
                sound_type = custom_match.get("name", sound_type)
                confidence = similarity
                print(f"   {sound_type}: {similarity:.3f} (threshold: {threshold:.3f})")
            elif (
                custom_match.get("sound_type") == "excluded" and similarity >= threshold
            ):
                # For excluded sounds, we can be slightly more lenient
                is_custom = True
                custom_sound_type = custom_match.get("sound_type")
                sound_type = custom_match.get("name", sound_type)
                confidence = similarity
                print(f"   {sound_type}: {similarity:.3f} (threshold: {threshold:.3f})")
            else:
                print(
                    f"   {custom_match.get('name', 'unknown')}: {similarity:.3f} (below threshold: {threshold:.3f})"
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
                str(embedding_mean),
            ),
        )

        conn.commit()
        conn.close()

        should_notify = (
            (custom_sound_type == "specific")
            if is_custom
            else should_send_notification(
                state.db_path, audio_data.device_id, sound_type
            )
        )

        await broadcast_to_websockets(
            {
                "type": "sound_detected",
                "device_id": audio_data.device_id,
                "sound_type": sound_type,
                "confidence": confidence,
                "timestamp": timestamp,
                "should_notify": should_notify,
                "is_custom": is_custom,
                "custom_sound_type": custom_sound_type,
                "db_level": audio_data.db_level,
            }
        )

        return {"sound_type": sound_type, "confidence": confidence}
    except Exception as e:
        print(f"❌ Ошибка детекции: {e}")
        return {"sound_type": "error", "confidence": 0.0}
