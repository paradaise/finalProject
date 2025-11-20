# receiver_pc_final.py
import sys
import io

# Исправляем кодировку для Windows консоли
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import socket
import json
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import time
from collections import defaultdict

# Настройки
UDP_IP = "0.0.0.0"
UDP_PORT = 5228
BUFFER_SIZE = 65536


class AudioDetector:
    def __init__(self):
        print("Загрузка модели YAMNet...")
        try:
            # Загружаем модель
            self.model = hub.load("https://tfhub.dev/google/yamnet/1")

            # Получаем путь к файлу с классами
            class_map_path = self.model.class_map_path().numpy().decode("utf-8")

            # Загружаем и парсим названия классов
            self.class_names = self._load_class_names(class_map_path)
            print(f"Модель загружена, {len(self.class_names)} классов")

        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            raise

    def _load_class_names(self, class_map_path):
        """Загружает названия классов из файла"""
        class_names = {}
        try:
            # Читаем файл как текст
            with open(class_map_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    try:
                        class_id = int(parts[0])
                        class_name = parts[2].strip('" ')
                        class_names[class_id] = class_name
                    except (ValueError, IndexError):
                        continue

        except Exception as e:
            print(f"Ошибка загрузки названий классов: {e}")
            # Создаем fallback названия
            for i in range(521):
                class_names[i] = f"Class_{i}"

        return class_names

    def detect_sounds(self, audio_data, sample_rate=16000):
        try:
            # Проверяем длину аудио
            if len(audio_data) < sample_rate * 0.5:
                return []

            # Детекция
            scores, embeddings, spectrogram = self.model(audio_data)
            scores = scores.numpy()

            # Топ-3 предсказания
            mean_scores = np.mean(scores, axis=0)
            top_classes = np.argsort(mean_scores)[-3:][::-1]

            results = []
            for class_id in top_classes:
                if class_id in self.class_names:
                    confidence = mean_scores[class_id]
                    sound_name = self.class_names[class_id]

                    # Фильтруем только с достаточной уверенностью
                    if confidence > 0.1:
                        results.append(
                            {
                                "sound": sound_name,
                                "confidence": float(confidence),
                                "class_id": int(class_id),
                            }
                        )

            return results

        except Exception as e:
            print(f"Ошибка детекции: {e}")
            return []


class AudioReceiver:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((UDP_IP, UDP_PORT))
        print(f"Сокет привязан к порту {UDP_PORT}")

        self.detector = AudioDetector()
        self.segment_buffers = defaultdict(list)
        self.segment_count = 0

    def start_receiver(self):
        print(f"Ожидание аудио на порту {UDP_PORT}...")
        print("Готов к детекции звуков!")
        print(
            "Система мониторит: речь, музыка, стекло, сигнализации, бытовые звуки и др."
        )

        while True:
            try:
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                self.process_packet(data, addr)

            except KeyboardInterrupt:
                print("\nОстановка приемника...")
                break
            except Exception as e:
                print(f"Ошибка приема: {e}")

    def process_packet(self, data, addr):
        try:
            packet = json.loads(data.decode("utf-8"))

            segment_id = packet["segment_id"]
            packet_id = packet["packet_id"]
            total_packets = packet["total_packets"]
            audio_list = packet["audio"]

            # Конвертируем в numpy array
            audio_data = np.array(audio_list, dtype=np.float32)
            self.segment_buffers[segment_id].append((packet_id, audio_data))

            # Проверяем, собрали ли все пакеты
            current_packets = len(self.segment_buffers[segment_id])

            if current_packets == total_packets:
                print(
                    f"✅ Сегмент {segment_id} собран! ({current_packets}/{total_packets} пакетов)"
                )
                self.segment_count += 1

                # Собираем полное аудио
                sorted_packets = sorted(
                    self.segment_buffers[segment_id], key=lambda x: x[0]
                )
                full_audio = np.concatenate([packet[1] for packet in sorted_packets])

                print(
                    f"Анализ аудио: {len(full_audio)} samples ({len(full_audio)/16000:.1f} сек)"
                )

                # Детекция
                results = self.detector.detect_sounds(full_audio)

                # Вывод результатов
                if results:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"\n🎵 [{timestamp}] ОБНАРУЖЕНЫ ЗВУКИ:")
                    for result in results:
                        stars = "★" * min(int(result["confidence"] * 10), 5)
                        print(
                            f"   🔊 {result['sound']}: {result['confidence']:.1%} {stars}"
                        )
                    print("")  # пустая строка для разделения
                else:
                    print(f"Фоновый шум (сегмент {self.segment_count})")

                # Очистка буфера
                del self.segment_buffers[segment_id]
            else:
                # Показываем прогресс каждый 10-й пакет
                if current_packets % 10 == 0:
                    print(f"Сегмент {segment_id}: {current_packets}/{total_packets}")

        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON: {e}")
        except KeyError as e:
            print(f"Отсутствует ключ в пакете: {e}")
        except Exception as e:
            print(f"Ошибка обработки пакета: {e}")


if __name__ == "__main__":
    print("Запуск приемника аудио...")
    receiver = AudioReceiver()
    receiver.start_receiver()
