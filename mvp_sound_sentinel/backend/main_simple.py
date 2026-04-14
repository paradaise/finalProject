#!/usr/bin/env python3
"""
Sound Sentinel MVP - API Server (Simple Version)
Простой сервер с захардкоденным SSL
"""

import os
import sys
import json
import uuid
import sqlite3
import asyncio
import warnings
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional, Dict

# Подавление TensorFlow предупреждений
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import time

# Ensure `import backend.*` works even when uvicorn runs `main_simple:app` from `backend/`.
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

try:
    from backend.env_loader import load_env_file

    load_env_file()
except Exception:
    pass

from backend.api.simple import state as simple_state
from backend.api.simple.router import router as simple_router
from backend.utils.yamnet_cached import (
    load_yamnet_model,
    get_cache_info,
    clear_yamnet_cache,
)

# Глобальные переменные
db_path = os.getenv("DB_PATH", "soundsentinel.db")
model = None
class_names = []
websocket_connections = set()

# Keep shared state in sync with extracted route modules.
simple_state.db_path = db_path
simple_state.model = model
simple_state.class_names = class_names
simple_state.websocket_connections = websocket_connections

# Хардкодированные настройки
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
USE_SSL = os.getenv("USE_SSL", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "y",
    "on",
}
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "certs/cert.pem")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "certs/key.pem")


# Модели данных
class DeviceRegistration(BaseModel):
    model_config = {"protected_namespaces": ()}
    name: str
    ip_address: str
    mac_address: str
    model: str
    model_image_url: Optional[str] = None
    microphone_info: Optional[str] = None
    wifi_signal: int = 0


class AudioData(BaseModel):
    device_id: str
    audio_data: List[float]
    sample_rate: int = 16000
    db_level: Optional[float] = None


class SoundDetection(BaseModel):
    device_id: str
    sound_type: str
    confidence: float
    timestamp: str
    audio_data: List[float]


class AudioLevel(BaseModel):
    device_id: str
    db_level: float
    timestamp: str


class DeviceUpdate(BaseModel):
    wifi_signal: Optional[int] = None
    microphone_info: Optional[str] = None
    status: Optional[str] = None
    last_seen: Optional[str] = None


# Инициализация lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Server starting up ---")
    init_database()
    success = load_model()
    if not success:
        print("⚠️ Модель не загружена. Сервер будет работать в ограниченном режиме.")

    # Update extracted route modules with runtime state.
    simple_state.db_path = db_path
    simple_state.model = model
    simple_state.class_names = class_names
    simple_state.websocket_connections = websocket_connections

    yield

    print("--- Server shutting down ---")


# Инициализация FastAPI
app = FastAPI(title="Sound Sentinel MVP", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Логируем запрос
    print(f"📥 {request.method} {request.url.path}")

    response = await call_next(request)

    # Логируем ответ
    process_time = time.time() - start_time
    print(f"📤 {response.status_code} - {process_time:.3f}s")

    return response


# Инициализация базы данных
def init_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_sounds (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sound_type TEXT NOT NULL,
            embeddings TEXT,
            centroid TEXT,
            threshold REAL DEFAULT 0.8,
            device_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """
    )

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

    # Sync legacy/default custom thresholds with environment default.
    default_match_threshold = float(os.getenv("CUSTOM_MATCH_DEFAULT_THRESHOLD", "0.7"))
    cursor.execute(
        """
        UPDATE custom_sounds
        SET threshold = ?
        WHERE threshold IS NULL OR ABS(threshold - 0.75) < 0.000001 OR ABS(threshold - 0.6) < 0.000001
        """,
        (default_match_threshold,),
    )

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


# Загрузка модели с кэшированием
def load_model():
    global model, class_names
    try:
        print("🔄 Загрузка YAMNet модели с кэшированием...")

        # Загружаем модель с локальным кэшированием
        model, class_names = load_yamnet_model()

        if model is not None and class_names is not None:
            print(f"✅ YAMNet модель загружена. Классов: {len(class_names)}")
            return True
        else:
            print("❌ Не удалось загрузить YAMNet модель")
            return False
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return False


# Дополнительные роуты
@app.post("/update_audio_level")
async def update_audio_level(data: AudioLevel):
    """Обновление только уровня звука без детекции"""
    dead_connections = []
    for ws in list(websocket_connections):
        try:
            await ws.send_text(
                json.dumps(
                    {
                        "type": "audio_level_updated",
                        "device_id": data.device_id,
                        "db_level": data.db_level,
                        "timestamp": data.timestamp,
                    }
                )
            )
        except Exception:
            dead_connections.append(ws)

    for ws in dead_connections:
        websocket_connections.discard(ws)
    return {"status": "success"}


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


# WebSocket функции
app.include_router(simple_router)

if __name__ == "__main__":
    print("🚀 Запуск Sound Sentinel API сервера...")
    print(f"📡 Сервер будет доступен на https://{HOST}:{PORT}")
    print(f"🔗 WebSocket: wss://{HOST}:{PORT}/ws")

    # Пути к сертификатам
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = (
        SSL_CERT_PATH
        if os.path.isabs(SSL_CERT_PATH)
        else os.path.join(script_dir, SSL_CERT_PATH)
    )
    key_path = (
        SSL_KEY_PATH
        if os.path.isabs(SSL_KEY_PATH)
        else os.path.join(script_dir, SSL_KEY_PATH)
    )

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        print(f"❌ Ошибка: SSL сертификаты не найдены")
        print(f"cert_path: {cert_path}")
        print(f"key_path: {key_path}")
    else:
        uvicorn.run(
            "main_simple:app",
            host=HOST,
            port=PORT,
            reload=True,
            log_level="info",
            ssl_keyfile=key_path,
            ssl_certfile=cert_path,
        )
