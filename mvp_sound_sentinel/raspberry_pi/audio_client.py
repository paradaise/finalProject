#!/usr/bin/env python3
"""
Sound Sentinel MVP - Клиент для Raspberry Pi
Простой и надежный клиент для записи и отправки аудио
"""

import os
import sys
import time
import json
import uuid
import socket
import requests
import numpy as np
import pyaudio
import threading
from datetime import datetime

# Конфигурация
API_SERVER_URL = "http://192.168.0.61:8000"  # IP вашего ПК с API сервером
DEVICE_NAME = "Raspberry Pi Monitor"
SAMPLE_RATE = 16000  # YAMNet ожидает 16kHz
CHANNELS = 1
FORMAT = pyaudio.paFloat32
CHUNK_DURATION = 3  # секунды на один чанк (увеличил для реже отправки)
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)


class AudioClient:
    def __init__(self):
        self.device_id = None
        self.is_running = False
        self.audio = None
        self.stream = None

    def get_device_info(self):
        """Получение информации об устройстве"""
        try:
            # Получаем реальный IP адрес (не localhost)
            ip_address = self.get_real_ip_address()

            # Получаем MAC адрес
            mac = ":".join(
                [
                    "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                    for elements in range(0, 2 * 6, 2)
                ][::-1]
            )

            # Определяем модель Raspberry Pi
            model = self.get_raspberry_pi_model()

            # Получаем уровень сигнала WiFi (примерная реализация)
            wifi_signal = self.get_wifi_signal()

            return {
                "name": DEVICE_NAME,
                "ip_address": ip_address,
                "mac_address": mac,
                "model": model,
                "wifi_signal": wifi_signal,
            }
        except Exception as e:
            print(f"❌ Ошибка получения информации об устройстве: {e}")
            return None

    def get_real_ip_address(self):
        """Получение реального IP адреса, а не 127.0.0.1"""
        try:
            # Создаем сокет для подключения к внешнему адресу
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                real_ip = s.getsockname()[0]
            return real_ip
        except:
            # Fallback к hostname
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except:
                return "127.0.0.1"

    def get_raspberry_pi_model(self):
        """Определение модели Raspberry Pi"""
        try:
            # Сначала пробуем файл из /sys/firmware/devicetree/base/model
            try:
                with open("/sys/firmware/devicetree/base/model", "r") as f:
                    model_info = f.read().strip()
                    if "Raspberry Pi" in model_info:
                        return model_info
            except:
                pass

            # Fallback к /proc/cpuinfo
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("Model"):
                        model_info = line.split(":")[1].strip()
                        if "Raspberry Pi" in model_info:
                            return model_info
            return "Raspberry Pi (Unknown model)"
        except:
            return "Raspberry Pi"

    def get_wifi_signal(self):
        """Получение уровня сигнала WiFi в dBm"""
        try:
            # Попытка получить уровень сигнала через iwconfig
            import subprocess

            result = subprocess.run(
                ["iwconfig", "wlan0"], capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Signal level=" in line:
                        signal_part = line.split("Signal level=")[1].split(" ")[0]
                        return int(signal_part.replace("dBm", ""))
        except:
            pass
        return -70  # Значение по умолчанию

    def register_device(self):
        """Регистрация устройства на API сервере"""
        try:
            device_info = self.get_device_info()
            if not device_info:
                return False

            print(f"🔄 Регистрация устройства: {device_info['name']}")

            response = requests.post(
                f"{API_SERVER_URL}/register_device", json=device_info, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.device_id = data["device_id"]
                print(f"✅ Устройство зарегистрировано. ID: {self.device_id}")
                return True
            else:
                print(
                    f"❌ Ошибка регистрации: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Ошибка подключения к API серверу: {e}")
            return False

    def init_audio(self):
        """Инициализация аудио потока"""
        try:
            self.audio = pyaudio.PyAudio()

            # Поиск доступных микрофонов
            print("🎤 Поиск доступных микрофонов...")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    print(
                        f"   {i}: {info['name']} (каналов: {info['maxInputChannels']})"
                    )

            # Используем первый доступный микрофон
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                input_device_index=None,  # Автовыбор
            )

            print("✅ Аудио поток инициализирован")
            return True

        except Exception as e:
            print(f"❌ Ошибка инициализации аудио: {e}")
            return False

    def send_audio_chunk(self, audio_data):
        """Отправка аудио чанка на детекцию"""
        try:
            # Конвертация в список для JSON
            audio_list = audio_data.tolist()

            payload = {
                "device_id": self.device_id,
                "audio_data": audio_list,
                "sample_rate": SAMPLE_RATE,
            }

            response = requests.post(
                f"{API_SERVER_URL}/detect_sound", json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                confidence = result.get("confidence", 0)
                sound_type = result.get("sound_type", "Unknown")

                # Показываем только если уверенность > 0.3
                if confidence > 0.3:
                    print(f"🔊 {sound_type}: {confidence:.1%}")

                return True
            else:
                print(f"❌ Ошибка детекции: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Ошибка отправки аудио: {e}")
            return False

    def audio_recording_loop(self):
        """Основной цикл записи аудио"""
        print("🎙️ Начало записи аудио...")
        print("🔄 Нажмите Ctrl+C для остановки")

        while self.is_running:
            try:
                # Чтение аудио чанка
                audio_data = np.frombuffer(
                    self.stream.read(CHUNK_SIZE, exception_on_overflow=False),
                    dtype=np.float32,
                )

                # Проверка уровня звука (простая детекция тишины)
                if np.max(np.abs(audio_data)) > 0.01:  # Порог тишины
                    # Отправка на детекцию в отдельном потоке
                    threading.Thread(
                        target=self.send_audio_chunk, args=(audio_data,), daemon=True
                    ).start()

            except Exception as e:
                print(f"❌ Ошибка записи: {e}")
                time.sleep(1)  # Пауза перед повторной попыткой

    def start(self):
        """Запуск клиента"""
        print("🚀 Запуск Sound Sentinel клиента для Raspberry Pi")
        print(f"📡 API сервер: {API_SERVER_URL}")

        # Регистрация устройства
        if not self.register_device():
            print("❌ Не удалось зарегистрировать устройство")
            return False

        # Инициализация аудио
        if not self.init_audio():
            print("❌ Не удалось инициализировать аудио")
            return False

        # Запуск записи
        self.is_running = True

        try:
            self.audio_recording_loop()
        except KeyboardInterrupt:
            print("\n👋 Остановка по запросу пользователя")
        finally:
            self.stop()

        return True

    def stop(self):
        """Остановка клиента"""
        print("🔄 Остановка клиента...")
        self.is_running = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.audio:
            self.audio.terminate()

        print("✅ Клиент остановлен")


def main():
    """Главная функция"""
    client = AudioClient()

    try:
        success = client.start()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
