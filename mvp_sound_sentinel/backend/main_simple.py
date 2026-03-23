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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

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
USE_SSL = os.getenv("USE_SSL", "true").strip().lower() in {"1", "true", "yes", "y", "on"}
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

# Инициализация базы данных
def init_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
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
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sound_detections (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            sound_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp TEXT NOT NULL,
            embeddings TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

# Загрузка модели
def load_model():
    global model, class_names
    try:
        print("🔄 Загрузка YAMNet модели...")
        
        # Очищаем кэш
        import tempfile
        cache_dir = os.path.join(tempfile.gettempdir(), 'tfhub_modules')
        if os.path.exists(cache_dir):
            import shutil
            try:
                shutil.rmtree(cache_dir)
                print("🧹 Старый кэш TensorFlow Hub удалён")
            except:
                pass
        
        # Загружаем модель
        model = hub.load("https://tfhub.dev/google/yamnet/1")
        
        # Загружаем классы
        class_names_path = tf.keras.utils.get_file(
            "yamnet_class_map.csv",
            "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv",
        )
        class_names = []
        with open(class_names_path, "r") as f:
            next(f)
            for line in f:
                class_names.append(line.strip().split(",")[2])
        
        print(f"✅ YAMNet модель загружена. Классов: {len(class_names)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return False

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
        SSL_KEY_PATH if os.path.isabs(SSL_KEY_PATH) else os.path.join(script_dir, SSL_KEY_PATH)
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
