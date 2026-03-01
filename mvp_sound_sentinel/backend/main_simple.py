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

# Глобальные переменные
db_path = "soundsentinel.db"
model = None
class_names = []
websocket_connections = set()

# Хардкодированные настройки
HOST = "0.0.0.0"
PORT = 8000
USE_SSL = True
SSL_CERT_PATH = "certs/cert.pem"
SSL_KEY_PATH = "certs/key.pem"

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
app = FastAPI(title="Sound Sentinel MVP", version="1.0.0")

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
async def broadcast_to_websockets(data):
    if websocket_connections:
        await asyncio.gather(
            *[ws.send_json(data) for ws in websocket_connections],
            return_exceptions=True
        )

# Эндпоинты
@app.post("/register_device")
async def register_device(device: DeviceRegistration):
    device_id = str(uuid.uuid4())
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO devices 
        (id, name, ip_address, mac_address, model, model_image_url, microphone_info, wifi_signal, status, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'online', ?)
    """, (
        device_id, device.name, device.ip_address, device.mac_address,
        device.model, device.model_image_url, device.microphone_info,
        device.wifi_signal, datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
    
    await broadcast_to_websockets({
        "type": "device_registered",
        "device": device.dict()
    })
    
    return {"device_id": device_id, "status": "registered"}

@app.post("/detect_sound")
async def detect_sound(audio_data: AudioData):
    try:
        if model is None:
            return {"sound_type": "unknown", "confidence": 0.0}
        
        # Простая детекция
        audio_np = np.array(audio_data.audio_data, dtype=np.float32)
        scores, embeddings, spectrogram = model(audio_np)
        
        # Находим класс с максимальной вероятностью
        scores_np = scores.numpy()
        max_index = int(np.argmax(scores_np))
        confidence = float(scores_np[0, max_index])
        sound_type = class_names[max_index] if max_index < len(class_names) else "unknown"
        
        # Сохраняем детекцию
        detection_id = str(uuid.uuid4())
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sound_detections 
            (id, device_id, sound_type, confidence, timestamp, embeddings)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            detection_id, audio_data.device_id, sound_type, confidence,
            audio_data.timestamp, str(embeddings.numpy().tolist())
        ))
        
        conn.commit()
        conn.close()
        
        # Рассылаем через WebSocket
        await broadcast_to_websockets({
            "type": "sound_detected",
            "detection": {
                "id": detection_id,
                "device_id": audio_data.device_id,
                "sound_type": sound_type,
                "confidence": confidence,
                "timestamp": audio_data.timestamp
            }
        })
        
        return {"sound_type": sound_type, "confidence": confidence}
        
    except Exception as e:
        print(f"❌ Ошибка детекции: {e}")
        return {"sound_type": "error", "confidence": 0.0}

@app.get("/devices")
async def get_devices():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM devices ORDER BY created_at DESC")
    devices = []
    
    for row in cursor.fetchall():
        devices.append({
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
            "created_at": row[10]
        })
    
    conn.close()
    return {"devices": devices}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "devices_connected": len(websocket_connections),
        "timestamp": datetime.now().isoformat(),
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.add(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

if __name__ == "__main__":
    print("🚀 Запуск Sound Sentinel API сервера...")
    print(f"📡 Сервер будет доступен на https://{HOST}:{PORT}")
    print(f"🔗 WebSocket: wss://{HOST}:{PORT}/ws")
    
    # Пути к сертификатам
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(script_dir, SSL_CERT_PATH)
    key_path = os.path.join(script_dir, SSL_KEY_PATH)
    
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
