#!/usr/bin/env python3
"""
Миграция базы данных для добавления новых колонок model_image_url и microphone_info
"""

import sqlite3
import os

db_path = "sound_sentinel.db"


def migrate_database():
    """Добавляет новые колонки в существующую базу данных"""
    if not os.path.exists(db_path):
        print(
            "❌ База данных не найдена. Запустите основной сервер для создания новой БД."
        )
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем существующие колонки
        cursor.execute("PRAGMA table_info(devices)")
        columns = [row[1] for row in cursor.fetchall()]

        print(f"📋 Текущие колонки: {columns}")

        # Добавляем колонку model_image_url если ее нет
        if "model_image_url" not in columns:
            print("➕ Добавляю колонку 'model_image_url'...")
            cursor.execute("ALTER TABLE devices ADD COLUMN model_image_url TEXT")

        # Добавляем колонку microphone_info если ее нет
        if "microphone_info" not in columns:
            print("➕ Добавляю колонку 'microphone_info'...")
            cursor.execute("ALTER TABLE devices ADD COLUMN microphone_info TEXT")

        conn.commit()
        conn.close()

        print("✅ Миграция базы данных завершена успешно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


if __name__ == "__main__":
    migrate_database()
