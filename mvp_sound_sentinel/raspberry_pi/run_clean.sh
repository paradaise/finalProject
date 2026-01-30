#!/bin/bash
# Sound Sentinel Audio Client - Clean Launch Script

# Подавляем все ALSA и PortAudio ошибки
export ALSA_PCM_CARD=0
export ALSA_PCM_DEVICE=0
export ALSA_LIB_EXTRA_VERBOSITY=0
export ALSA_DEBUG_LEVEL=0
export PYTHONWARNINGS="ignore"

# Перенаправляем stderr в /dev/null для подавления ошибок
python3 audio_client_fixed.py 2>/dev/null
