from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import librosa
import time
from datetime import datetime
import sqlite3
import uuid
from contextlib import asynccontextmanager


# Модели данных
class AudioEvent(BaseModel):
    id: str
    sound_type: str
    confidence: float
    timestamp: datetime
    device_id: str
    intensity: float
    description: str


class Device(BaseModel):
    id: str
    name: str
    ip_address: str
    status: str
    last_seen: datetime
    temperature: Optional[float] = None
    cpu_load: Optional[float] = None


class CustomSound(BaseModel):
    id: str
    name: str
    sound_type: str  # 'specific' or 'excluded'
    mfcc_features: List[float]
    created_at: datetime
    device_id: str


class AudioPacket(BaseModel):
    segment_id: int
    packet_id: int
    total_packets: int
    audio: List[float]
    sample_rate: int
    timestamp: float
    device_id: str


# Глобальные переменные
class AppState:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.audio_buffers: Dict[str, Dict[int, List]] = {}
        self.sound_detector = None
        self.db_conn = None


app_state = AppState()


# Инициализация БД
def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect("sound_sentinel.db")
    cursor = conn.cursor()

    # Таблица устройств
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT,
            ip_address TEXT,
            status TEXT,
            last_seen TEXT,
            temperature REAL,
            cpu_load REAL,
            wifi_ssid TEXT
        )
    """
    )

    # Таблица аудио событий
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_events (
            id TEXT PRIMARY KEY,
            sound_type TEXT,
            confidence REAL,
            timestamp TEXT,
            device_id TEXT,
            intensity REAL,
            db_level REAL,
            description TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """
    )

    # Таблица пользовательских звуков
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_sounds (
            id TEXT PRIMARY KEY,
            name TEXT,
            sound_type TEXT,
            mfcc_features TEXT,
            created_at TEXT,
            device_id TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """
    )

    conn.commit()
    return conn


# Улучшенный детектор звуков
class AdvancedSoundDetector:
    def __init__(self):
        print("Загрузка улучшенной модели детекции звуков...")
        try:
            # Используем PANNs модель для лучшей детекции бытовых звуков
            self.model = hub.load("https://tfhub.dev/google/yamnet/1")
            self.class_map_path = self.model.class_map_path().numpy().decode("utf-8")
            self.class_names = self._load_class_names()

            # Словарь релевантных бытовых звуков
            self.relevant_sounds = {
                "Doorbell",
                "Door knock",
                "Alarm",
                "Fire alarm",
                "Smoke alarm",
                "Baby cry",
                "Infant cry",
                "Dog bark",
                "Cat meow",
                "Glass breaking",
                "Window breaking",
                "Car horn",
                "Siren",
                "Emergency vehicle",
                "Telephone bell ringing",
                "Mobile phone ringing",
                "Knock",
                "Water tap",
                "Water running",
                "Shower",
                "Toilet flush",
                "Microwave oven",
                "Dishwasher",
                "Washing machine",
                "Vacuum cleaner",
            }

            # Пользовательские звуки
            self.custom_sounds = []
            self.excluded_sounds = []

            print(f"Модель загружена. Релевантных классов: {len(self.relevant_sounds)}")

        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            raise

    def _load_class_names(self):
        class_names = {}
        try:
            with open(self.class_map_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    try:
                        class_id = int(parts[0])
                        class_name = parts[2].strip('" ')
                        class_names[class_id] = class_name
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            print(f"Ошибка загрузки классов: {e}")
            for i in range(521):
                class_names[i] = f"Class_{i}"

        return class_names

    def extract_mfcc(self, audio_data, sample_rate=16000):
        """Извлечение MFCC признаков для сравнения"""
        try:
            mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            mfcc_mean = np.mean(mfcc, axis=1)
            return mfcc_mean.tolist()
        except Exception as e:
            print(f"Ошибка извлечения MFCC: {e}")
            return None

    def compare_with_custom_sounds(self, audio_data, sample_rate=16000):
        """Сравнение с пользовательскими звуками через MFCC"""
        if not self.custom_sounds:
            return []

        current_mfcc = self.extract_mfcc(audio_data, sample_rate)
        if not current_mfcc:
            return []

        matches = []
        for custom_sound in self.custom_sounds:
            # Косинусное сходство между MFCC векторами
            similarity = self.cosine_similarity(
                current_mfcc, custom_sound["mfcc_features"]
            )
            if similarity > 0.7:  # Порог схожести
                matches.append(
                    {
                        "sound": custom_sound["name"],
                        "confidence": similarity,
                        "type": "custom",
                    }
                )

        return matches

    def cosine_similarity(self, vec1, vec2):
        """Вычисление косинусного сходства"""
        vec1, vec2 = np.array(vec1), np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1, norm2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0

    def detect_sounds(self, audio_data, sample_rate=16000):
        try:
            if len(audio_data) < sample_rate * 0.5:
                return []

            # Детекция основной моделью
            scores, embeddings, spectrogram = self.model(audio_data)
            scores = scores.numpy()
            mean_scores = np.mean(scores, axis=0)

            # Проверка на пользовательские звуки
            custom_matches = self.compare_with_custom_sounds(audio_data, sample_rate)
            if custom_matches:
                return custom_matches

            # Фильтрация релевантных звуков
            results = []
            for class_id, confidence in enumerate(mean_scores):
                if confidence > 0.1 and class_id in self.class_names:
                    sound_name = self.class_names[class_id]

                    # Проверяем, является ли звук релевантным и не исключенным
                    if self._is_relevant_sound(sound_name):
                        results.append(
                            {
                                "sound": sound_name,
                                "confidence": float(confidence),
                                "type": "detected",
                            }
                        )

            # Сортировка по уверенности
            results.sort(key=lambda x: x["confidence"], reverse=True)
            return results[:3]  # Топ-3

        except Exception as e:
            print(f"Ошибка детекции: {e}")
            return []

    def _is_relevant_sound(self, sound_name):
        """Проверка релевантности звука"""
        # Исключенные звуки
        for excluded in self.excluded_sounds:
            if excluded["name"].lower() in sound_name.lower():
                return False

        # Релевантные звуки
        for relevant in self.relevant_sounds:
            if relevant.lower() in sound_name.lower():
                return True

        return False

    def add_custom_sound(self, name: str, mfcc_features: list, sound_type: str):
        """Добавление пользовательского звука"""
        sound_data = {"name": name, "mfcc_features": mfcc_features, "type": sound_type}

        if sound_type == "specific":
            self.custom_sounds.append(sound_data)
        elif sound_type == "excluded":
            self.excluded_sounds.append(sound_data)


# Управление жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск
    app_state.db_conn = init_database()
    app_state.sound_detector = AdvancedSoundDetector()
    print("API сервер запущен")
    yield
    # Очистка
    if app_state.db_conn:
        app_state.db_conn.close()


app = FastAPI(title="Sound Sentinel API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket для реального времени
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_state.active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Эхо для тестирования
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        app_state.active_connections.remove(websocket)


# API эндпоинты
@app.get("/")
async def root():
    return {"message": "Sound Sentinel API", "version": "1.0.0"}


@app.post("/audio_packet")
async def process_audio_packet(packet: AudioPacket):
    """Обработка аудио пакета от Raspberry Pi"""
    try:
        device_id = packet.device_id
        segment_id = packet.segment_id

        # Инициализация буфера для устройства
        if device_id not in app_state.audio_buffers:
            app_state.audio_buffers[device_id] = {}

        if segment_id not in app_state.audio_buffers[device_id]:
            app_state.audio_buffers[device_id][segment_id] = {}

        # Сохранение пакета
        app_state.audio_buffers[device_id][segment_id][packet.packet_id] = packet.audio

        # Проверка полноты сегмента
        if len(app_state.audio_buffers[device_id][segment_id]) == packet.total_packets:
            # Сборка полного аудио
            sorted_packets = sorted(
                app_state.audio_buffers[device_id][segment_id].items()
            )
            full_audio = np.concatenate([audio for _, audio in sorted_packets])

            # Детекция звуков
            detections = app_state.sound_detector.detect_sounds(
                full_audio, packet.sample_rate
            )

            # Сохранение событий
            for detection in detections:
                event = AudioEvent(
                    id=str(uuid.uuid4()),
                    sound_type=detection["sound"],
                    confidence=detection["confidence"],
                    timestamp=datetime.now(),
                    device_id=device_id,
                    intensity=float(np.mean(np.abs(full_audio))),
                    description=f"Detected {detection['sound']} with confidence {detection['confidence']:.2f}",
                )

                # Сохранение в БД
                cursor = app_state.db_conn.cursor()

                # Вычисление уровня в дБ
                db_level = 20 * np.log10(np.max(np.abs(full_audio)) + 1e-10)

                cursor.execute(
                    """
                    INSERT INTO audio_events (id, sound_type, confidence, timestamp, device_id, intensity, db_level, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.id,
                        event.sound_type,
                        event.confidence,
                        event.timestamp,
                        event.device_id,
                        event.intensity,
                        db_level,
                        event.description,
                    ),
                )
                app_state.db_conn.commit()

                # Отправка в WebSocket с реальными данными
                websocket_data = {
                    **event.dict(),
                    "db_level": db_level,
                    "audio_waveform": full_audio[
                        :100
                    ].tolist(),  # Первые 100 сэмплов для визуализации
                    "device_stats": {
                        "temperature": device.get("temperature"),
                        "cpu_load": device.get("cpu_load"),
                        "wifi_ssid": device.get("wifi_ssid"),
                    },
                }
                await broadcast_audio_event(websocket_data)

            # Очистка буфера
            del app_state.audio_buffers[device_id][segment_id]

            return {"status": "processed", "detections": detections}

        return {
            "status": "buffering",
            "packets_received": len(app_state.audio_buffers[device_id][segment_id]),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def broadcast_audio_event(event_data):
    """Рассылка событий всем подключенным клиентам"""
    for connection in app_state.active_connections:
        try:
            await connection.send_text(json.dumps(event_data))
        except:
            # Удаление неактивных соединений
            app_state.active_connections.remove(connection)


@app.get("/devices", response_model=List[Device])
async def get_devices():
    """Получение списка устройств"""
    cursor = app_state.db_conn.cursor()
    cursor.execute("SELECT * FROM devices")
    rows = cursor.fetchall()

    devices = []
    for row in rows:
        devices.append(
            Device(
                id=row[0],
                name=row[1],
                ip_address=row[2],
                status=row[3],
                last_seen=datetime.fromisoformat(row[4]),
                temperature=row[5],
                cpu_load=row[6],
            )
        )

    return devices


@app.get("/events/{device_id}", response_model=List[AudioEvent])
async def get_device_events(device_id: str, limit: int = 50):
    """Получение событий для устройства"""
    cursor = app_state.db_conn.cursor()
    cursor.execute(
        """
        SELECT * FROM audio_events 
        WHERE device_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """,
        (device_id, limit),
    )
    rows = cursor.fetchall()

    events = []
    for row in rows:
        events.append(
            AudioEvent(
                id=row[0],
                sound_type=row[1],
                confidence=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                device_id=row[4],
                intensity=row[5],
                description=row[6],
            )
        )

    return events


@app.post("/custom_sounds")
async def add_custom_sound(
    name: str, sound_type: str, mfcc_features: List[float], device_id: str
):
    """Добавление пользовательского звука"""
    try:
        sound_id = str(uuid.uuid4())

        # Сохранение в БД
        cursor = app_state.db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO custom_sounds (id, name, sound_type, mfcc_features, created_at, device_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                sound_id,
                name,
                sound_type,
                json.dumps(mfcc_features),
                datetime.now(),
                device_id,
            ),
        )
        app_state.db_conn.commit()

        # Добавление в детектор
        app_state.sound_detector.add_custom_sound(name, mfcc_features, sound_type)

        return {"status": "success", "sound_id": sound_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/devices")
async def register_device(device: dict):
    """Регистрация нового устройства"""
    try:
        device_id = device.get("id", str(uuid.uuid4()))
        cursor = app_state.db_conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO devices (id, name, ip_address, status, last_seen, temperature, cpu_load, wifi_ssid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                device_id,
                device.get("name"),
                device.get("ip_address"),
                device.get("status", "online"),
                datetime.now(),
                device.get("temperature"),
                device.get("cpu_load"),
                device.get("wifi_ssid"),
            ),
        )
        app_state.db_conn.commit()
        return {"id": device_id, "status": "registered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/custom_sounds")
async def get_custom_sounds(device_id: Optional[str] = None):
    """Получение пользовательских звуков"""
    try:
        cursor = app_state.db_conn.cursor()
        if device_id:
            cursor.execute(
                "SELECT * FROM custom_sounds WHERE device_id = ?", (device_id,)
            )
        else:
            cursor.execute("SELECT * FROM custom_sounds")
        rows = cursor.fetchall()

        sounds = []
        for row in rows:
            sounds.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "sound_type": row[2],
                    "mfcc_features": json.loads(row[3]),
                    "created_at": row[4],
                    "device_id": row[5],
                }
            )
        return sounds
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    """Удаление устройства"""
    try:
        cursor = app_state.db_conn.cursor()
        cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        cursor.execute("DELETE FROM audio_events WHERE device_id = ?", (device_id,))
        app_state.db_conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/custom_sounds/{sound_id}")
async def delete_custom_sound(sound_id: str):
    """Удаление пользовательского звука"""
    try:
        cursor = app_state.db_conn.cursor()
        cursor.execute("DELETE FROM custom_sounds WHERE id = ?", (sound_id,))
        app_state.db_conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
