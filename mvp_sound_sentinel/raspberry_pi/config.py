#!/usr/bin/env python3
"""
Конфигурация Sound Sentinel Raspberry Pi Client
"""

import os
from typing import Dict, List

class Config:
    """Основные настройки клиента"""
    
    # Сервер
    SERVER_HOST: str = os.getenv("SERVER_HOST", "192.168.0.94")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    USE_SSL: bool = os.getenv("USE_SSL", "true").lower() == "true"
    API_BASE_URL: str = f"{'https' if USE_SSL else 'http'}://{SERVER_HOST}:{SERVER_PORT}"
    
    # Устройство
    DEVICE_NAME: str = os.getenv("DEVICE_NAME", "Raspberry Pi Monitor")
    DEVICE_TYPE: str = os.getenv("DEVICE_TYPE", "raspberry_pi")
    
    # Аудио
    SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", "16000"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1024"))
    CHANNELS: int = int(os.getenv("CHANNELS", "1"))
    AUDIO_FORMAT: str = os.getenv("AUDIO_FORMAT", "int16")
    
    # Детекция
    DETECTION_INTERVAL: float = float(os.getenv("DETECTION_INTERVAL", "2.0"))  # секунды
    DETECTION_THRESHOLD: float = float(os.getenv("DETECTION_THRESHOLD", "0.5"))
    MIN_AUDIO_LENGTH: float = float(os.getenv("MIN_AUDIO_LENGTH", "1.0"))  # секунды
    MAX_AUDIO_LENGTH: float = float(os.getenv("MAX_AUDIO_LENGTH", "3.0"))  # секунды
    
    # Отправка данных
    AUDIO_LEVEL_UPDATE_INTERVAL: float = float(os.getenv("AUDIO_LEVEL_UPDATE_INTERVAL", "0.5"))  # секунды
    DEVICE_INFO_UPDATE_INTERVAL: float = float(os.getenv("DEVICE_INFO_UPDATE_INTERVAL", "60"))  # секунды
    WIFI_SIGNAL_UPDATE_INTERVAL: float = float(os.getenv("WIFI_SIGNAL_UPDATE_INTERVAL", "30"))  # секунды
    
    # Микрофон
    MICROPHONE_DEVICE_INDEX: int = int(os.getenv("MICROPHONE_DEVICE_INDEX", "0"))
    AUTO_SELECT_MICROPHONE: bool = os.getenv("AUTO_SELECT_MICROPHONE", "true").lower() == "true"
    
    # WebSocket
    WS_RECONNECT_DELAY: float = float(os.getenv("WS_RECONNECT_DELAY", "5.0"))  # секунды
    WS_MAX_RECONNECT_ATTEMPTS: int = int(os.getenv("WS_MAX_RECONNECT_ATTEMPTS", "10"))
    WS_PING_INTERVAL: float = float(os.getenv("WS_PING_INTERVAL", "30"))  # секунды
    
    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    VERBOSE: bool = os.getenv("VERBOSE", "false").lower() == "true"
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "audio_client.log")
    
    # Статистика
    STATS_UPDATE_INTERVAL: float = float(os.getenv("STATS_UPDATE_INTERVAL", "300"))  # секунды
    
    # Обработка ошибок
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "2.0"))  # секунды
    
    # Системные
    CPU_USAGE_WARNING_THRESHOLD: float = float(os.getenv("CPU_USAGE_WARNING_THRESHOLD", "80"))  # %
    MEMORY_USAGE_WARNING_THRESHOLD: float = float(os.getenv("MEMORY_USAGE_WARNING_THRESHOLD", "80"))  # %
    DISK_USAGE_WARNING_THRESHOLD: float = float(os.getenv("DISK_USAGE_WARNING_THRESHOLD", "90"))  # %

class DevelopmentConfig(Config):
    """Настройки для разработки"""
    LOG_LEVEL: str = "DEBUG"
    VERBOSE: bool = True
    DETECTION_INTERVAL: float = 1.0
    AUDIO_LEVEL_UPDATE_INTERVAL: float = 0.2

class ProductionConfig(Config):
    """Настройки для продакшена"""
    LOG_LEVEL: str = "WARNING"
    VERBOSE: bool = False
    LOG_TO_FILE: bool = True

# Выбор конфигурации
def get_config():
    env = os.getenv("SOUND_SENTINEL_ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()

# Глобальный объект конфигурации
config = get_config()

# Удобные функции для получения URL
def get_api_url(endpoint: str) -> str:
    """Получить полный URL для API эндпоинта"""
    return f"{config.API_BASE_URL}{endpoint}"

def get_ws_url() -> str:
    """Получить WebSocket URL"""
    protocol = "wss" if config.USE_SSL else "ws"
    return f"{protocol}://{config.SERVER_HOST}:{config.SERVER_PORT}/ws"

# Вывод текущей конфигурации при запуске
def print_config():
    """Вывести текущую конфигурацию"""
    print(f"🔧 Конфигурация клиента:")
    print(f"   🌐 Сервер: {config.API_BASE_URL}")
    print(f"   🎤 Аудио: {config.SAMPLE_RATE}Hz, chunk={config.CHUNK_SIZE}")
    print(f"   🕐 Детекция каждые {config.DETECTION_INTERVAL}с")
    print(f"   📡 Уровень звука каждые {config.AUDIO_LEVEL_UPDATE_INTERVAL}с")
    print(f"   📶 WiFi каждые {config.WIFI_SIGNAL_UPDATE_INTERVAL}с")
    print(f"   📊 Логирование: {config.LOG_LEVEL}")

if __name__ == "__main__":
    print_config()
