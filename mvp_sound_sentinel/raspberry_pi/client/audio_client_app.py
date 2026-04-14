#!/usr/bin/env python3
"""
Sound Sentinel MVP - Raspberry Pi Audio Client (Modular)

This module contains the full client logic, while `raspberry_pi/audio_client.py`
acts as the entrypoint wrapper.
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
import warnings
import logging
from datetime import datetime
from contextlib import contextmanager

from config import (
    API_SERVER_URL,
    DEVICE_NAME,
    SAMPLE_RATE,
    CHANNELS,
    LEVEL_UPDATE_INTERVAL,
    DETECTION_INTERVAL,
    CHUNK_DURATION,
    CHUNK_SIZE,
    DEVICE_INFO_UPDATE_INTERVAL,
    WIFI_SIGNAL_UPDATE_INTERVAL,
    DETECTION_CONFIDENCE_THRESHOLD,
)

import alsa_suppress as _alsa_suppress
import audio_math as _audio_math
import audio_enhancement as _audio_enhancement
import device_info as _device_info

# Импортируем предобработку аудио
sys.path.append(os.path.join(os.path.dirname(__file__), "audio_preprocessing"))
from audio_preprocessing import AudioPreprocessor


# Подавляем ALSA и PortAudio ошибки
os.environ["ALSA_PCM_CARD"] = "0"
os.environ["ALSA_PCM_DEVICE"] = "0"
os.environ["ALSA_LIB_EXTRA_VERBOSITY"] = "0"
os.environ["ALSA_DEBUG_LEVEL"] = "0"
os.environ["PYTHONWARNINGS"] = "ignore"

# Подавляем предупреждения
logging.getLogger().setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

FORMAT = pyaudio.paFloat32


class AudioClient:
    def __init__(self):
        self.device_id = None
        self.is_running = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.fallback_sample_rate = None
        self.audio_enhancer = _audio_enhancement.AudioEnhancer(sample_rate=SAMPLE_RATE)
        self.enhancement_stats = {
            "processed_chunks": 0,
            "improvements_sum": 0,
            "last_improvement": 0,
        }

        # Инициализация предобработчика аудио
        self.audio_preprocessor = AudioPreprocessor(SAMPLE_RATE)
        print("🎛️ Аудиопредобработчик инициализирован: peak_normalize")

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
        return _device_info.collect_device_info(DEVICE_NAME)

    def get_real_ip_address(self):
        """Получение реального IP адреса, а не 127.0.0.1"""
        return _device_info.get_real_ip_address()

    def get_raspberry_pi_model(self):
        """Определение модели Raspberry Pi и получение URL изображения"""
        return _device_info.get_raspberry_pi_model()

    def get_model_image_url(self, model_name: str) -> str:
        """Получение URL изображения для модели Raspberry Pi"""
        return _device_info.get_model_image_url(model_name)

    def get_microphone_info(self):
        """Получение информации о микрофоне"""
        return _device_info.get_microphone_info()

    def get_wifi_signal(self):
        """Получение уровня WiFi сигнала в процентах"""
        return _device_info.get_wifi_signal()

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
        """Инициализация аудио потока"""
        try:
            with _alsa_suppress.suppress_alsa_errors():
                self.audio = pyaudio.PyAudio()

            print("🎤 Поиск и проверка доступных аудио устройств...")
            supported_devices = []

            device_count = self.audio.get_device_count()
            for i in range(device_count):
                with _alsa_suppress.suppress_alsa_errors():
                    try:
                        info = self.audio.get_device_info_by_index(i)
                        if info["maxInputChannels"] > 0:
                            is_supported = self.audio.is_format_supported(
                                SAMPLE_RATE,
                                input_device_index=i,
                                input_channels=CHANNELS,
                                input_format=FORMAT,
                            )
                            if is_supported:
                                supported_devices.append(i)
                                print(
                                    f"  [✅] Устройство {i}: {info['name']} (поддерживает {SAMPLE_RATE} Hz)"
                                )
                            else:
                                print(
                                    f"  [❌] Устройство {i}: {info['name']} (не поддерживает {SAMPLE_RATE} Hz)"
                                )
                    except Exception:
                        print(f"  [⚠️] Не удалось проверить устройство {i}")

            if not supported_devices:
                print("❌ Ни одно устройство не поддерживает 16000 Hz!")
                print("🔄 Пробуем стандартную частоту 44100 Hz...")
                return self.init_audio_fallback()

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
        return _audio_math.resample_audio(audio_data, original_rate, target_rate)

    def calculate_db(self, audio_data):
        """Расчет уровня звука в дБ (RMS)"""
        return _audio_math.calculate_db(audio_data)

    def send_audio_chunk(self, audio_data):
        """Отправка аудио чанка на детекцию"""
        try:
            if not self.device_id:
                return

            # Применяем peak_normalize предобработку
            processed_audio = self.audio_preprocessor.normalizer.peak_normalize(
                audio_data
            )

            db_level = self.calculate_db(processed_audio)
            normalized_db = db_level + 100

            payload = {
                "device_id": self.device_id,
                "audio_data": processed_audio.tolist(),
                "sample_rate": SAMPLE_RATE,
                "db_level": normalized_db,
            }

            response = self.session.post(
                f"{API_SERVER_URL}/detect_sound",
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                sound_type = result["sound_type"]
                confidence = result["confidence"]

                if confidence > DETECTION_CONFIDENCE_THRESHOLD:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"🎵 [{timestamp}] {sound_type}: {confidence:.1%}")
            else:
                print(f"❌ Ошибка детекции: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"⏰ Таймаут отправки аудио, пробую еще раз...")
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
                    if confidence > DETECTION_CONFIDENCE_THRESHOLD:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"🎵 [{timestamp}] {sound_type}: {confidence:.1%}")
            except:
                print(f"❌ Повторная попытка не удалась")
        except Exception as e:
            if "timed out" in str(e).lower():
                print(f"⏰ Ошибка таймаута отправки аудио")
            else:
                print(f"❌ Ошибка отправки аудио: {e}")

    def send_audio_level(self, normalized_db):
        """Отправка только уровня звука"""
        try:
            payload = {
                "device_id": self.device_id,
                "db_level": normalized_db,
                "timestamp": datetime.now().isoformat(),
            }
            self.session.post(
                f"{API_SERVER_URL}/update_audio_level",
                json=payload,
                timeout=2,
            )
        except Exception:
            pass

    def restart_audio_stream(self):
        """Перезапуск аудио потока при ошибках"""
        try:
            print("🔄 Перезапуск аудио потока...")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()

            return self.init_audio()
        except Exception as e:
            print(f"❌ Ошибка перезапуска аудио: {e}")
            return False

    def update_device_info(self):
        """Обновление информации об устройстве (WiFi сигнал и т.д.)"""
        try:
            device_info = self.get_device_info()
            if device_info and self.device_id:
                payload = {
                    "device_id": self.device_id,
                    "wifi_signal": device_info["wifi_signal"],
                    "cpu_usage": device_info["cpu_usage"],
                    "device_temperature": device_info["device_temperature"],
                    "microphone_info": device_info["microphone_info"],
                    "last_seen": datetime.now().isoformat(),
                }

                response = self.session.put(
                    f"{API_SERVER_URL}/update_device/{self.device_id}",
                    json=payload,
                    timeout=5,
                )

                if response.status_code == 200:
                    print(
                        f"📶 WiFi: {device_info['wifi_signal']}% | 🖥️ CPU: {device_info['cpu_usage']}% | 🌡️ Temp: {device_info['device_temperature']}°C"
                    )
                else:
                    print(f"❌ Ошибка обновления WiFi: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка обновления информации об устройстве: {e}")

    def update_wifi_signal(self):
        """Separate update of WiFi signal, CPU and temperature."""
        try:
            if not self.device_id:
                return

            device_info = self.get_device_info()
            payload = {
                "device_id": self.device_id,
                "wifi_signal": device_info["wifi_signal"],
                "cpu_usage": device_info["cpu_usage"],
                "device_temperature": device_info["device_temperature"],
                "last_seen": datetime.now().isoformat(),
            }

            response = self.session.put(
                f"{API_SERVER_URL}/update_device/{self.device_id}",
                json=payload,
                timeout=5,
            )

            if response.status_code == 200:
                print(
                    f"PUT success: WiFi {device_info['wifi_signal']}% | CPU {device_info['cpu_usage']}% | Temp {device_info['device_temperature']}°C"
                )
        except Exception as e:
            print(f"PUT request failed: {e}")

    def audio_loop(self):
        """Основной цикл записи и отправки аудио"""
        print(
            f"🎙️ Начинаю мониторинг (дБ каждые {LEVEL_UPDATE_INTERVAL}s, детекция каждые {DETECTION_INTERVAL}s)..."
        )

        audio_buffer = []
        seconds_passed = 0
        last_device_info_update = 0.0
        last_wifi_update = 0.0

        try:
            while self.is_running:
                import time

                if hasattr(self, "fallback_sample_rate"):
                    chunk_size = int(self.fallback_sample_rate * LEVEL_UPDATE_INTERVAL)
                else:
                    chunk_size = CHUNK_SIZE

                try:
                    raw_data = self.stream.read(chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(raw_data, dtype=np.float32)
                except Exception as e:
                    print(f"❌ Ошибка чтения аудио: {e}")
                    if not self.restart_audio_stream():
                        break
                    continue

                if hasattr(self, "fallback_sample_rate"):
                    audio_data = self.resample_audio(
                        audio_data, self.fallback_sample_rate, SAMPLE_RATE
                    )

                # Send dB every second
                db_level = self.calculate_db(audio_data)
                normalized_db = db_level + 100
                self.send_audio_level(normalized_db)

                # Buffer for detections
                audio_buffer.append(audio_data)
                seconds_passed += LEVEL_UPDATE_INTERVAL

                if seconds_passed >= DETECTION_INTERVAL:
                    full_audio_to_detect = np.concatenate(audio_buffer)
                    self.send_audio_chunk(full_audio_to_detect)
                    audio_buffer = []
                    seconds_passed = 0

                now = time.monotonic()

                # Initial tick: set reference times so updates happen after full intervals.
                if last_device_info_update == 0.0:
                    last_device_info_update = now
                    last_wifi_update = now

                # Update full device info (wifi + mic) on DEVICE_INFO_UPDATE_INTERVAL
                if now - last_device_info_update >= DEVICE_INFO_UPDATE_INTERVAL:
                    self.update_device_info()
                    last_device_info_update = now
                # Update WiFi only on WIFI_SIGNAL_UPDATE_INTERVAL (independent of device info)
                if now - last_wifi_update >= WIFI_SIGNAL_UPDATE_INTERVAL:
                    self.update_wifi_signal()
                    last_wifi_update = now

        except Exception as e:
            print(f"❌ Ошибка в аудио цикле: {e}")

    def start(self):
        """Запуск клиента"""
        print("🚀 Запуск Sound Sentinel Audio Client...")

        if not self.register_device():
            print("❌ Не удалось зарегистрировать устройство!")
            return

        if not self.init_audio():
            print("❌ Не удалось инициализировать аудио!")
            return

        self.is_running = True

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


@contextmanager
def suppress_alsa_errors():
    """Suppress ALSA stderr messages via stderr redirection."""
    original_stderr_fd = sys.stderr.fileno()
    saved_stderr_fd = os.dup(original_stderr_fd)
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, original_stderr_fd)
        yield
    finally:
        os.dup2(saved_stderr_fd, original_stderr_fd)
        os.close(saved_stderr_fd)


def main():
    client = AudioClient()
    try:
        client.start()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
