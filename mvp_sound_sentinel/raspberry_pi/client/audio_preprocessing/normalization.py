"""
Audio normalization module for audio preprocessing.
Implements various normalization techniques to standardize audio levels.
"""

import numpy as np
from typing import Tuple


class AudioNormalization:
    """Audio normalization methods for consistent audio levels."""
    
    def __init__(self, target_level: float = 0.8):
        self.target_level = target_level
        
    def peak_normalize(self, audio: np.ndarray) -> np.ndarray:
        """
        Peak normalization to target level.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Peak-normalized audio signal
        """
        max_val = np.max(np.abs(audio))
        if max_val == 0:
            return audio
            
        scale_factor = self.target_level / max_val
        return audio * scale_factor
    
    def rms_normalize(self, audio: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
        """
        RMS normalization to target RMS level.
        
        Args:
            audio: Input audio signal
            target_rms: Target RMS value
            
        Returns:
            RMS-normalized audio signal
        """
        rms = np.sqrt(np.mean(audio ** 2))
        if rms == 0:
            return audio
            
        scale_factor = target_rms / rms
        normalized = audio * scale_factor
        
        # Clip to prevent distortion
        max_val = np.max(np.abs(normalized))
        if max_val > self.target_level:
            normalized = normalized * (self.target_level / max_val)
            
        return normalized
    
    def lufs_normalize(self, audio: np.ndarray, target_lufs: float = -23.0,
                      sample_rate: int = 16000) -> np.ndarray:
        """
        LUFS loudness normalization (simplified implementation).
        
        Args:
            audio: Input audio signal
            target_lufs: Target LUFS level
            sample_rate: Audio sample rate
            
        Returns:
            LUFS-normalized audio signal
        """
        # Calculate current LUFS (simplified)
        # This is a basic approximation - full LUFS requires more complex filtering
        rms = np.sqrt(np.mean(audio ** 2))
        
        # Convert RMS to LUFS (approximation)
        current_lufs = -0.691 + 10 * np.log10(rms ** 2 + 1e-8)
        
        # Calculate gain needed
        gain_db = target_lufs - current_lufs
        gain_linear = 10 ** (gain_db / 20)
        
        normalized = audio * gain_linear
        
        # Clip to prevent distortion
        max_val = np.max(np.abs(normalized))
        if max_val > self.target_level:
            normalized = normalized * (self.target_level / max_val)
            
        return normalized
    
    def adaptive_normalization(self, audio: np.ndarray, 
                              window_size: int = 1024) -> np.ndarray:
        """
        Adaptive normalization that adjusts to local audio characteristics.
        
        Args:
            audio: Input audio signal
            window_size: Window size for local analysis
            
        Returns:
            Adaptively normalized audio signal
        """
        if len(audio) < window_size:
            return self.peak_normalize(audio)
            
        normalized = np.zeros_like(audio)
        
        for i in range(0, len(audio), window_size // 2):
            end = min(i + window_size, len(audio))
            window = audio[i:end]
            
            if len(window) > 0:
                # Apply peak normalization to window
                window_normalized = self.peak_normalize(window)
                normalized[i:end] = window_normalized
                
        return normalized
    
    def dynamic_range_compression(self, audio: np.ndarray,
                                threshold: float = 0.5,
                                ratio: float = 4.0,
                                attack: float = 0.01,
                                release: float = 0.1,
                                sample_rate: int = 16000) -> np.ndarray:
        """
        Simple dynamic range compression.
        
        Args:
            audio: Input audio signal
            threshold: Compression threshold (0-1)
            ratio: Compression ratio
            attack: Attack time in seconds
            release: Release time in seconds
            sample_rate: Audio sample rate
            
        Returns:
            Compressed audio signal
        """
        audio_abs = np.abs(audio)
        compressed = audio.copy()
        
        attack_coeff = np.exp(-1.0 / (attack * sample_rate))
        release_coeff = np.exp(-1.0 / (release * sample_rate))
        
        gain_reduction = 0.0
        
        for i in range(len(audio)):
            if audio_abs[i] > threshold:
                # Above threshold - apply compression
                target_gain = 1.0 - ((audio_abs[i] - threshold) * (1.0 - 1.0/ratio))
                target_gain = max(target_gain, 1.0/ratio)
            else:
                # Below threshold - no compression
                target_gain = 1.0
                
            # Smooth gain changes
            if target_gain < gain_reduction:
                gain_reduction = gain_reduction * attack_coeff + target_gain * (1 - attack_coeff)
            else:
                gain_reduction = gain_reduction * release_coeff + target_gain * (1 - release_coeff)
                
            compressed[i] *= gain_reduction
            
        return compressed
    
    def comprehensive_normalize(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply comprehensive normalization pipeline.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Normalized audio signal
        """
        # Step 1: Remove DC offset
        audio_dc_removed = audio - np.mean(audio)
        
        # Step 2: Apply dynamic range compression
        compressed = self.dynamic_range_compression(audio_dc_removed)
        
        # Step 3: RMS normalization
        normalized = self.rms_normalize(compressed)
        
        return normalized
