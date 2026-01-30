#!/usr/bin/env python3
"""
Sound Sentinel MVP - Raspberry Pi Audio Client (Fixed Version)
Улучшенная версия с лучшей обработкой ошибок и выбором аудио устройств
"""

import os
import sys
import json
import uuid
import socket
import threading
import requests
import pyaudio
import numpy as np
from datetime import datetime

# Подавляем ALSA и PortAudio ошибки
os.environ["ALSA_PCM_CARD"] = "0"
os.environ["ALSA_PCM_DEVICE"] = "0"
os.environ["ALSA_LIB_EXTRA_VERBOSITY"] = "0"
os.environ["ALSA_DEBUG_LEVEL"] = "0"
os.environ["PYTHONWARNINGS"] = "ignore"

# Подавляем предупреждения
import logging

logging.getLogger().setLevel(logging.ERROR)
import warnings

warnings.filterwarnings("ignore")

# Конфигурация
API_SERVER_URL = "https://192.168.0.61:8000"  # IP вашего ПК с API сервером
DEVICE_NAME = "Raspberry Pi Monitor"
SAMPLE_RATE = 16000  # YAMNet ожидает 16kHz
CHANNELS = 1
FORMAT = pyaudio.paFloat32
CHUNK_DURATION = 30  # секунды на один чанк (обновление каждые 30 секунд)
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)


class AudioClient:
    def __init__(self):
        self.device_id = None
        self.is_running = False
        self.audio = None
        self.stream = None

        # Настройки для HTTPS с самоподписанным сертификатом
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.session = requests.Session()
        self.session.verify = False  # Отключаем проверку сертификата
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "SoundSentinel-Pi-Client/1.0",
            }
        )

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
            model_info = self.get_raspberry_pi_model()

            # Получаем информацию о микрофоне
            microphone_info = self.get_microphone_info()

            # Получаем уровень сигнала WiFi
            wifi_signal = self.get_wifi_signal()

            return {
                "name": DEVICE_NAME,
                "ip_address": ip_address,
                "mac_address": mac,
                "model": model_info["name"],
                "model_image_url": model_info["image_url"],
                "microphone_info": microphone_info,
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
        """Определение модели Raspberry Pi и получение URL изображения"""
        try:
            model_name = None

            # Сначала пробуем файл из /sys/firmware/devicetree/base/model
            try:
                with open("/sys/firmware/devicetree/base/model", "r") as f:
                    model_info = f.read().strip()
                    if "Raspberry Pi" in model_info:
                        model_name = model_info
            except:
                pass

            # Fallback к /proc/cpuinfo
            if not model_name:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("Model"):
                            model_info = line.split(":")[1].strip()
                            if "Raspberry Pi" in model_info:
                                model_name = model_info
                                break

            if not model_name:
                return {
                    "name": "Raspberry Pi",
                    "image_url": "/images/raspberry-pi-default.png",
                }

            # Определяем URL изображения на основе модели
            image_url = self.get_model_image_url(model_name)

            return {"name": model_name, "image_url": image_url}
        except:
            return {
                "name": "Raspberry Pi",
                "image_url": "/images/raspberry-pi-default.png",
            }

    def get_model_image_url(self, model_name: str) -> str:
        """Получение URL изображения для модели Raspberry Pi"""
        model_lower = model_name.lower()

        if "zero 2 w" in model_lower:
            return "/images/raspberry-pi-zero-2-w.png"
        elif "zero w" in model_lower:
            return "/images/raspberry-pi-zero-w.png"
        elif "zero" in model_lower:
            return "/images/raspberry-pi-zero.png"
        elif "4" in model_lower:
            if "compute" in model_lower:
                return "/images/raspberry-pi-4-compute.png"
            else:
                return "/images/raspberry-pi-4.png"
        elif "3" in model_lower:
            if "a+" in model_lower:
                return "/images/raspberry-pi-3-a-plus.png"
            elif "b+" in model_lower:
                return "/images/raspberry-pi-3-b-plus.png"
            else:
                return "/images/raspberry-pi-3.png"
        elif "2" in model_lower:
            return "/images/raspberry-pi-2.png"
        elif "1" in model_lower:
            if "b+" in model_lower:
                return "/images/raspberry-pi-1-b-plus.png"
            else:
                return "/images/raspberry-pi-1.png"
        else:
            return "/images/raspberry-pi-default.png"

    def get_microphone_info(self):
        """Получение информации о микрофоне"""
        try:
            # Пробуем получить информацию об аудио устройствах
            import subprocess

            # Для Linux используем arecord или pactl
            try:
                result = subprocess.run(
                    ["arecord", "-l"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "card" in line and "device" in line:
                            # Извлекаем имя устройства
                            parts = line.split(":")
                            if len(parts) >= 2:
                                device_info = parts[1].strip()
                                return device_info
            except:
                pass

            # Fallback - пробуем pactl
            try:
                result = subprocess.run(
                    ["pactl", "list", "sources"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "Description:" in line:
                            return line.split("Description:")[1].strip()
            except:
                pass

            return "Default Microphone"
        except:
            return "Unknown Microphone"

    def get_wifi_signal(self):
        """Получение уровня WiFi сигнала в процентах"""
        try:
            import subprocess

            # Используем nmcli для получения информации о текущем подключении
            result = subprocess.run(
                ["nmcli", "dev", "wifi"], capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    # Ищем строку с * (активное подключение)
                    if line.strip().startswith("*"):
                        # Парсим строку для получения SIGNAL
                        parts = line.split()
                        # nmcli выводит: IN-USE BSSID SSID MODE CHAN RATE SIGNAL BARS SECURITY
                        # SIGNAL обычно на 7-й позиции (индекс 7)
                        if len(parts) > 7:
                            signal_percent = parts[7]
                            try:
                                return int(signal_percent)
                            except:
                                return 50  # Default fallback
                return 50  # Default if no active connection found

            # Fallback - пробуем iwconfig
            try:
                result = subprocess.run(["iwconfig"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "wlan" in line.lower() and "Signal level" in line:
                            # Парсим строку типа "Signal level=-70 dBm"
                            import re

                            match = re.search(r"Signal level=(-?\d+) dBm", line)
                            if match:
                                dbm = int(match.group(1))
                                # Конвертируем dBm в проценты (приблизительно)
                                if dbm <= -100:
                                    return 0
                                elif dbm >= -50:
                                    return 100
                                else:
                                    return 2 * (dbm + 100)
            except:
                pass

            return 50  # Default fallback
        except:
            return 50

    def register_device(self):
        """Регистрация устройства на API сервере"""
        try:
            device_info = self.get_device_info()
            if not device_info:
                return False

            print(f"📡 Регистрация устройства: {device_info['name']}")
            print(f"🖥️ Модель: {device_info['model']}")
            print(f"🎤 Микрофон: {device_info['microphone_info']}")
            print(f"📡 WiFi сигнал: {device_info['wifi_signal']}%")
            print(f"🌐 IP адрес: {device_info['ip_address']}")
            print(f"🔗 MAC адрес: {device_info['mac_address']}")

            response = self.session.post(
                f"{API_SERVER_URL}/register_device",
                json=device_info,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.device_id = data["device_id"]
                print(f"✅ Устройство успешно зарегистрировано! ID: {self.device_id}")
                return True
            else:
                print(
                    f"❌ Ошибка регистрации: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Ошибка регистрации устройства: {e}")
            return False

    def init_audio(self):
        """Инициализация аудио потока с улучшенной обработкой ошибок"""
        try:
            # Устанавливаем переменные окружения для уменьшения ошибок ALSA
            os.environ["ALSA_PCM_CARD"] = "0"
            os.environ["ALSA_PCM_DEVICE"] = "0"
            os.environ["ALSA_LIB_EXTRA_VERBOSITY"] = "0"
            os.environ["ALSA_DEBUG_LEVEL"] = "0"

            self.audio = pyaudio.PyAudio()

            print("🎤 Доступные аудио устройства:")
            supported_devices = []

            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    print(
                        f"  [{i}] {info['name']} (каналов: {info['maxInputChannels']})"
                    )

                    # Проверяем поддерживаемые частоты дискретизации
                    try:
                        test_stream = self.audio.open(
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            input=True,
                            input_device_index=i,
                            frames_per_buffer=1024,
                        )
                        test_stream.close()
                        supported_devices.append(i)
                        print(f"      ✅ Поддерживает {SAMPLE_RATE} Hz")
                    except Exception as e:
                        # Показываем только краткую ошибку
                        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
                        print(f"      ❌ Не поддерживает {SAMPLE_RATE} Hz: {error_msg}")

            if not supported_devices:
                print("❌ Ни одно устройство не поддерживает 16000 Hz!")
                print("🔄 Пробуем стандартную частоту 44100 Hz...")
                return self.init_audio_fallback()

            # Пробуем устройства в порядке приоритета
            device_priority = {}
            for i in supported_devices:
                info = self.audio.get_device_info_by_index(i)
                name_lower = info["name"].lower()

                if "pulse" in name_lower:
                    device_priority[i] = 1
                elif "default" in name_lower:
                    device_priority[i] = 2
                elif "sysdefault" in name_lower:
                    device_priority[i] = 3
                else:
                    device_priority[i] = 4

            # Сортируем по приоритету
            priority_devices = sorted(
                device_priority.keys(), key=lambda x: device_priority[x]
            )

            for device_index in priority_devices:
                try:
                    device_info = self.audio.get_device_info_by_index(device_index)
                    print(f"🎤 Пробую устройство: {device_info['name']}")

                    self.stream = self.audio.open(
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=CHUNK_SIZE,
                    )

                    print(f"✅ Аудио поток инициализирован с {device_info['name']}")
                    return True

                except Exception as e:
                    print(f"❌ Устройство {device_info['name']} недоступно: {e}")
                    continue

            print("❌ Все устройства недоступны!")
            print("🔄 Пробуем запасной вариант...")
            return self.init_audio_fallback()

        except Exception as e:
            print(f"❌ Ошибка инициализации аудио: {e}")
            print("🔄 Пробуем запасной вариант...")
            return self.init_audio_fallback()

    def init_audio_fallback(self):
        """Запасной вариант инициализации аудио"""
        try:
            # Пробуем с частотой 44100 Hz и последующим ресемплингом
            fallback_sample_rate = 44100

            print(f"🔄 Пробую инициализировать с {fallback_sample_rate} Hz...")

            device_index = None
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    device_index = i
                    break

            if device_index is None:
                print("❌ Не найдено аудио устройств!")
                return False

            device_info = self.audio.get_device_info_by_index(device_index)
            print(f"🎤 Используем устройство: {device_info['name']}")

            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=fallback_sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=int(fallback_sample_rate * CHUNK_DURATION),
            )

            self.fallback_sample_rate = fallback_sample_rate
            print(f"✅ Аудио поток инициализирован с {fallback_sample_rate} Hz")
            return True

        except Exception as e:
            print(f"❌ Ошибка запасной инициализации аудио: {e}")
            return False

    def resample_audio(self, audio_data, original_rate, target_rate):
        """Ресемплинг аудио до целевой частоты"""
        try:
            import librosa

            # Используем librosa для ресемплинга
            resampled = librosa.resample(
                audio_data, orig_sr=original_rate, target_sr=target_rate
            )
            return resampled
        except ImportError:
            # Если librosa недоступен, используем простой линейный интерполяции
            ratio = target_rate / original_rate
            new_length = int(len(audio_data) * ratio)
            resampled = np.interp(
                np.linspace(0, len(audio_data), new_length),
                np.arange(len(audio_data)),
                audio_data,
            )
            return resampled
        except Exception as e:
            print(f"❌ Ошибка ресемплинга: {e}")
            return audio_data  # Возвращаем оригинал если не получилось

    def send_audio_chunk(self, audio_data):
        """Отправка аудио чанка на детекцию"""
        try:
            if not self.device_id:
                print("❌ Устройство не зарегистрировано!")
                return

            payload = {
                "device_id": self.device_id,
                "audio_data": audio_data.tolist(),
                "sample_rate": SAMPLE_RATE,
            }

            response = self.session.post(
                f"{API_SERVER_URL}/detect_sound",
                json=payload,
                timeout=30,  # Увеличиваем таймаут
            )

            if response.status_code == 200:
                result = response.json()
                sound_type = result["sound_type"]
                confidence = result["confidence"]

                if confidence > 0.3:  # Порог уверенности
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"🎵 [{timestamp}] {sound_type}: {confidence:.1%}")
            else:
                print(f"❌ Ошибка детекции: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"⏰ Таймаут отправки аудио, пробую еще раз...")
            # Пробуем еще раз с меньшим таймаутом
            try:
                response = self.session.post(
                    f"{API_SERVER_URL}/detect_sound",
                    json=payload,
                    timeout=15,
                )
                if response.status_code == 200:
                    result = response.json()
                    sound_type = result["sound_type"]
                    confidence = result["confidence"]
                    if confidence > 0.3:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"🎵 [{timestamp}] {sound_type}: {confidence:.1%}")
            except:
                print(f"❌ Повторная попытка не удалась")
        except Exception as e:
            if "timed out" in str(e).lower():
                print(f"⏰ Ошибка таймаута отправки аудио")
            else:
                print(f"❌ Ошибка отправки аудио: {e}")

    def audio_loop(self):
        """Основной цикл записи и отправки аудио"""
        print(f"🎙️ Начинаю запись аудио (чанки по {CHUNK_DURATION} сек)...")

        update_counter = 0  # Счетчик для обновления информации об устройстве

        try:
            while self.is_running:
                # Определяем размер чанка в зависимости от частоты
                if hasattr(self, "fallback_sample_rate"):
                    chunk_size = int(self.fallback_sample_rate * CHUNK_DURATION)
                else:
                    chunk_size = CHUNK_SIZE

                # Читаем аудио данные
                try:
                    audio_data = np.frombuffer(
                        self.stream.read(chunk_size, exception_on_overflow=False),
                        dtype=np.float32,
                    )
                except Exception as e:
                    print(f"❌ Ошибка чтения аудио: {e}")
                    # Пробуем перезапустить поток
                    if not self.restart_audio_stream():
                        break
                    continue

                # Ресемплинг если используется другая частота
                if hasattr(self, "fallback_sample_rate"):
                    audio_data = self.resample_audio(
                        audio_data, self.fallback_sample_rate, SAMPLE_RATE
                    )

                # Отправляем на детекцию
                self.send_audio_chunk(audio_data)

                # Обновляем информацию об устройстве каждый чанк (каждые 30 секунд)
                self.update_device_info()

        except Exception as e:
            print(f"❌ Ошибка в аудио цикле: {e}")

    def restart_audio_stream(self):
        """Перезапуск аудио потока при ошибках"""
        try:
            print("🔄 Перезапуск аудио потока...")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()

            # Пробуем инициализировать заново
            return self.init_audio()
        except Exception as e:
            print(f"❌ Ошибка перезапуска аудио: {e}")
            return False

    def update_device_info(self):
        """Обновление информации об устройстве (WiFi сигнал и т.д.)"""
        try:
            device_info = self.get_device_info()
            if device_info and self.device_id:
                # Отправляем обновление через API
                payload = {
                    "device_id": self.device_id,
                    "wifi_signal": device_info["wifi_signal"],
                    "microphone_info": device_info["microphone_info"],
                    "last_seen": datetime.now().isoformat(),
                }

                response = self.session.put(
                    f"{API_SERVER_URL}/update_device/{self.device_id}",
                    json=payload,
                    timeout=5,
                )

                if response.status_code == 200:
                    print(f"📶 WiFi сигнал обновлен: {device_info['wifi_signal']}%")
                else:
                    print(f"❌ Ошибка обновления WiFi: {response.status_code}")

        except Exception as e:
            print(f"❌ Ошибка обновления информации об устройстве: {e}")

    def start(self):
        """Запуск клиента"""
        print("🚀 Запуск Sound Sentinel Audio Client...")

        # Регистрация устройства
        if not self.register_device():
            print("❌ Не удалось зарегистрировать устройство!")
            return

        # Инициализация аудио
        if not self.init_audio():
            print("❌ Не удалось инициализировать аудио!")
            return

        self.is_running = True

        # Запуск аудио цикла в отдельном потоке
        audio_thread = threading.Thread(target=self.audio_loop, daemon=True)
        audio_thread.start()

        print("✅ Клиент запущен! Нажмите Ctrl+C для остановки.")

        try:
            while self.is_running:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Остановка клиента...")
            self.stop()

    def stop(self):
        """Остановка клиента"""
        self.is_running = False

        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass

        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass

        print("✅ Клиент остановлен")


def main():
    client = AudioClient()
    try:
        client.start()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
