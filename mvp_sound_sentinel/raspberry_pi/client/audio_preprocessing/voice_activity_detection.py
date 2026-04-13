#!/usr/bin/env python3
"""
Voice Activity Detection (VAD) for audio preprocessing
"""

import numpy as np
from typing import Tuple, Dict, Any, List

# Try to import webrtcvad, but make it optional
try:
    import webrtcvad

    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    print("Warning: webrtcvad not available, using simple VAD only")


def simple_vad(
    audio: np.ndarray, sample_rate: int = 16000
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Simple energy-based voice activity detection

    Args:
        audio: Input audio signal
        sample_rate: Sample rate of audio

    Returns:
        Processed audio and VAD metrics
    """
    try:
        frame_length = int(0.03 * sample_rate)  # 30ms frames
        hop_length = int(0.01 * sample_rate)  # 10ms hop

        energy_threshold = 0.01
        voiced_frames = []

        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i : i + frame_length]
            energy = np.sum(frame**2)

            # Simple energy-based VAD
            is_voiced = energy > energy_threshold
            voiced_frames.append(is_voiced)

        # Remove unvoiced frames
        voiced_audio = []
        for i, is_voiced in enumerate(voiced_frames):
            if is_voiced:
                start_idx = i * hop_length
                end_idx = min(start_idx + frame_length, len(audio))
                voiced_audio.extend(audio[start_idx:end_idx])

        voiced_audio = np.array(voiced_audio)

        metrics = {
            "vad_applied": True,
            "method": "energy_based",
            "voiced_ratio": np.mean(voiced_frames),
            "frames_processed": len(voiced_frames),
        }

        return voiced_audio, metrics

    except Exception as e:
        print(f"VAD error: {e}")
        return audio, {"vad_applied": False}


def webrtc_vad(
    audio: np.ndarray, sample_rate: int = 16000
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    WebRTC Voice Activity Detection

    Args:
        audio: Input audio signal
        sample_rate: Sample rate of audio

    Returns:
        Processed audio and VAD metrics
    """
    if not WEBRTC_AVAILABLE:
        return audio, {"vad_applied": False, "error": "webrtcvad not available"}

    try:
        # Convert to 16-bit PCM for WebRTC VAD
        audio_int16 = (audio * 32767).astype(np.int16)

        # Initialize VAD
        vad = webrtcvad.Vad(sample_rate, frame_duration=30)

        frame_size = int(sample_rate * 0.03)  # 30ms frames
        voiced_frames = []
        voiced_audio = []

        for i in range(0, len(audio_int16), frame_size):
            frame = audio_int16[i : i + frame_size]

            # Check if frame contains voice
            is_speech = vad.is_speech(frame, sample_rate)
            voiced_frames.append(is_speech)

            if is_speech:
                voiced_audio.extend(audio[i : i + frame_size])

        voiced_audio = np.array(voiced_audio) / 32767.0  # Convert back to float

        metrics = {
            "vad_applied": True,
            "method": "webrtc",
            "voiced_ratio": np.mean(voiced_frames),
            "frames_processed": len(voiced_frames),
        }

        return voiced_audio, metrics

    except Exception as e:
        print(f"WebRTC VAD error: {e}")
        return audio, {"vad_applied": False}
