#!/usr/bin/env python3
"""
Полный сброс базы данных для чистого старта
"""

import sqlite3
import os

db_path = "sound_sentinel.db"


def reset_database():
    """Полностью удаляет и создает новую базу данных"""
    try:
        # Удаляем старую базу
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️ Старая база данных удалена")

        # Создаем новую базу
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Таблица устройств
        cursor.execute(
            """
            CREATE TABLE devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                mac_address TEXT UNIQUE NOT NULL,
                model TEXT DEFAULT 'Unknown',
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
            CREATE TABLE sound_detections (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                sound_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL,
                mfcc_features TEXT,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        """
        )

        # Таблица пользовательских звуков
        cursor.execute(
            """
            CREATE TABLE custom_sounds (
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

        print("✅ Новая база данных создана успешно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка сброса базы: {e}")
        return False


if __name__ == "__main__":
    reset_database()
