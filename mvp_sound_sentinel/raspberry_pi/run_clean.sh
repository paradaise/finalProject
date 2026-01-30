#!/bin/bash
# Sound Sentinel Audio Client - Clean Launch Script

# Полное подавление всех ошибок
exec 2>/dev/null
export ALSA_PCM_CARD=0
export ALSA_PCM_DEVICE=0
export ALSA_LIB_EXTRA_VERBOSITY=0
export ALSA_DEBUG_LEVEL=0
export PYTHONWARNINGS="ignore"
export ALSA_CONFIG_PATH="/dev/null"

cd "$(dirname "$0")"
python3 audio_client_fixed.py
