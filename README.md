# 🎙️ Sound Sentinel

**Интеллектуальная система мониторинга звуков в реальном времени**  
Разработана для помощи людям с нарушениями слуха и для умного мониторинга помещений.

---

## 📌 Что умеет приложение

- **Обнаружение звуков в реальном времени** — классификация 521 класса звуков через модель YAMNet (Google AudioSet)
- **Push-уведомления** — мгновенные оповещения при обнаружении важных звуков (пожарная сигнализация, плач ребёнка, разбитое стекло и др.)
- **Пользовательские звуки** — обучение системы на своих звуках (3–5 аудиозаписей + cosine similarity)
- **Множество устройств** — поддержка нескольких Raspberry Pi одновременно
- **WebSocket real-time** — моментальная передача данных на веб-интерфейс
- **Гибкие настройки** — управление списком уведомляемых и исключённых звуков
- **Мониторинг устройств** — CPU, температура, уровень WiFi сигнала, уровень звука

---

## 🏗️ Архитектура системы

```
┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
│    Raspberry Pi     │  HTTP/  │     API Server      │  HTTP/  │    Веб-браузер      │
│   (Audio Client)    │◄───────►│  FastAPI + SQLite   │◄───────►│   React + Vite      │
│                     │  HTTPS  │                     │   WS    │                     │
│ • Захват аудио      │         │ • YAMNet детекция   │         │ • Список устройств  │
│ • Ресемплинг 16kHz  │         │ • Хранение данных   │         │ • История детекций  │
│ • Отправка чанков   │         │ • WebSocket broadcast│        │ • Настройки звуков  │
│ • Системные метрики │         │ • REST API          │         │ • Уведомления       │
└─────────────────────┘         └─────────────────────┘         └─────────────────────┘
```

### Поток обработки звука

```
Микрофон → PyAudio захват (3 сек) → Ресемплинг 16kHz → POST /detect_sound
    → YAMNet embeddings → Top-5 предсказания → Cosine Similarity (custom)
    → Фильтр уведомлений → WebSocket broadcast → Уведомление пользователю
```

<!-- TODO: Вставить диаграмму архитектуры системы -->

### Схема базы данных

```
devices              sound_detections         custom_sounds
───────────          ────────────────         ─────────────
id (PK)              id (PK)                  id (PK)
name                 device_id (FK) ──────►   device_id (FK)
ip_address           sound_type               name
mac_address          confidence               sound_type (specific/excluded)
model                timestamp                embeddings (JSON 1024-d)
wifi_signal          embeddings               centroid (JSON)
cpu_usage                                     threshold
device_temperature   notification_sounds      excluded_sounds
status               ───────────────          ──────────────
last_seen            id (PK)                  id (PK)
                     sound_name               sound_name
                     device_id (FK)           device_id (FK)
```

<!-- TODO: Вставить ER-диаграмму базы данных -->

---

## 🚀 Быстрый старт

### Требования

| Компонент | Минимум |
|-----------|---------|
| Python | 3.9+ |
| Node.js | 18+ |
| RAM (сервер) | 2 GB (YAMNet ~500MB) |
| RAM (Raspberry Pi) | 512 MB |
| ОС (сервер) | Ubuntu 20.04+ / macOS / Windows WSL2 |
| ОС (Pi) | Raspberry Pi OS Lite (64-bit) |

---

## ⚙️ Развёртывание вручную

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-repo/sound-sentinel.git
cd sound-sentinel
```

### 2. Backend (API-сервер)

```bash
cd mvp_sound_sentinel/backend

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

**Необходимые библиотеки (requirements.txt):**

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
tensorflow==2.13.0
tensorflow-hub==0.14.0
numpy==1.24.3
requests==2.31.0
python-multipart==0.0.6
websockets==12.0
sqlite3          # встроена в Python
```

**Генерация SSL-сертификата (требуется для доступа с браузера):**

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem \
  -out certs/cert.pem -days 365 -nodes \
  -subj "/CN=192.168.0.61"  # замените на ваш IP
```

**Запуск:**

```bash
# Из папки backend
python main.py

# Или через uvicorn напрямую
uvicorn main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile certs/key.pem \
  --ssl-certfile certs/cert.pem
```

Сервер будет доступен по адресу: `https://192.168.0.61:8000`  
Документация API: `https://192.168.0.61:8000/docs`

---

### 3. Frontend (Веб-интерфейс)

```bash
cd mvp_sound_sentinel/frontend

# Установить зависимости
npm install
```

**Конфигурация (`src/api/client.ts`):**

```typescript
// Замените IP на адрес вашего API-сервера
const API_BASE_URL = "https://192.168.0.61:8000";
```

**Или через `.env` файл:**

```env
# mvp_sound_sentinel/frontend/.env
VITE_API_HOST=192.168.0.61
VITE_API_PORT=8000
VITE_USE_SSL=true
```

**Запуск в режиме разработки:**

```bash
npm run dev
# Доступно по: https://localhost:3000
```

**Сборка для продакшена:**

```bash
npm run build
npm run preview
```

> ⚠️ **Важно:** Браузер будет предупреждать о самоподписанном сертификате. Нужно добавить исключение вручную, перейдя по `https://192.168.0.61:8000` и нажав "Продолжить".

---

### 4. Клиент Raspberry Pi

```bash
cd mvp_sound_sentinel/raspberry_pi

# Установить системные зависимости
sudo apt update && sudo apt install -y \
  python3-pip python3-venv portaudio19-dev libportaudio2 \
  python3-dev alsa-utils

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить Python-пакеты
pip install -r requirements_pi.txt
```

**Необходимые библиотеки (requirements_pi.txt):**

```
pyaudio==0.2.13
numpy==1.24.3
requests==2.31.0
psutil==5.9.6
urllib3==2.1.0
```

**Конфигурация (`audio_client.py`):**

```python
# Настройки сервера
API_SERVER_URL = "https://192.168.0.61:8000"   # IP вашего сервера
VERIFY_SSL = False                               # False для самоподписанного сертификата

# Настройки аудио
SAMPLE_RATE = 16000    # Частота дискретизации (Hz)
CHANNELS = 1           # Моно
CHUNK_DURATION = 3     # Длительность чанка (секунды)
DEVICE_INDEX = None    # None = системный по умолчанию, или укажите номер
```

**Найти индекс микрофона:**

```bash
python3 -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d['maxInputChannels'] > 0:
        print(f'[{i}] {d[\"name\"]}')
"
```

**Запуск:**

```bash
python3 audio_client.py
```

**Автозапуск через systemd:**

```bash
# Создать файл службы
sudo nano /etc/systemd/system/sound-sentinel.service
```

```ini
[Unit]
Description=Sound Sentinel Audio Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/sound-sentinel/mvp_sound_sentinel/raspberry_pi
ExecStart=/home/pi/sound-sentinel/mvp_sound_sentinel/raspberry_pi/venv/bin/python3 audio_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sound-sentinel
sudo systemctl start sound-sentinel
sudo systemctl status sound-sentinel
```

---

## 🐳 Docker развёртывание

### Структура Docker-файлов

```
sound-sentinel/
├── docker-compose.yml
├── mvp_sound_sentinel/
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   └── Dockerfile
│   └── raspberry_pi/
│       └── Dockerfile
```

### docker-compose.yml

```yaml
version: '3.9'

services:
  backend:
    build:
      context: ./mvp_sound_sentinel/backend
      dockerfile: Dockerfile
    container_name: sound-sentinel-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data/db:/app/data          # SQLite БД
      - ./mvp_sound_sentinel/backend/certs:/app/certs  # SSL сертификаты
      - yamnet-cache:/app/cache/yamnet  # Кэш модели YAMNet
    environment:
      - DB_PATH=/app/data/sound_sentinel.db
      - YAMNET_CACHE_DIR=/app/cache/yamnet
      - HOST=0.0.0.0
      - PORT=8000
      - SSL_KEY=/app/certs/key.pem
      - SSL_CERT=/app/certs/cert.pem
    restart: unless-stopped
    networks:
      - sentinel-net

  frontend:
    build:
      context: ./mvp_sound_sentinel/frontend
      dockerfile: Dockerfile
    container_name: sound-sentinel-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_HOST=192.168.0.61   # IP сервера backend
      - VITE_API_PORT=8000
      - VITE_USE_SSL=true
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - sentinel-net

volumes:
  yamnet-cache:

networks:
  sentinel-net:
    driver: bridge
```

**Запуск через Docker Compose:**

```bash
# Собрать и запустить
docker compose up -d --build

# Посмотреть логи
docker compose logs -f backend
docker compose logs -f frontend

# Остановить
docker compose down

# Пересобрать только backend
docker compose up -d --build backend
```

---

## 🔧 Конфигурационные файлы

### Backend: переменные окружения

```env
# mvp_sound_sentinel/backend/.env

# База данных
DB_PATH=./data/sound_sentinel.db

# SSL
SSL_KEY=./certs/key.pem
SSL_CERT=./certs/cert.pem

# Сервер
HOST=0.0.0.0
PORT=8000

# YAMNet
YAMNET_TF_HUB_URL=https://tfhub.dev/google/yamnet/1
YAMNET_CACHE_DIR=./cache/yamnet

# Настройки детекции
CONFIDENCE_THRESHOLD=0.3
CUSTOM_MATCH_DEFAULT_THRESHOLD=0.7

# CORS (разделитель запятая)
CORS_ORIGINS=https://localhost:3000,https://192.168.0.61:3000
```

### Frontend: переменные окружения

```env
# mvp_sound_sentinel/frontend/.env

VITE_API_HOST=192.168.0.61
VITE_API_PORT=8000
VITE_USE_SSL=true

# UI
VITE_THEME=auto
VITE_LANGUAGE=ru

# Граф аудио
VITE_AUDIO_CHART_UPDATE_INTERVAL=100
VITE_AUDIO_CHART_MAX_POINTS=100

# Уведомления
VITE_NOTIFICATION_AUTO_HIDE_DELAY=5000
VITE_MAX_NOTIFICATIONS=10

# Данные
VITE_DETECTIONS_REFRESH_INTERVAL=1000
VITE_MAX_DETECTIONS_DISPLAY=50

# WebSocket
VITE_WS_RECONNECT_DELAY=3000
VITE_WS_MAX_RECONNECT_ATTEMPTS=10

# Отладка
VITE_DEBUG=false
VITE_VERBOSE_LOGGING=false
```

---

## 📡 API: основные эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/register_device` | Регистрация Raspberry Pi |
| `POST` | `/detect_sound` | Отправка аудио для детекции |
| `GET` | `/devices` | Список всех устройств |
| `DELETE` | `/devices/{id}` | Удаление устройства |
| `GET` | `/detections/{device_id}` | История детекций |
| `DELETE` | `/devices/{id}/detections` | Очистка истории |
| `GET` | `/yamnet_sounds` | Список всех 521 класса YAMNet |
| `POST` | `/custom_sounds/train` | Обучение нового кастомного звука |
| `GET` | `/custom_sounds` | Список кастомных звуков |
| `DELETE` | `/custom_sounds/{id}` | Удаление кастомного звука |
| `GET` | `/notification_settings/{device_id}` | Настройки уведомлений |
| `POST` | `/notification_sounds` | Добавить звук в уведомления |
| `POST` | `/excluded_sounds` | Добавить звук в исключения |
| `WS` | `/ws` | WebSocket подключение |
| `GET` | `/health` | Проверка состояния |

### WebSocket события

```jsonc
// Обнаружен звук
{
  "type": "sound_detected",
  "device_id": "uuid",
  "sound_type": "Fire alarm",
  "confidence": 0.94,
  "timestamp": "2026-01-01T12:00:00",
  "should_notify": true
}

// Устройство зарегистрировано
{
  "type": "device_registered",
  "device_id": "uuid",
  "device": { "name": "RPi Kitchen", "status": "online" }
}

// Обновление уровня звука
{
  "type": "audio_level_updated",
  "device_id": "uuid",
  "db_level": 45.2
}
```

<!-- TODO: Вставить диаграмму WebSocket взаимодействия -->

---

## 🧪 Тестирование подключения

```bash
# Проверить доступность API
curl -k https://192.168.0.61:8000/health

# Зарегистрировать устройство вручную
curl -k -X POST https://192.168.0.61:8000/register_device \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Device",
    "ip_address": "192.168.0.100",
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "model": "Raspberry Pi 4",
    "wifi_signal": 75
  }'

# Получить список устройств
curl -k https://192.168.0.61:8000/devices

# Проверить WebSocket (нужен wscat: npm install -g wscat)
wscat -c wss://192.168.0.61:8000/ws --no-check
```

---

## 🛠️ Устранение неполадок

### Проблемы с аудио на Raspberry Pi

```bash
# Перезапустить ALSA
sudo alsa force-reload

# Остановить PulseAudio (если мешает)
systemctl --user stop pulseaudio
systemctl --user disable pulseaudio

# Проверить аудиоустройства
arecord -l

# Тест записи
arecord -D hw:1,0 -f S16_LE -r 16000 -d 3 test.wav
```

### Проблема: "SSL certificate error" в браузере

1. Перейдите в браузере на `https://192.168.0.61:8000`
2. Нажмите "Дополнительно" → "Перейти на сайт"
3. Вернитесь на `https://192.168.0.61:3000`

### Проблема: YAMNet не загружается

```bash
# Очистить кэш TensorFlow Hub
rm -rf /tmp/tfhub_modules
rm -rf ~/.cache/tfhub_modules

# Проверить интернет-доступ до tfhub.dev
curl -I https://tfhub.dev/google/yamnet/1
```

### Проблема: WebSocket не подключается

- Убедитесь, что URL в `client.ts` содержит правильный IP
- Проверьте, что порт 8000 открыт в файерволе: `sudo ufw allow 8000`
- Для wss:// нужен SSL-сертификат на сервере

---

## 📁 Структура проекта

```
sound-sentinel/
├── README.md
├── docker-compose.yml
├── mvp_sound_sentinel/
│   ├── backend/
│   │   ├── main.py                  # FastAPI приложение
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── .env
│   │   ├── certs/                   # SSL сертификаты
│   │   ├── data/                    # SQLite БД
│   │   ├── cache/yamnet/            # Кэш модели
│   │   ├── database/
│   │   │   └── init_db.py           # Инициализация БД
│   │   └── utils/
│   │       ├── yamnet.py            # Загрузка и инференс YAMNet
│   │       ├── yamnet_cached.py     # YAMNet с кэшированием
│   │       ├── similarity.py        # Cosine similarity
│   │       ├── custom_matching.py   # Поиск кастомных звуков
│   │       └── notifications.py     # Логика уведомлений
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.tsx              # Корневой компонент
│   │   │   ├── api/client.ts        # HTTP/WS клиент
│   │   │   ├── components/          # UI компоненты
│   │   │   └── data/
│   │   │       └── criticalSounds.ts # Списки критических звуков
│   │   ├── Dockerfile
│   │   ├── .env
│   │   └── vite.config.ts
│   └── raspberry_pi/
│       ├── audio_client.py          # Клиент захвата аудио
│       ├── requirements_pi.txt
│       └── Dockerfile
└── docs/
    └── diagrams/                    # Диаграммы архитектуры
```

---

## 📊 Технические характеристики

| Параметр | Значение |
|----------|----------|
| Модель классификации | YAMNet (Google) |
| Классов звуков | 521 (AudioSet) |
| Размер модели | ~18 MB |
| Частота дискретизации | 16 000 Hz |
| Длительность чанка | 3 секунды |
| Размерность эмбеддингов | 1024 |
| Алгоритм поиска custom-звуков | Cosine Similarity + Centroid |
| Порог схожести по умолчанию | 0.70 |
| База данных | SQLite |
| Протокол реального времени | WebSocket |

---

## 📝 Лицензия

MIT License — свободное использование и модификация.
