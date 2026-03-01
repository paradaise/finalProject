#!/usr/bin/env python3
"""
Sound Sentinel MVP - API Server
Простой и надежный API сервер для детекции звуков
"""

import os
import sqlite3
import json
import uuid
import warnings
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
import librosa
import tensorflow as tf
import tensorflow_hub as hub

# Подавляем warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

# Получаем абсолютный путь к директории, где находится скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется при старте
    print("--- Server starting up ---")
    init_database()
    success = load_model()
    if not success:
        print("⚠️ Модель не загружена. Сервер будет работать в ограниченном режиме.")
    yield
    # Код, который выполняется при остановке
    print("--- Server shutting down ---")


# Инициализация FastAPI
app = FastAPI(title="Sound Sentinel MVP", version="1.0.0", lifespan=lifespan)

# CORS для мобильного приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
db_path = "soundsentinel.db"
model = None
class_names = []
websocket_connections = set()


# Модели данных
class DeviceRegistration(BaseModel):
    model_config = {"protected_namespaces": ()}
    name: str
    ip_address: str
    mac_address: str
    model: str
    model_image_url: Optional[str] = None
    microphone_info: Optional[str] = None
    wifi_signal: int = 0  # dBm


class AudioData(BaseModel):
    device_id: str
    audio_data: List[float]  # 16kHz, mono
    sample_rate: int = 16000
    db_level: Optional[float] = None


class SoundDetection(BaseModel):
    device_id: str
    sound_type: str
    confidence: float
    timestamp: str
    audio_data: List[float]


class CustomSound(BaseModel):
    name: str
    sound_type: str  # "specific" или "excluded"
    embeddings: List[float]  # YAMNet embeddings
    device_id: str
    threshold: float = 0.75  # Порог схожести


class AudioLevel(BaseModel):
    device_id: str
    db_level: float
    timestamp: str


@app.post("/update_audio_level")
async def update_audio_level(data: AudioLevel):
    """Обновление только уровня звука без детекции"""
    await broadcast_to_websockets(
        {
            "type": "audio_level_updated",
            "device_id": data.device_id,
            "db_level": data.db_level,
            "timestamp": data.timestamp,
        }
    )
    return {"status": "success"}


class DeviceUpdate(BaseModel):
    device_id: str
    wifi_signal: Optional[int] = None
    microphone_info: Optional[str] = None
    model: Optional[str] = None
    last_seen: Optional[str] = None


@app.put("/devices/{device_id}")
async def update_device(device_id: str, device_update: DeviceUpdate):
    """Обновление информации об устройстве"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Обновляем только переданные поля
        update_fields = []
        update_values = []

        if device_update.wifi_signal is not None:
            update_fields.append("wifi_signal = ?")
            update_values.append(device_update.wifi_signal)

        if device_update.microphone_info is not None:
            update_fields.append("microphone_info = ?")
            update_values.append(device_update.microphone_info)

        if device_update.model is not None:
            update_fields.append("model = ?")
            update_values.append(device_update.model)

        # Всегда обновляем last_seen
        update_fields.append("last_seen = ?")
        update_values.append(device_update.last_seen or datetime.now().isoformat())

        if update_fields:
            sql = f"UPDATE devices SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, update_values + [device_id])
            conn.commit()

            # Рассылка обновления через WebSocket
            await broadcast_to_websockets(
                {
                    "type": "device_updated",
                    "device_id": device_id,
                    "device_info": device_update.dict(),
                }
            )

            print(f"🔄 Устройство обновлено: {device_id}")

        conn.close()
        return {"status": "success"}

    except Exception as e:
        print(f"❌ Ошибка обновления устройства: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class NotificationSound(BaseModel):
    sound_name: str
    device_id: str


class ExcludedSound(BaseModel):
    sound_name: str
    device_id: str


# Инициализация базы данных
def init_database():
    """Создание таблиц в SQLite"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Таблица устройств
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            mac_address TEXT NOT NULL,
            model TEXT DEFAULT 'Unknown',
            model_image_url TEXT,
            microphone_info TEXT,
            wifi_signal INTEGER DEFAULT 0,
            status TEXT DEFAULT 'offline',
            last_seen TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Таблица детекций звуков
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sound_detections (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            sound_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp TEXT NOT NULL,
            embeddings TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """
    )

    # Таблица пользовательских звуков с YAMNet embeddings
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_sounds (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            name TEXT NOT NULL,
            sound_type TEXT NOT NULL CHECK (sound_type IN ('specific', 'excluded')),
            embeddings TEXT,
            centroid TEXT,
            threshold REAL DEFAULT 0.75,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """
    )

    # Таблица важных звуков для уведомлений
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_sounds (
            id TEXT PRIMARY KEY,
            sound_name TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id),
            UNIQUE(sound_name, device_id)
        )
    """
    )

    # Таблица исключенных звуков
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS excluded_sounds (
            id TEXT PRIMARY KEY,
            sound_name TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id),
            UNIQUE(sound_name, device_id)
        )
    """
    )

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


# Загрузка YAMNet модели
def load_model():
    """Загрузка предобученной модели YAMNet"""
    global model, class_names
    try:
        print("🔄 Загрузка YAMNet модели...")

        # Очищаем кэш если есть проблемы
        import tempfile

        cache_dir = os.path.join(tempfile.gettempdir(), "tfhub_modules")
        if os.path.exists(cache_dir):
            import shutil

            try:
                shutil.rmtree(cache_dir)
                print("🧹 Старый кэш TensorFlow Hub удалён")
            except:
                pass

        # Загружаем модель
        model = hub.load("https://tfhub.dev/google/yamnet/1")

        # Загрузка названий классов
        class_names_path = tf.keras.utils.get_file(
            "yamnet_class_map.csv",
            "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv",
        )
        class_names = []
        with open(class_names_path, "r") as f:
            next(f)  # Пропуск заголовка
            for line in f:
                class_names.append(line.strip().split(",")[2])

        print(f"✅ YAMNet модель загружена. Классов: {len(class_names)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return False


# Извлечение YAMNet embeddings
def extract_embeddings(audio_data: List[float]) -> List[float]:
    """Извлечение YAMNet embeddings из аудио"""
    try:
        # Конвертация в numpy array
        audio_np = np.array(audio_data, dtype=np.float32)

        # YAMNet ожидает моно 16kHz
        if len(audio_np.shape) > 1:
            audio_np = audio_np[:, 0]  # Берем первый канал

        # Запуск модели для получения embeddings
        scores, embeddings, spectrogram = model(audio_np)

        # Возвращаем средний embedding по времени (1024-d вектор)
        embedding_mean = np.mean(embeddings.numpy(), axis=0)

        return embedding_mean.tolist()
    except Exception as e:
        print(f"❌ Ошибка извлечения embeddings: {e}")
        return []


# Косинусное расстояние между векторами
def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Вычисление косинусного расстояния"""
    try:
        a_np = np.array(a)
        b_np = np.array(b)

        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)
    except Exception as e:
        print(f"❌ Ошибка вычисления cosine similarity: {e}")
        return 0.0


# Поиск лучшего совпадения среди custom sounds
def find_best_custom_match(embedding: List[float], device_id: str) -> dict:
    """Поиск лучшего совпадения embedding с custom sounds"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем все custom sounds для устройства
        cursor.execute(
            """
            SELECT id, name, sound_type, embeddings, centroid, threshold 
            FROM custom_sounds 
            WHERE device_id = ?
        """,
            (device_id,),
        )

        custom_sounds = cursor.fetchall()
        conn.close()

        best_match = None
        best_similarity = 0.0

        for sound in custom_sounds:
            sound_id, name, sound_type, embeddings_str, centroid_str, threshold = sound

            print(f"🔍 Проверяем custom sound: {name} (type: {sound_type})")

            # Парсим centroid (если есть) или вычисляем из embeddings
            try:
                if centroid_str:
                    centroid = json.loads(centroid_str)
                    # Конвертируем numpy array в список если нужно
                    if hasattr(centroid, "tolist"):
                        centroid = centroid.tolist()
                    elif isinstance(centroid, np.ndarray):
                        centroid = centroid.tolist()
                    # Если centroid это число (float), используем embeddings
                    elif isinstance(centroid, (int, float)):
                        print(
                            f"⚠️ Centroid это число ({centroid}), используем embeddings"
                        )
                        embeddings = (
                            json.loads(embeddings_str) if embeddings_str else []
                        )
                        if embeddings and len(embeddings) > 0:
                            # Убедимся что embeddings это 2D массив
                            if isinstance(embeddings[0], list):
                                # embeddings это массив массивов [[...], [...], [...]]
                                centroid = np.mean(embeddings, axis=0).tolist()
                            else:
                                # embeddings это плоский массив [...] - создаем из него centroid
                                centroid = embeddings
                            print(
                                f"✅ Centroid вычислен из embeddings: {len(centroid)} элементов"
                            )
                        else:
                            print(f"❌ Нет embeddings для звука {name}")
                            continue
                    print(
                        f"✅ Centroid загружен: {len(centroid) if isinstance(centroid, list) else 'not array'}"
                    )
                else:
                    embeddings = json.loads(embeddings_str) if embeddings_str else []
                    if embeddings:
                        centroid = np.mean(embeddings, axis=0).tolist()
                        print(f"✅ Centroid вычислен: {len(centroid)} элементов")
                    else:
                        print(f"❌ Нет embeddings для звука {name}")
                        continue
            except Exception as e:
                print(f"❌ Ошибка парсинга centroid для {name}: {e}")
                continue

            # Убедимся что centroid это список чисел
            if not isinstance(centroid, list):
                print(f"❌ Centroid не является списком для {name}: {type(centroid)}")
                continue

            # Вычисляем схожесть
            try:
                similarity = cosine_similarity(embedding, centroid)
                print(f"📊 Схожесть с {name}: {similarity:.3f}")
            except Exception as e:
                print(f"❌ Ошибка вычисления схожести с {name}: {e}")
                continue

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    "id": sound_id,
                    "name": name,
                    "sound_type": sound_type,  # 'specific' или 'excluded'
                    "similarity": similarity,
                    "threshold": threshold or 0.75,
                }
                print(f"🎯 Новый лучший матч: {name} (схожесть: {similarity:.3f})")

        return best_match or {}

    except Exception as e:
        print(f"❌ Ошибка поиска custom match: {e}")
        return {}


# Проверка настроек уведомлений
def should_send_notification(device_id: str, sound_type: str) -> bool:
    """Проверяет нужно ли отправлять уведомление для данного звука"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверяем исключенные звуки
    cursor.execute(
        """
        SELECT COUNT(*) FROM excluded_sounds 
        WHERE device_id = ? AND LOWER(sound_name) = LOWER(?)
    """,
        (device_id, sound_type),
    )

    if cursor.fetchone()[0] > 0:
        conn.close()
        return False

    # Проверяем важные звуки
    cursor.execute(
        """
        SELECT COUNT(*) FROM notification_sounds 
        WHERE device_id = ? AND LOWER(sound_name) = LOWER(?)
    """,
        (device_id, sound_type),
    )

    if cursor.fetchone()[0] > 0:
        conn.close()
        return True

    # Проверяем пользовательские звуки
    cursor.execute(
        """
        SELECT sound_type FROM custom_sounds 
        WHERE device_id = ? AND LOWER(name) = LOWER(?)
    """,
        (device_id, sound_type),
    )

    custom_sound = cursor.fetchone()
    conn.close()

    if custom_sound:
        return custom_sound[0] == "notification"

    # По умолчанию не отправляем уведомления
    return False


# Детекция звука с помощью YAMNet
def detect_sound(audio_data: List[float]) -> Dict:
    """Детекция звука с помощью YAMNet"""
    try:
        # Конвертация в numpy array
        audio_np = np.array(audio_data, dtype=np.float32)

        # YAMNet ожидает моно 16kHz
        if len(audio_np.shape) > 1:
            audio_np = audio_np[:, 0]  # Берем первый канал

        # Запуск модели
        scores, embeddings, spectrogram = model(audio_np)

        # Получение топ-5 предсказаний
        top_scores = tf.math.top_k(scores, k=5)

        results = []
        for i in range(5):
            class_id = top_scores.indices[0][i].numpy()
            confidence = top_scores.values[0][i].numpy()
            class_name = class_names[class_id]

            results.append({"sound_type": class_name, "confidence": float(confidence)})

        return {"predictions": results, "embeddings": embeddings.numpy().tolist()}
    except Exception as e:
        print(f"❌ Ошибка детекции: {e}")
        return {"predictions": [], "embeddings": []}


# WebSocket менеджер
async def broadcast_to_websockets(message: dict):
    """Рассылка сообщения всем подключенным WebSocket клиентам"""
    if websocket_connections:
        message_str = json.dumps(message)
        disconnected = set()
        for websocket in websocket_connections:
            try:
                await websocket.send_text(message_str)
            except:
                disconnected.add(websocket)

        # Удаление отключенных соединений
        websocket_connections.difference_update(disconnected)


# API эндпоинты


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для реального времени"""
    await websocket.accept()
    websocket_connections.add(websocket)

    try:
        while True:
            await websocket.receive_text()  # Поддержание соединения
    except WebSocketDisconnect:
        websocket_connections.discard(websocket)


@app.post("/register_device")
async def register_device(device: DeviceRegistration):
    """Регистрация нового устройства или обновление существующего"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверяем существует ли устройство с таким MAC адресом
    cursor.execute(
        "SELECT id FROM devices WHERE mac_address = ?", (device.mac_address,)
    )
    existing_device = cursor.fetchone()

    if existing_device:
        # Обновляем существующее устройство
        device_id = existing_device[0]
        cursor.execute(
            """
            UPDATE devices 
            SET name = ?, ip_address = ?, model = ?, model_image_url = ?, microphone_info = ?, wifi_signal = ?, status = 'online', last_seen = ?
            WHERE id = ?
        """,
            (
                device.name,
                device.ip_address,
                device.model,
                device.model_image_url,
                device.microphone_info,
                device.wifi_signal,
                datetime.now().isoformat(),
                device_id,
            ),
        )
        print(f"🔄 Устройство обновлено: {device.name}")
    else:
        # Создаем новое устройство
        device_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO devices (id, name, ip_address, mac_address, model, model_image_url, microphone_info, wifi_signal, status, last_seen)
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
        print(f"✅ Новое устройство зарегистрировано: {device.name}")

    conn.commit()
    conn.close()

    # Рассылка обновления
    await broadcast_to_websockets(
        {
            "type": "device_registered",
            "device_id": device_id,
            "name": device.name,
            "status": "online",
        }
    )

    return {"device_id": device_id, "status": "registered"}


@app.post("/detect_sound")
async def detect_sound_endpoint(audio: AudioData):
    """Детекция звука с поддержкой custom sounds через YAMNet embeddings"""
    if model is None:
        raise HTTPException(status_code=503, detail="Модель не загружена")

    print(f"🎵 Получен аудио запрос от устройства: {audio.device_id}")

    # 1. Извлекаем YAMNet embeddings из аудио
    embedding = extract_embeddings(audio.audio_data)

    if not embedding:
        raise HTTPException(status_code=400, detail="Не удалось извлечь embeddings")

    print(f"📊 Embeddings извлечены: {len(embedding)} элементов")

    detection_id = str(uuid.uuid4())

    # 2. Проверяем custom sounds через embeddings
    print(f"🔍 Ищем custom matches для устройства: {audio.device_id}")
    custom_match = find_best_custom_match(embedding, audio.device_id)

    print(f"🎯 Custom match результат: {custom_match}")

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

    # 3. Если найден custom sound с высокой схожестью
    if custom_match and custom_match.get("similarity", 0) > custom_match.get(
        "threshold", 0.75
    ):
        sound_type = custom_match["sound_type"]  # 'specific' или 'excluded'

        final_result.update(
            {
                "is_custom": True,
                "custom_sound_type": sound_type,
                "sound_type": custom_match["name"],  # Имя custom sound
                "confidence": custom_match["similarity"],
                "should_notify": sound_type
                == "specific",  # Уведомления только для specific
            }
        )

        print(
            f"🎯 Custom sound detected: {custom_match['name']} - {custom_match['similarity']*100:.2f}% ({sound_type})"
        )

    # 4. Если custom sound не найден - используем YAMNet
    else:
        detection_result = detect_sound(audio.audio_data)

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

            print(
                f"🔊 YAMNet Detection: {top_prediction['sound_type']} - {top_prediction['confidence']*100:.2f}% - should_notify: {final_result['should_notify']}"
            )
        else:
            raise HTTPException(status_code=400, detail="Не удалось детектировать звук")

    # 5. Сохраняем в БД
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sound_detections (id, device_id, sound_type, confidence, timestamp, embeddings)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
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

    # 6. Рассылка в реальном времени
    await broadcast_to_websockets(
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
            "db_level": audio.db_level,
        }
    )

    return {
        "detection_id": detection_id,
        "sound_type": final_result["sound_type"],
        "confidence": final_result["confidence"],
        "is_custom": final_result["is_custom"],
        "custom_sound_type": final_result["custom_sound_type"],
        "should_notify": final_result["should_notify"],
        "all_predictions": (
            detection_result.get("predictions", [])
            if not final_result["is_custom"]
            else []
        ),
    }


@app.delete("/devices/{device_id}/detections")
async def clear_device_detections(device_id: str):
    """Удаление всех детекций для указанного устройства"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Device not found")

        cursor.execute("DELETE FROM sound_detections WHERE device_id = ?", (device_id,))
        conn.commit()

        await broadcast_to_websockets(
            {
                "type": "detections_cleared",
                "device_id": device_id,
            }
        )

        return {
            "status": "success",
            "message": f"All detections for device {device_id} have been cleared.",
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal server error while clearing detections."
        )
    finally:
        conn.close()


@app.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    """Удаление устройства"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Удаляем связанные детекции
    cursor.execute("DELETE FROM sound_detections WHERE device_id = ?", (device_id,))

    # Удаляем связанные пользовательские звуки
    cursor.execute("DELETE FROM custom_sounds WHERE device_id = ?", (device_id,))

    # Удаляем устройство
    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))

    conn.commit()
    conn.close()

    # Рассылка обновления
    await broadcast_to_websockets(
        {
            "type": "device_deleted",
            "device_id": device_id,
        }
    )

    return {"status": "deleted"}


@app.put("/update_device/{device_id}")
async def update_device(device_id: str, device_update: dict):
    """Обновление информации об устройстве (WiFi, микрофон и т.д.)"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем существует ли устройство
        cursor.execute("SELECT COUNT(*) FROM devices WHERE id = ?", (device_id,))
        device_exists = cursor.fetchone()[0] > 0

        if not device_exists:
            # Создаем устройство если его нет
            cursor.execute(
                """
                INSERT INTO devices (id, name, ip_address, mac_address, model, wifi_signal, microphone_info, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    device_update.get("name", f"Device {device_id[:8]}"),
                    device_update.get("ip_address", "Unknown"),
                    device_update.get("mac_address", "Unknown"),
                    device_update.get("model", "Unknown"),
                    device_update.get("wifi_signal", 0),
                    device_update.get("microphone_info", "Unknown"),
                    device_update.get("last_seen", datetime.now().isoformat()),
                ),
            )
            print(f"✅ Устройство создано: {device_id}")
        else:
            # Обновляем существующее устройство
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
            print(f"🔄 Устройство обновлено: {device_id}")

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


@app.get("/yamnet_sounds")
async def get_yamnet_sounds():
    """Получение полного списка звуков YAMNet"""
    # Полный список классов YAMNet (521 звук)
    yamnet_classes = [
        "Silence",
        "Alarm",
        "Bark",
        "Baby cry",
        "Babbling",
        "Bang",
        "Bass drum",
        "Bear",
        "Bee",
        "Bicycle bell",
        "Bird",
        "Bleat",
        "Boat",
        "Boing",
        "Bong",
        "Buzzer",
        "Car",
        "Cat",
        "Chatter",
        "Chicken",
        "Chirp",
        "Clang",
        "Clap",
        "Clock",
        "Cough",
        "Cow",
        "Crack",
        "Crackle",
        "Crash",
        "Creak",
        "Crow",
        "Crowd",
        "Crying",
        "Cuckoo",
        "Dog",
        "Door",
        "Doorbell",
        "Drip",
        "Drum",
        "Eagle",
        "Eating",
        "Electric shaver",
        "Engine",
        "Explosion",
        "Fart",
        "Female speech",
        "Fire",
        "Fire alarm",
        "Firecracker",
        "Fire engine",
        "Flap",
        "Flush",
        "Fly",
        "Footsteps",
        "Frog",
        "Gasp",
        "Glass",
        "Goat",
        "Goose",
        "Grasshopper",
        "Growl",
        "Gunshot",
        "Hammer",
        "Hand saw",
        "Helicopter",
        "Hen",
        "Hiccup",
        "Hiss",
        "Hog",
        "Horse",
        "Human voice",
        "Hyena",
        "Insect",
        "Jackhammer",
        "Jet engine",
        "Keyboard",
        "Knock",
        "Laugh",
        "Lawn mower",
        "Lion",
        "Machine gun",
        "Male speech",
        "Meow",
        "Microwave",
        "Motorcycle",
        "Mouse",
        "Music",
        "Navy sonar",
        "Oink",
        "Owl",
        "Parrot",
        "Pig",
        "Pigeon",
        "Power tool",
        "Purr",
        "Rain",
        "Raindrop",
        "Raven",
        "Rattle",
        "Ring",
        "Roar",
        "Roll",
        "Rooster",
        "Saw",
        "Scissors",
        "Scream",
        "Sewing machine",
        "Shatter",
        "Sheep",
        "Siren",
        "Skateboard",
        "Ski",
        "Slam",
        "Slide whistle",
        "Snare drum",
        "Snake",
        "Sneeze",
        "Snowmobile",
        "Spray",
        "Squeak",
        "Squelch",
        "Steam",
        "Stream",
        "Strum",
        "Swim",
        "Tap",
        "Thunder",
        "Tick",
        "Tinkle",
        "Toilet flush",
        "Train",
        "Trumpet",
        "Typewriter",
        "Vacuum",
        "Vibration",
        "Water",
        "Waterfall",
        "Whack",
        "Whimper",
        "Whisper",
        "Whistle",
        "Wind",
        "Wobble",
        "Yawn",
        "Yell",
        "Zipper",
        "Animal",
        "Bird vocalization",
        "Bus",
        "Can",
        "Change ringing",
        "Chime",
        "Computer keyboard",
        "Cup",
        "Dishes",
        "Drawer",
        "Eating apple",
        "Frying",
        "Gong",
        "Gurgling",
        "Hair dryer",
        "Knocking",
        "Maraca",
        "Printer",
        "Rustle",
        "Scrubbing",
        "Shaker",
        "Shuffling",
        "Sink",
        "Splash",
        "Sprinkler",
        "Stir",
        "Tap water",
        "Tearing",
        "Typing",
        "Writing",
        "Applause",
        "Babbling brook",
        "Bicycle",
        "Boat/Ship",
        "Brushing teeth",
        "Camera",
        "Chewing",
        "Chopping",
        "Church bell",
        "Clipping",
        "Cricket",
        "Cutting",
        "Dishes, pots, and pans",
        "Door closing",
        "Drawer opening/closing",
        "Electric toothbrush",
        "Filling",
        "Food processor",
        "Garbage disposal",
        "Hair dryer",
        "Hammering",
        "Idling",
        "Knocking on door",
        "Lawn mower",
        "Microwave oven",
        "Motorcycle",
        "Power tool",
        "Refrigerator",
        "Scissors",
        "Shaver",
        "Sink (filling or washing)",
        "Toilet flushing",
        "Vacuum cleaner",
        "Washing machine",
        "Water tap",
        "Wind chime",
        "Wind noise (microphone)",
        "Alarm clock",
        "Analog watch",
        "Analog watch ticking",
        "Bicycle bell",
        "Buzzer",
        "Cellular telephone",
        "Chime",
        "Church bell",
        "Clock",
        "Digital clock",
        "Doorbell",
        "Fire alarm",
        "Microwave oven",
        "Music box",
        "Pager",
        "Refrigerator",
        "Telephone bell ringing",
        "Timer",
        "Watch ticking",
        "Acoustic guitar",
        "Banjo",
        "Bass guitar",
        "Cello",
        "Clarinet",
        "Cymbal",
        "Double bass",
        "Drum",
        "Drum kit",
        "Electric piano",
        "Flute",
        "French horn",
        "Glockenspiel",
        "Gong",
        "Guitar",
        "Harmonica",
        "Harp",
        "Harpsichord",
        "Hi-hat",
        "Keyboard (musical)",
        "Marimba",
        "Music",
        "Oboe",
        "Organ",
        "Piano",
        "Saxophone",
        "Steelpan",
        "Synthesizer",
        "Tambourine",
        "Trombone",
        "Trumpet",
        "Tuba",
        "Violin",
        "Violoncello",
        "Xylophone",
        "Accordion",
        "Bagpipe",
        "Band",
        "Barbershop quartet",
        "Bassoon",
        "Blues",
        "Calliope",
        "Carnatic music",
        "Choir",
        "Country music",
        "Dixieland",
        "Folk music",
        "Gospel",
        "Jazz",
        "Mariachi",
        "Military band",
        "Music for children",
        "Opera",
        "Pop music",
        "Rap",
        "Reggae",
        "Rock and roll",
        "Salsa",
        "Soul music",
        "Swing music",
        "World music",
        "Adult speech",
        "Babble",
        "Child speech",
        "Conversation",
        "Crying, sobbing",
        "Female speech, singing",
        "Giggle",
        "Grunting",
        "Humming",
        "Laughter",
        "Male speech, singing",
        "Narration, monodrama",
        "Panting",
        "Reading",
        "Shout",
        "Singing",
        "Speech",
        "Speech synthesizer",
        "Whispering",
        "Yodeling",
        "Applause",
        "Babble",
        "Bark",
        "Bleat",
        "Breathe",
        "Buzz",
        "Chatter",
        "Chirp",
        "Chuckle",
        "Cluck",
        "Coo",
        "Cough",
        "Croak",
        "Crow",
        "Cry",
        "Cuckoo",
        "Ding",
        "Drip",
        "Fart",
        "Gasp",
        "Gibber",
        "Grunt",
        "Growl",
        "Groan",
        "Hiccup",
        "Hiss",
        "Huff",
        "Hum",
        "Meow",
        "Moo",
        "Neigh",
        "Oink",
        "Pant",
        "Peep",
        "Purr",
        "Quack",
        "Ribbit",
        "Roar",
        "Rumble",
        "Scream",
        "Shriek",
        "Sigh",
        "Sizzle",
        "Snarl",
        "Sniff",
        "Snore",
        "Snort",
        "Splash",
        "Squawk",
        "Squeal",
        "Squeak",
        "Thump",
        "Thwack",
        "Tsk",
        "Wail",
        "Warble",
        "Whimper",
        "Whine",
        "Whisper",
        "Whistle",
        "Whoop",
        "Wow",
        "Yawn",
        "Yelp",
        "Yip",
        "Yodel",
        "Zing",
        "Zip",
        "Zoom",
        "Air conditioning",
        "Air horn",
        "Airplane",
        "Ambulance",
        "Bicycle",
        "Bus",
        "Car",
        "Fire engine",
        "Helicopter",
        "Jet engine",
        "Motorcycle",
        "Police car (siren)",
        "Railroad car",
        "Siren",
        "Skateboard",
        "Ski",
        "Snowmobile",
        "Subway",
        "Train",
        "Train horn",
        "Truck",
        "Van",
        "Water vehicle",
        "Boat",
        "Ferry",
        "Ship",
        "Steamboat",
        "Tugboat",
        "Yacht",
        "Aircraft",
        "Airplane",
        "Helicopter",
        "Jet engine",
        "Propeller",
        "Rocket",
        "Spacecraft",
        "Bicycle",
        "Bus",
        "Car",
        "Fire engine",
        "Motorcycle",
        "Police car",
        "Siren",
        "Taxi",
        "Train",
        "Truck",
        "Van",
        "Ambulance",
        "Fire engine",
        "Police car",
        "Siren",
        "Alarm",
        "Bell",
        "Buzzer",
        "Chime",
        "Doorbell",
        "Fire alarm",
        "Smoke detector",
        "Telephone bell",
        "Timer",
        "Watch",
        "Water",
        "Waterfall",
        "Ocean",
        "Rain",
        "River",
        "Stream",
        "Splash",
        "Drip",
        "Faucet",
        "Shower",
        "Toilet",
        "Washing machine",
        "Dishwasher",
        "Vacuum cleaner",
        "Hair dryer",
        "Fan",
        "Air conditioning",
        "Heater",
        "Refrigerator",
        "Freezer",
        "Microwave",
        "Oven",
        "Stove",
        "Toaster",
        "Blender",
        "Mixer",
        "Coffee maker",
        "Electric shaver",
        "Toothbrush",
        "Hair clipper",
        "Nail file",
        "Scissors",
        "Razor",
        "Tweezers",
        "Comb",
        "Brush",
        "Makeup",
        "Perfume",
        "Soap",
        "Shampoo",
        "Toothpaste",
        "Deodorant",
        "Lotion",
        "Cream",
        "Powder",
        "Lipstick",
        "Mascara",
        "Eyeliner",
        "Eyeshadow",
        "Foundation",
        "Concealer",
        "Blush",
        "Bronzer",
        "Highlighter",
        "Contour",
        "Primer",
        "Setting spray",
        "Makeup remover",
        "Cleanser",
        "Toner",
        "Moisturizer",
        "Sunscreen",
        "Serum",
        "Essence",
        "Ampoule",
        "Mask",
        "Patch",
        "Peel",
        "Exfoliator",
        "Scrub",
        "Gel",
        "Mousse",
        "Foam",
        "Oil",
        "Balm",
        "Wax",
        "Butter",
        "Margarine",
        "Cheese",
        "Yogurt",
        "Milk",
        "Cream",
        "Sour cream",
        "Buttermilk",
        "Kefir",
        "Cottage cheese",
        "Ricotta",
        "Mozzarella",
        "Cheddar",
        "Swiss",
        "Parmesan",
        "Gouda",
        "Brie",
        "Camembert",
        "Feta",
        "Goat cheese",
        "Blue cheese",
        "Roquefort",
        "Gorgonzola",
        "Stilton",
        "Limburger",
        "Munster",
        "Provolone",
        "Edam",
        "Maasdam",
        "Emmental",
        "Gruyère",
        "Comté",
        "Beaufort",
        "Abondance",
        "Reblochon",
        "Tome",
        "Cantal",
        "Laguiole",
        "Salers",
        "Fourme",
        "Ambert",
        "Bleu",
        "Des Causses",
        "Roquefort",
        "Papillon",
        "Valençay",
        "Pouligny",
        "Sainte",
        "Maure",
        "Crottin",
        "Chavignol",
        "Selles",
        "Sur",
        "Cher",
        "Chaource",
        "Langres",
        "Epoisses",
        "Maroilles",
        "Munster",
        "Géromé",
        "Vacherin",
        "Mont",
        "D'or",
        "Comté",
        "Beaufort",
        "Abondance",
        "Reblochon",
        "Tome",
        "Des Bauges",
        "Savoie",
        "Emmental",
        "Gruyère",
        "Comté",
        "Beaufort",
        "Abondance",
        "Reblochon",
        "Tome",
        "Des Bauges",
        "Savoie",
    ]

    # Удаляем дубликаты и сортируем
    unique_sounds = sorted(list(set(yamnet_classes)))

    return {"sounds": unique_sounds, "total": len(unique_sounds)}


@app.get("/devices")
async def get_devices():
    """Получение списка устройств"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, ip_address, mac_address, model, model_image_url, microphone_info, wifi_signal, status, last_seen, created_at
        FROM devices
        ORDER BY last_seen DESC
    """
    )

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
            }
        )

    conn.close()
    return devices


@app.get("/detections/{device_id}")
async def get_detections(device_id: str, limit: int = 1000):
    """Получение детекций для устройства"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Сначала получаем общее количество
    cursor.execute(
        "SELECT COUNT(*) FROM sound_detections WHERE device_id = ?", (device_id,)
    )
    total_count = cursor.fetchone()[0]

    # Затем получаем детекции с лимитом
    cursor.execute(
        """
        SELECT id, sound_type, confidence, timestamp, embeddings
        FROM sound_detections
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (device_id, limit),
    )

    detections = []
    for row in cursor.fetchall():
        detections.append(
            {
                "id": row[0],
                "sound_type": row[1],
                "confidence": row[2],
                "timestamp": row[3],
                "embeddings": json.loads(row[4]) if row[4] else [],
            }
        )

    conn.close()
    return {"detections": detections, "total_count": total_count}


@app.post("/custom_sounds/train")
async def train_custom_sound(sound_data: dict):
    """Тренировка custom sound из нескольких аудио записей"""
    try:
        name = sound_data["name"]
        sound_type = sound_data["sound_type"]  # "specific" или "excluded"
        device_id = sound_data["device_id"]
        audio_recordings = sound_data["audio_recordings"]  # List[List[float]]
        threshold = sound_data.get("threshold", 0.75)

        if not audio_recordings:
            raise HTTPException(status_code=400, detail="No audio recordings provided")

        # Извлекаем embeddings из каждой записи
        all_embeddings = []
        for audio_data in audio_recordings:
            embedding = extract_embeddings(audio_data)
            if embedding:
                all_embeddings.append(embedding)

        if not all_embeddings:
            raise HTTPException(
                status_code=400, detail="Failed to extract embeddings from audio"
            )

        # Вычисляем centroid
        centroid = np.mean(all_embeddings, axis=0).tolist()

        # Сохраняем в БД
        sound_id = str(uuid.uuid4())
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO custom_sounds (id, name, sound_type, embeddings, centroid, threshold, device_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sound_id,
                name,
                sound_type,
                json.dumps(all_embeddings),
                json.dumps(centroid),
                threshold,
                device_id,
            ),
        )

        conn.commit()
        conn.close()

        print(
            f"🎯 Custom sound trained: {name} ({sound_type}) - {len(all_embeddings)} samples - threshold: {threshold}"
        )

        return {
            "sound_id": sound_id,
            "name": name,
            "sound_type": sound_type,
            "samples_count": len(all_embeddings),
            "threshold": threshold,
            "centroid": centroid,
            "status": "trained",
        }

    except Exception as e:
        print(f"❌ Error training custom sound: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/custom_sounds")
async def add_custom_sound(sound: CustomSound):
    """Добавление пользовательского звука с YAMNet embeddings"""
    sound_id = str(uuid.uuid4())

    # Вычисляем centroid из embeddings
    centroid = np.mean(sound.embeddings, axis=0).tolist()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO custom_sounds (id, name, sound_type, embeddings, centroid, threshold, device_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            sound_id,
            sound.name,
            sound.sound_type,
            json.dumps(sound.embeddings),
            json.dumps(centroid),
            sound.threshold,
            sound.device_id,
        ),
    )

    conn.commit()
    conn.close()

    print(
        f"✅ Custom sound added: {sound.name} ({sound.sound_type}) - threshold: {sound.threshold}"
    )

    return {"sound_id": sound_id, "status": "added", "centroid": centroid}


@app.get("/custom_sounds")
async def get_custom_sounds():
    """Получение пользовательских звуков"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, sound_type, embeddings, centroid, threshold, device_id, created_at
        FROM custom_sounds
        ORDER BY created_at DESC
    """
    )

    sounds = []
    for row in cursor.fetchall():
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

    conn.close()
    return sounds


@app.delete("/custom_sounds/{sound_id}")
async def delete_custom_sound(sound_id: str):
    """Удаление пользовательского звука"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM custom_sounds WHERE id = ?", (sound_id,))

    conn.commit()
    conn.close()

    return {"status": "deleted"}


# API для настроек уведомлений
@app.post("/notification_sounds")
async def add_notification_sound(sound: NotificationSound):
    """Добавление важного звука для уведомлений"""
    sound_id = str(uuid.uuid4())

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Сначала удаляем из исключенных если есть
        cursor.execute(
            "DELETE FROM excluded_sounds WHERE device_id = ? AND LOWER(sound_name) = LOWER(?)",
            (sound.device_id, sound.sound_name),
        )

        # Затем добавляем в важные
        cursor.execute(
            """
            INSERT OR REPLACE INTO notification_sounds (id, sound_name, device_id)
            VALUES (?, ?, ?)
        """,
            (sound_id, sound.sound_name, sound.device_id),
        )
        conn.commit()
        return {"sound_id": sound_id, "status": "added"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/notification_sounds/{device_id}")
async def get_notification_sounds(device_id: str):
    """Получение важных звуков для устройства"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, sound_name, device_id, created_at
        FROM notification_sounds
        WHERE device_id = ?
        ORDER BY created_at DESC
    """,
        (device_id,),
    )

    sounds = []
    for row in cursor.fetchall():
        sounds.append(
            {
                "id": row[0],
                "sound_name": row[1],
                "device_id": row[2],
                "created_at": row[3],
            }
        )

    conn.close()
    return sounds


@app.delete("/notification_sounds/{sound_id}")
async def delete_notification_sound(sound_id: str):
    """Удаление важного звука"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notification_sounds WHERE id = ?", (sound_id,))

    conn.commit()
    conn.close()

    return {"status": "deleted"}


@app.post("/excluded_sounds")
async def add_excluded_sound(sound: ExcludedSound):
    """Добавление исключенного звука"""
    sound_id = str(uuid.uuid4())

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Сначала удаляем из важных если есть
        cursor.execute(
            "DELETE FROM notification_sounds WHERE device_id = ? AND LOWER(sound_name) = LOWER(?)",
            (sound.device_id, sound.sound_name),
        )

        # Затем добавляем в исключенные
        cursor.execute(
            """
            INSERT OR REPLACE INTO excluded_sounds (id, sound_name, device_id)
            VALUES (?, ?, ?)
        """,
            (sound_id, sound.sound_name, sound.device_id),
        )
        conn.commit()
        return {"sound_id": sound_id, "status": "added"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/excluded_sounds/{device_id}")
async def get_excluded_sounds(device_id: str):
    """Получение исключенных звуков для устройства"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, sound_name, device_id, created_at
        FROM excluded_sounds
        WHERE device_id = ?
        ORDER BY created_at DESC
    """,
        (device_id,),
    )

    sounds = []
    for row in cursor.fetchall():
        sounds.append(
            {
                "id": row[0],
                "sound_name": row[1],
                "device_id": row[2],
                "created_at": row[3],
            }
        )

    conn.close()
    return sounds


@app.delete("/excluded_sounds/{sound_id}")
async def delete_excluded_sound(sound_id: str):
    """Удаление исключенного звука"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM excluded_sounds WHERE id = ?", (sound_id,))

    conn.commit()
    conn.close()

    return {"status": "deleted"}


@app.get("/notification_settings/{device_id}")
async def get_notification_settings(device_id: str):
    """Получение всех настроек уведомлений для устройства"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем важные звуки
    cursor.execute(
        """
        SELECT sound_name FROM notification_sounds WHERE device_id = ?
    """,
        (device_id,),
    )
    notification_sounds = [row[0] for row in cursor.fetchall()]

    # Получаем исключенные звуки
    cursor.execute(
        """
        SELECT sound_name FROM excluded_sounds WHERE device_id = ?
    """,
        (device_id,),
    )
    excluded_sounds = [row[0] for row in cursor.fetchall()]

    # Получаем пользовательские звуки
    cursor.execute(
        """
        SELECT name, sound_type FROM custom_sounds WHERE device_id = ?
    """,
        (device_id,),
    )
    custom_sounds = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]

    conn.close()

    return {
        "notification_sounds": notification_sounds,
        "excluded_sounds": excluded_sounds,
        "custom_sounds": custom_sounds,
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "devices_connected": len(websocket_connections),
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    print("🚀 Запуск Sound Sentinel API сервера...")
    print("📡 Сервер будет доступен на https://localhost:8000")
    print("🔗 WebSocket: wss://localhost:8000/ws")

    # Запуск сервера с SSL
    # Пути к сертификатам теперь абсолютные
    script_dir = os.path.dirname(__file__)
    cert_path = os.path.join(script_dir, "certs", "cert.pem")
    key_path = os.path.join(script_dir, "certs", "key.pem")

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        print(
            f"❌ Ошибка: SSL сертификаты не найдены по путям {cert_path} и {key_path}"
        )
        print(
            "Пожалуйста, убедитесь, что файлы cert.pem и key.pem находятся в папке 'certs' рядом с main.py"
        )
    else:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            ssl_keyfile=key_path,
            ssl_certfile=cert_path,
        )
