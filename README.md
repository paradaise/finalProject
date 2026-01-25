# Sound Sentinel

**Интеллектуальная система мониторинга звуков в реальном времени**

## 📋 Обзор

Sound Sentinel - это распределенная система для обнаружения и классификации звуков с использованием Raspberry Pi в качестве устройств сбора данных и веб-интерфейса для мониторинга.

## 🏗️ Архитектура системы

```
┌─────────────────┐    WiFi/Network    ┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   Raspberry Pi  │ ────────────────── │   API Server    │ ────────────────── │   Web Client    │
│   (Audio Client)│                    │  (FastAPI + DB) │                    │   (React + TS)  │
└─────────────────┘                    └─────────────────┘                    └─────────────────┘
        │                                      │                                      │
        │ 1. Захват аудио                      │ 2. Детекция звука                   │ 3. Отображение
        │ 2. Отправка на сервер                │ 3. Сохранение в БД                  │ 4. Управление
        │ 3. Получение команд                  │ 4. WebSocket обновления             │ 5. Настройки
        └──────────────────────────────────────┴──────────────────────────────────────┴──────────────────────────────────────┘
```

## 🔄 Процесс детекции звуков

### 1. Захват аудио на Raspberry Pi

```python
# Параметры захвата
SAMPLE_RATE = 16000 Hz     # Стандартная частота для YAMNet
CHANNELS = 1               # Моно
CHUNK_DURATION = 3 сек     # Длительность чанка
FORMAT = Float32           # Формат сэмплов
```

### 2. Обработка и отправка

```python
# Цикл обработки
while is_running:
    audio_data = capture_audio_chunk()      # Захват 3-секундного чанка
    resampled = resample_to_16000(audio)     # Ресемплинг если нужно
    send_to_server(resampled)               # HTTP POST на API
    sleep(3)                                # Пауза между чанками
```

### 3. Детекция на сервере

```python
# YAMNet детекция
def detect_sound(audio_data):
    embeddings = yamnet(audio_data)         # Извлечение признаков
    predictions = classifier(embeddings)     # Классификация
    return top_predictions(predictions)      # Топ-5 результатов
```

## 🌐 Протоколы взаимодействия

### HTTP API

- `POST /register_device` - Регистрация устройства
- `POST /detect_sound` - Детекция звука
- `GET /devices` - Список устройств
- `DELETE /devices/{id}` - Удаление устройства
- `GET /detections/{device_id}` - История детекций

### WebSocket

- `ws://server:8000/ws` - Реальные обновления
- События: `device_registered`, `device_deleted`, `sound_detected`

### База данных (SQLite)

```sql
CREATE TABLE devices (
    id TEXT PRIMARY KEY,                    -- UUID устройства
    name TEXT NOT NULL,                      -- Имя устройства
    ip_address TEXT NOT NULL,               -- IP адрес
    mac_address TEXT NOT NULL,              -- MAC адрес
    model TEXT DEFAULT 'Unknown',           -- Модель устройства
    model_image_url TEXT,                    -- URL изображения модели
    microphone_info TEXT,                   -- Информация о микрофоне
    wifi_signal INTEGER DEFAULT 0,          -- Сигнал WiFi (%)
    status TEXT DEFAULT 'offline',          -- Статус
    last_seen TEXT,                          -- Последняя активность
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sound_detections (
    id TEXT PRIMARY KEY,                    -- UUID детекции
    device_id TEXT NOT NULL,                -- ID устройства
    sound_type TEXT NOT NULL,               -- Тип звука
    confidence REAL NOT NULL,               -- Уверенность (0-1)
    timestamp TEXT NOT NULL,                -- Время детекции
    mfcc_features TEXT,                     -- MFCC признаки (JSON)
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE custom_sounds (
    id TEXT PRIMARY KEY,                    -- UUID звука
    name TEXT NOT NULL,                      -- Название
    sound_type TEXT NOT NULL,               -- Тип (excluded/important)
    mfcc_features TEXT NOT NULL,           -- MFCC признаки
    device_id TEXT NOT NULL,                -- ID устройства
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
```

## 🎯 Основные классы YAMNet для тестирования

YAMNet обучен на **AudioSet-YouTube** датасете и распознает **521 класс звуков**:

### 🔊 Человеческие звуки

- `Speech`, `Laughter`, `Crying baby`, `Sneeze`, `Cough`
- `Footsteps`, `Clapping`, `Finger snapping`

### 🎵 Музыкальные инструменты

- `Piano`, `Guitar`, `Violin`, `Drums`, `Flute`
- `Singing`, `Whistling`, `Humming`

### 🏠 Бытовые звуки

- `Doorbell`, `Telephone bell ringing`, `Alarm`
- `Microwave oven`, `Dishwasher`, `Vacuum cleaner`
- `Typing`, `Computer keyboard`, `Mouse click`

### 🚖 Транспорт и улица

- `Car horn`, `Siren`, `Traffic noise`, `Train`
- `Airplane`, `Helicopter`, `Boat`

### 🌿 Природа

- `Bird`, `Dog`, `Cat`, `Insect`, `Wind`
- `Rain`, `Thunder`, `Water`, `Fire`

### 🏭 Промышленные

- `Power tool`, `Drill`, `Saw`, `Hammer`
- `Engine`, `Generator`, `Machinery`

## 🛠️ Технологический стек

### Backend

- **FastAPI** - Веб-фреймворк API
- **SQLite** - База данных
- **TensorFlow** - Машинное обучение
- **YAMNet** - Модель детекции звуков
- **WebSocket** - Реальное время

### Frontend

- **React 18** - UI фреймворк
- **TypeScript** - Типизация
- **TailwindCSS** - Стилизация
- **Lucide** - Иконки

### Client (Raspberry Pi)

- **Python 3.9+** - Основной язык
- **PyAudio** - Захват аудио
- **NumPy** - Обработка данных
- **Requests** - HTTP клиент

## 📊 Схема данных

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOUND SENTINEL                           │
│                        DATABASE SCHEMA                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     DEVICES     │    │ SOUND_DETECTIONS│    │  CUSTOM_SOUNDS  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │◄───┤ device_id (FK) │◄───┤ device_id (FK) │
│ name            │    │ id (PK)         │    │ id (PK)         │
│ ip_address      │    │ sound_type      │    │ name            │
│ mac_address     │    │ confidence      │    │ sound_type      │
│ model           │    │ timestamp       │    │ mfcc_features   │
│ model_image_url │    │ mfcc_features   │    │ created_at      │
│ microphone_info │    └─────────────────┘    └─────────────────┘
│ wifi_signal     │
│ status          │
│ last_seen       │
│ created_at      │
└─────────────────┘
```

## 🚀 Быстрый старт

### 1. Запуск API сервера

```bash
cd mvp_sound_sentinel/api_server
pip install -r requirements.txt
python main.py
```

### 2. Запуск веб-интерфейса

```bash
cd mvp_sound_sentinel/mobile_app
npm install
npm run dev
```

### 3. Запуск клиента на Raspberry Pi

```bash
cd mvp_sound_sentinel/raspberry_pi
pip install -r requirements.txt
python audio_client.py
```

## 📱 API Ручки

### Устройства

```http
POST /register_device
Content-Type: application/json

{
  "name": "Raspberry Pi Monitor",
  "ip_address": "192.168.0.228",
  "mac_address": "68:a2:8b:2c:b1:c6",
  "model": "Raspberry Pi Zero 2 W Rev 1.0",
  "model_image_url": "/images/raspberry-pi-zero-2-w.png",
  "microphone_info": "Microphone [Fifine Microphone], device 0",
  "wifi_signal": 82
}
```

```http
GET /devices
Response: [
  {
    "id": "9619ab8b-35e6-41f9-b54c-cfa7bfe3c614",
    "name": "Raspberry Pi Monitor",
    "status": "online",
    "last_seen": "2026-01-25T20:15:30.123456",
    ...
  }
]
```

### Детекции

```http
POST /detect_sound
Content-Type: application/json

{
  "device_id": "9619ab8b-35e6-41f9-b54c-cfa7bfe3c614",
  "audio_data": [0.1, -0.2, 0.3, ...],
  "sample_rate": 16000
}

Response: {
  "detection_id": "abc123...",
  "sound_type": "Speech",
  "confidence": 0.85,
  "all_predictions": [...]
}
```

## 🎛️ WebSocket события

```javascript
// Подключение
const ws = new WebSocket('ws://192.168.0.61:8000/ws');

// Новая детекция
{
  "type": "sound_detected",
  "device_id": "9619ab8b-35e6-41f9-b54c-cfa7bfe3c614",
  "sound_type": "Speech",
  "confidence": 0.85,
  "timestamp": "2026-01-25T20:15:30.123456"
}

// Устройство зарегистрировано
{
  "type": "device_registered",
  "device_id": "9619ab8b-35e6-41f9-b54c-cfa7bfe3c614",
  "name": "Raspberry Pi Monitor",
  "status": "online"
}
```

## 🔧 Конфигурация

### Raspberry Pi Client

```python
# audio_client.py
API_SERVER_URL = "http://192.168.0.61:8000"
SAMPLE_RATE = 16000
CHUNK_DURATION = 3  # секунды
```

### API Server

```python
# main.py
DB_PATH = "sound_sentinel.db"
MODEL_PATH = "yamnet.h5"
CONFIDENCE_THRESHOLD = 0.3
```

## 📈 Мониторинг и отладка

### Логи клиента

```bash
# Уровень детекции
🎵 [20:15:30] Speech: 85.2%
🎵 [20:15:33] Keyboard typing: 72.1%
🎵 [20:15:36] Background noise (ниже порога)
```

### Логи сервера

```bash
✅ Устройство зарегистрировано: Raspberry Pi Monitor
🔄 Устройство обновлено: Raspberry Pi Monitor
🎵 Детекция: Speech (85.2%) от устройства 9619ab8b...
```

## 🎯 Особенности реализации

### MFCC извлечение

```python
def extract_mfcc(audio_data, sample_rate=16000, n_mfcc=13):
    # Извлечение 13 MFCC коэффициентов
    mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
    # Нормализация
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    return mfcc.T.tolist()  # Транспонирование для хранения
```

### Ресемплинг аудио

```python
def resample_audio(audio_data, original_rate, target_rate=16000):
    if original_rate != target_rate:
        # Используем librosa для качественного ресемплинга
        return librosa.resample(audio_data, orig_sr=original_rate, target_sr=target_rate)
    return audio_data
```

### WebSocket broadcast

```python
async def broadcast_to_websockets(message: dict):
    if websocket_connections:
        message_str = json.dumps(message)
        for websocket in websocket_connections.copy():
            try:
                await websocket.send_text(message_str)
            except:
                websocket_connections.discard(websocket)
```

## 🔒 Безопасность

- **CORS** настроен для локальной сети
- **Валидация** входных данных
- **SQL Injection** защита через параметры
- **Rate limiting** для API эндпоинтов

## 🚨 Устранение неполадок

### Проблемы с аудио на Raspberry Pi

```bash
# Остановка конфликтующих процессов
sudo systemctl stop pulseaudio
sudo pkill -f pulseaudio
sudo alsa force-reload

# Проверка устройств
arecord -l
python3 -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'[{i}] {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels']>0]"
```

### Проблемы с сетью

```bash
# Проверка подключения
ping 192.168.0.61
curl -X POST http://192.168.0.61:8000/health

# Проверка WebSocket
wscat -c ws://192.168.0.61:8000/ws
```

## 📝 Лицензия

MIT License - свободное использование и модификация

---

**Sound Sentinel** - превращаем любой Raspberry Pi в умную систему мониторинга звуков! 🎙️🔊
