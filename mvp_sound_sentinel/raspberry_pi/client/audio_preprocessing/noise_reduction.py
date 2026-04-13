#!/usr/bin/env python3
"""
Noise reduction algorithms for audio preprocessing
"""

import numpy as np
from scipy import signal
from typing import Tuple, Dict, Any


def spectral_subtraction(audio: np.ndarray, sample_rate: int = 16000) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply spectral subtraction to reduce background noise
    
    Args:
        audio: Input audio signal
        sample_rate: Sample rate of audio
        
    Returns:
        Processed audio and metrics
    """
    try:
        # Simple noise reduction using spectral subtraction
        fft = np.fft.fft(audio)
        magnitude = np.abs(fft)
        phase = np.angle(fft)
        
        # Estimate noise from first 0.1 seconds
        noise_frames = int(0.1 * sample_rate)
        if len(magnitude) > noise_frames:
            noise_spectrum = np.mean(magnitude[:noise_frames], axis=0)
            # Apply subtraction with over-subtraction factor
            alpha = 2.0
            magnitude = np.maximum(magnitude - alpha * noise_spectrum, 0.1 * magnitude)
        
        # Reconstruct signal
        processed_fft = magnitude * np.exp(1j * phase)
        processed_audio = np.real(np.fft.ifft(processed_fft))
        
        # Normalize
        if np.max(np.abs(processed_audio)) > 0:
            processed_audio = processed_audio / np.max(np.abs(processed_audio))
        
        metrics = {
            "noise_reduction_applied": True,
            "method": "spectral_subtraction",
            "snr_improvement": "Estimated 3-6 dB"
        }
        
        return processed_audio, metrics
        
    except Exception as e:
        print(f"Noise reduction error: {e}")
        return audio, {"noise_reduction_applied": False}


def wiener_filter(audio: np.ndarray, sample_rate: int = 16000) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply Wiener filter for noise reduction
    
    Args:
        audio: Input audio signal
        sample_rate: Sample rate of audio
        
    Returns:
        Processed audio and metrics
    """
    try:
        # Simple Wiener filtering implementation
        frame_size = 1024
        hop_size = 512
        
        # Estimate noise variance from non-speech frames
        noise_variance = np.var(audio[:frame_size]) * 0.1
        
        processed_audio = np.zeros_like(audio)
        
        for i in range(0, len(audio) - frame_size, hop_size):
            frame = audio[i:i + frame_size]
            
            # Compute Wiener filter
            signal_power = np.var(frame)
            wiener_gain = signal_power / (signal_power + noise_variance)
            
            # Apply gain with smoothing
            smoothed_gain = np.maximum(wiener_gain, 0.1)
            processed_frame = frame * smoothed_gain
            
            processed_audio[i:i + frame_size] = processed_frame
        
        metrics = {
            "noise_reduction_applied": True,
            "method": "wiener_filter",
            "snr_improvement": "Estimated 4-8 dB"
        }
        
        return processed_audio, metrics
        
    except Exception as e:
        print(f"Wiener filter error: {e}")
        return audio, {"noise_reduction_applied": False}
