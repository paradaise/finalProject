#!/bin/bash
# Sound Sentinel Audio Client - Simple Launch Script

# Подавляем ALSA ошибки
export ALSA_PCM_CARD=0
export ALSA_PCM_DEVICE=0
export ALSA_LIB_EXTRA_VERBOSITY=0
export ALSA_DEBUG_LEVEL=0
export PYTHONWARNINGS="ignore"

# Перенаправляем stderr в /dev/null
exec 2>/dev/null

cd "$(dirname "$0")"
python3 audio_client_fixed.py
