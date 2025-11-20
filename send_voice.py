# send_voice_fixed.py
import pyaudio
import socket
import time
import json
import numpy as np

# Настройки
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
SEGMENT_DURATION = 2  # секунды
SAMPLES_PER_SEGMENT = RATE * SEGMENT_DURATION

PC_IP = "192.168.0.61"
PC_PORT = 5228


class AudioSender:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_SNDBUF, 8192
        )  # Уменьшаем буфер

    def start_stream(self):
        print("Запуск аудио потока...")
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=0,
            frames_per_buffer=CHUNK,
        )

    def resample_audio(self, audio_array, original_rate, target_rate):
        """Ресемплинг до целевой частоты"""
        if original_rate == target_rate:
            return audio_array

        ratio = original_rate / target_rate
        new_length = int(len(audio_array) / ratio)
        indices = (np.arange(new_length) * ratio).astype(np.int32)
        indices = np.clip(indices, 0, len(audio_array) - 1)
        return audio_array[indices]

    def capture_and_send(self):
        print(f"Отправка на {PC_IP}:{PC_PORT}")
        segment_count = 0

        while True:
            try:
                segment = []
                samples_collected = 0

                # Захват сегмента
                while samples_collected < SAMPLES_PER_SEGMENT:
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    segment.append(data)
                    samples_collected += CHUNK

                # Подготовка данных
                audio_data = b"".join(segment)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Ресемплинг до 16kHz для модели
                audio_16k = self.resample_audio(audio_array, RATE, 16000)

                # Нормализация
                audio_float = audio_16k.astype(np.float32) / 32768.0

                # Разбиваем на маленькие пакеты по 256 сэмплов
                packet_size = 256
                num_packets = len(audio_float) // packet_size

                print(
                    f"Сегмент {segment_count}: {len(audio_float)} samples -> {num_packets} пакетов"
                )

                for i in range(num_packets):
                    start_idx = i * packet_size
                    end_idx = start_idx + packet_size
                    packet_audio = audio_float[start_idx:end_idx]

                    # Создаем пакет
                    packet = {
                        "segment_id": segment_count,
                        "packet_id": i,
                        "total_packets": num_packets,
                        "audio": packet_audio.tolist(),
                        "sample_rate": 16000,
                        "timestamp": time.time(),
                    }

                    # Отправляем пакет
                    json_data = json.dumps(packet).encode("utf-8")

                    # Проверяем размер пакета
                    if len(json_data) > 1400:  # MTU размер
                        print(f"Предупреждение: пакет большой {len(json_data)} байт")

                    self.socket.sendto(json_data, (PC_IP, PC_PORT))

                    # Небольшая задержка между пакетами
                    time.sleep(0.001)

                print(f"✅ Сегмент {segment_count} отправлен")
                segment_count += 1

            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(1)

    def start(self):
        self.start_stream()
        self.capture_and_send()

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()


if __name__ == "__main__":
    sender = AudioSender()
    try:
        sender.start()
    except KeyboardInterrupt:
        print("Остановка")
        sender.stop()
