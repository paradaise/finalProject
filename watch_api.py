#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

API_BASE = "http://192.168.0.61:8000"


def get_device_id():
    """Получить ID первого устройства"""
    try:
        response = requests.get(f"{API_BASE}/devices")
        devices = response.json()
        return devices[0]["id"] if devices else None
    except:
        return None


def watch_events():
    """Следить за событиями в реальном времени"""
    device_id = get_device_id()
    if not device_id:
        print("❌ Устройства не найдены")
        return

    print(f"🎯 Наблюдение за устройством: {device_id}")
    print("🔄 Запуск мониторинга (Ctrl+C для остановки)...")

    last_event_count = 0

    try:
        while True:
            try:
                response = requests.get(f"{API_BASE}/events/{device_id}")
                events = response.json()

                if len(events) > last_event_count:
                    # Новые события!
                    new_events = events[last_event_count:]
                    for event in reversed(new_events):  # Показываем новые события
                        print(f"\n🔊 НОВЫЙ ЗВУК ОБНАРУЖЕН!")
                        print(f"   📵 Тип: {event['sound_type']}")
                        print(f"   📊 Уверенность: {event['confidence']:.1%}")
                        print(f"   📅 Время: {event['timestamp']}")
                        if event.get("db_level"):
                            print(f"   🔉 Уровень: {event['db_level']:.1f} dB")
                        print(f"   📝 {event['description']}")
                        print("-" * 40)

                    last_event_count = len(events)
                else:
                    # Нет новых событий
                    print(
                        f"⏰ {datetime.now().strftime('%H:%M:%S')} - тишина, ждем звуки...",
                        end="\r",
                    )

                time.sleep(2)  # Проверяем каждые 2 секунды

            except KeyboardInterrupt:
                print("\n👋 Остановка мониторинга")
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\n👋 Остановка мониторинга")


if __name__ == "__main__":
    watch_events()
