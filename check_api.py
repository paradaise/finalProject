#!/usr/bin/env python3
import requests
import json
from datetime import datetime

API_BASE = "http://192.168.0.61:8000"


def check_devices():
    """Проверка устройств"""
    try:
        response = requests.get(f"{API_BASE}/devices")
        devices = response.json()
        print("📱 Устройства:")
        for device in devices:
            print(
                f"  🏠 {device['name']} ({device['ip_address']}) - {device['status']}"
            )
            print(f"     Последний раз: {device['last_seen']}")
        return devices
    except Exception as e:
        print(f"❌ Ошибка устройств: {e}")
        return []


def check_events(device_id):
    """Проверка событий устройства"""
    try:
        response = requests.get(f"{API_BASE}/events/{device_id}")
        events = response.json()
        print(f"\n🎵 События устройства:")
        if events:
            for event in events[-5:]:  # Последние 5 событий
                print(f"  🔊 {event['sound_type']} - {event['confidence']:.1%}")
                print(f"     📅 {event['timestamp']}")
                if event.get("db_level"):
                    print(f"     🔉 Уровень: {event['db_level']:.1f} dB")
        else:
            print("  📭 Событий пока нет")
        return events
    except Exception as e:
        print(f"❌ Ошибка событий: {e}")
        return []


def check_custom_sounds():
    """Проверка пользовательских звуков"""
    try:
        response = requests.get(f"{API_BASE}/custom_sounds")
        sounds = response.json()
        print(f"\n🎛️ Пользовательские звуки:")
        if sounds:
            for sound in sounds:
                print(f"  {sound['name']} ({sound['sound_type']})")
        else:
            print("  📭 Пользовательских звуков нет")
        return sounds
    except Exception as e:
        print(f"❌ Ошибка звуков: {e}")
        return []


def main():
    print("=" * 50)
    print("🔍 Sound Sentinel API Monitor")
    print("=" * 50)

    # Проверка устройств
    devices = check_devices()

    if devices:
        # Проверка событий для каждого устройства
        for device in devices:
            check_events(device["id"])

    # Проверка пользовательских звуков
    check_custom_sounds()

    print(f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
