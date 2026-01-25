#!/usr/bin/env python3
"""
Sound Sentinel MVP - API Server
Простой и надежный API сервер для детекции звуков
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
import librosa
import tensorflow as tf
import tensorflow_hub as hub

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Инициализация FastAPI
app = FastAPI(title="Sound Sentinel MVP", version="1.0.0")

# CORS для мобильного приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
db_path = "sound_sentinel.db"
model = None
class_names = []
websocket_connections = set()


# Модели данных
class DeviceRegistration(BaseModel):
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


class SoundDetection(BaseModel):
    device_id: str
    sound_type: str
    confidence: float
    timestamp: str
    audio_data: List[float]


class CustomSound(BaseModel):
    name: str
    sound_type: str  # "excluded" или "specific"
    mfcc_features: List[float]
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
            mfcc_features TEXT,
            audio_data TEXT,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """
    )

    # Таблица пользовательских звуков
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_sounds (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sound_type TEXT NOT NULL,
            mfcc_features TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
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


# Извлечение MFCC признаков
def extract_mfcc(audio_data: List[float], sample_rate: int = 16000) -> List[float]:
    """Извлечение MFCC признаков из аудио"""
    try:
        # Конвертация в numpy array
        audio_np = np.array(audio_data, dtype=np.float32)

        # Извлечение MFCC
        mfcc = librosa.feature.mfcc(y=audio_np, sr=sample_rate, n_mfcc=13)

        # Усреднение по времени
        mfcc_mean = np.mean(mfcc, axis=1)

        return mfcc_mean.tolist()
    except Exception as e:
        print(f"❌ Ошибка извлечения MFCC: {e}")
        return []


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
@app.on_event("startup")
async def startup_event():
    """Инициализация при старте"""
    init_database()
    success = load_model()
    if not success:
        print("⚠️ Модель не загружена. Сервер будет работать в ограниченном режиме.")


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
    """Детекция звука"""
    if model is None:
        raise HTTPException(status_code=503, detail="Модель не загружена")

    # Детекция
    detection_result = detect_sound(audio.audio_data)

    if not detection_result["predictions"]:
        raise HTTPException(status_code=400, detail="Не удалось детектировать звук")

    # Сохранение лучшего результата
    top_prediction = detection_result["predictions"][0]

    detection_id = str(uuid.uuid4())
    mfcc_features = extract_mfcc(audio.audio_data)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sound_detections (id, device_id, sound_type, confidence, timestamp, mfcc_features)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            detection_id,
            audio.device_id,
            top_prediction["sound_type"],
            top_prediction["confidence"],
            datetime.now().isoformat(),
            json.dumps(mfcc_features),
        ),
    )

    conn.commit()
    conn.close()

    # Рассылка в реальном времени
    await broadcast_to_websockets(
        {
            "type": "sound_detected",
            "detection_id": detection_id,
            "device_id": audio.device_id,
            "sound_type": top_prediction["sound_type"],
            "confidence": top_prediction["confidence"],
            "timestamp": datetime.now().isoformat(),
        }
    )

    return {
        "detection_id": detection_id,
        "sound_type": top_prediction["sound_type"],
        "confidence": top_prediction["confidence"],
        "all_predictions": detection_result["predictions"],
    }


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
        SELECT id, sound_type, confidence, timestamp, mfcc_features
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
                "mfcc_features": json.loads(row[4]) if row[4] else [],
            }
        )

    conn.close()
    return {"detections": detections, "total_count": total_count}


@app.post("/custom_sounds")
async def add_custom_sound(sound: CustomSound):
    """Добавление пользовательского звука"""
    sound_id = str(uuid.uuid4())

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO custom_sounds (id, name, sound_type, mfcc_features, device_id)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            sound_id,
            sound.name,
            sound.sound_type,
            json.dumps(sound.mfcc_features),
            sound.device_id,
        ),
    )

    conn.commit()
    conn.close()

    return {"sound_id": sound_id, "status": "added"}


@app.get("/custom_sounds")
async def get_custom_sounds():
    """Получение пользовательских звуков"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, sound_type, mfcc_features, device_id, created_at
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
                "mfcc_features": json.loads(row[3]) if row[3] else [],
                "device_id": row[4],
                "created_at": row[5],
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
    print("📡 Сервер будет доступен на http://localhost:8000")
    print("🔗 WebSocket: ws://localhost:8000/ws")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
