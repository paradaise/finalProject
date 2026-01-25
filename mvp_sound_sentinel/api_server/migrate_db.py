#!/usr/bin/env python3
"""
Миграция базы данных для добавления новых колонок
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

        # Добавляем колонку model если ее нет
        if "model" not in columns:
            print("➕ Добавляю колонку 'model'...")
            cursor.execute(
                "ALTER TABLE devices ADD COLUMN model TEXT DEFAULT 'Unknown'"
            )

        # Добавляем колонку wifi_signal если ее нет
        if "wifi_signal" not in columns:
            print("➕ Добавляю колонку 'wifi_signal'...")
            cursor.execute(
                "ALTER TABLE devices ADD COLUMN wifi_signal INTEGER DEFAULT 0"
            )

        conn.commit()
        conn.close()

        print("✅ Миграция базы данных завершена успешно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


if __name__ == "__main__":
    migrate_database()
