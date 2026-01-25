#!/bin/bash
# Скрипт для исправления проблем с аудио на Raspberry Pi

echo "🛑 Останавливаю аудио сервисы..."

# Останавливаем PulseAudio если он запущен
sudo systemctl stop pulseaudio
sudo systemctl disable pulseaudio

# Убиваем все процессы использующие аудио
sudo pkill -f pulseaudio
sudo pkill -f jackd
sudo pkill -f arecord

# Перезагружаем ALSA
sudo alsa force-reload

echo "✅ Аудио сервисы остановлены"
echo "🎤 Теперь можно запустить audio_client.py"
