#!/usr/bin/env python3
"""
Audio normalization algorithms for audio preprocessing
"""

import numpy as np
from typing import Tuple, Dict, Any


def normalize_rms(audio: np.ndarray, target_rms: float = 0.3) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Normalize audio to target RMS level
    
    Args:
        audio: Input audio signal
        target_rms: Target RMS level (default 0.3)
        
    Returns:
        Normalized audio and metrics
    """
    try:
        # Calculate current RMS
        current_rms = np.sqrt(np.mean(audio ** 2))
        
        # Avoid division by zero
        if current_rms < 1e-6:
            return audio, {"normalization_applied": False}
        
        # Calculate gain factor
        gain = target_rms / current_rms
        
        # Apply gain with limiting to prevent clipping
        max_gain = 10.0
        limited_gain = np.minimum(gain, max_gain)
        
        normalized_audio = audio * limited_gain
        
        # Check for clipping
        clipped_samples = np.sum(np.abs(normalized_audio) > 1.0)
        clipping_ratio = clipped_samples / len(normalized_audio)
        
        # Apply soft clipping if necessary
        if clipping_ratio > 0.01:
            normalized_audio = np.tanh(normalized_audio * 0.95)
        
        metrics = {
            "normalization_applied": True,
            "method": "rms_normalization",
            "original_rms": float(current_rms),
            "normalized_rms": float(np.sqrt(np.mean(normalized_audio ** 2))),
            "gain_applied": float(limited_gain),
            "clipping_ratio": float(clipping_ratio),
            "clipping_detected": clipping_ratio > 0.01
        }
        
        return normalized_audio, metrics
        
    except Exception as e:
        print(f"Normalization error: {e}")
        return audio, {"normalization_applied": False}


def peak_normalize(audio: np.ndarray, target_peak: float = 0.95) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Peak normalize audio to target peak level
    
    Args:
        audio: Input audio signal
        target_peak: Target peak level (default 0.95)
        
    Returns:
        Peak normalized audio and metrics
    """
    try:
        # Find current peak
        current_peak = np.max(np.abs(audio))
        
        # Avoid division by zero
        if current_peak < 1e-6:
            return audio, {"normalization_applied": False}
        
        # Calculate normalization factor
        norm_factor = target_peak / current_peak
        
        # Apply normalization
        normalized_audio = audio * norm_factor
        
        metrics = {
            "normalization_applied": True,
            "method": "peak_normalization",
            "original_peak": float(current_peak),
            "normalized_peak": float(np.max(np.abs(normalized_audio))),
            "normalization_factor": float(norm_factor)
        }
        
        return normalized_audio, metrics
        
    except Exception as e:
        print(f"Peak normalization error: {e}")
        return audio, {"normalization_applied": False}
