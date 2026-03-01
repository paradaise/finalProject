#!/usr/bin/env python3
"""
Конфигурация Sound Sentinel Backend
"""

import os
from typing import List

class Config:
    """Основные настройки сервера"""
    
    # Сервер
    HOST: str = os.getenv("SOUND_SENTINEL_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("SOUND_SENTINEL_PORT", "8000"))
    DEBUG: bool = os.getenv("SOUND_SENTINEL_DEBUG", "false").lower() == "true"
    
    # SSL
    SSL_CERT_PATH: str = os.getenv("SSL_CERT_PATH", "certs/cert.pem")
    SSL_KEY_PATH: str = os.getenv("SSL_KEY_PATH", "certs/key.pem")
    USE_SSL: bool = os.getenv("USE_SSL", "true").lower() == "true"
    
    # База данных
    DB_PATH: str = os.getenv("DB_PATH", "soundsentinel.db")
    
    # Модель YAMNet
    MODEL_URLS: List[str] = [
        "https://tfhub.dev/google/yamnet/1",
        "https://tfhub.dev/google/yamnet/1?tf-hub-format=compressed"
    ]
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", None)  # None = default temp
    
    # Детекция
    DETECTION_THRESHOLD: float = float(os.getenv("DETECTION_THRESHOLD", "0.5"))
    MAX_DETECTIONS_PER_DEVICE: int = int(os.getenv("MAX_DETECTIONS_PER_DEVICE", "1000"))
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SUPPRESS_TENSORFLOW_WARNINGS: bool = os.getenv("SUPPRESS_TENSORFLOW_WARNINGS", "true").lower() == "true"

class DevelopmentConfig(Config):
    """Настройки для разработки"""
    DEBUG: bool = True
    USE_SSL: bool = False
    LOG_LEVEL: str = "DEBUG"

class ProductionConfig(Config):
    """Настройки для продакшена"""
    DEBUG: bool = False
    USE_SSL: bool = True
    LOG_LEVEL: str = "WARNING"

# Выбор конфигурации
def get_config():
    env = os.getenv("SOUND_SENTINEL_ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()

# Глобальный объект конфигурации
config = get_config()
