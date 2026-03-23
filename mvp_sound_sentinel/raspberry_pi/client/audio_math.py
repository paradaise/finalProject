from __future__ import annotations

from typing import Any

import numpy as np


def resample_audio(audio_data: Any, original_rate: int, target_rate: int):
    """Resample audio to target_rate.

    Uses simple linear interpolation (no librosa dependency).
    """
    try:
        ratio = target_rate / original_rate
        new_length = int(len(audio_data) * ratio)
        return np.interp(
            np.linspace(0, len(audio_data), new_length),
            np.arange(len(audio_data)),
            audio_data,
        )
    except Exception as e:
        print(f"❌ Ошибка ресемплинга: {e}")
        return audio_data


def calculate_db(audio_data) -> float:
    """Calculate sound level in dB (RMS)."""
    try:
        rms = np.sqrt(np.mean(np.square(audio_data)))
        if rms > 0:
            db = 20 * np.log10(rms)
            return float(max(-100, min(0, db)))
        return -100.0
    except Exception as e:
        print(f"❌ Ошибка расчета дБ: {e}")
        return -100.0
