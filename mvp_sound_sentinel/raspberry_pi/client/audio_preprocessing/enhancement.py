"""
Audio enhancement module for audio preprocessing.
Implements various enhancement techniques to improve audio clarity.
"""

import numpy as np
from scipy import signal
from scipy.fft import fft, ifft
from typing import Tuple


class AudioEnhancement:
    """Audio enhancement methods for improved clarity and quality."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
    def spectral_enhancement(self, audio: np.ndarray, 
                           enhancement_factor: float = 1.5) -> np.ndarray:
        """
        Enhance audio using spectral modification.
        
        Args:
            audio: Input audio signal
            enhancement_factor: Factor to enhance spectral components
            
        Returns:
            Spectrally enhanced audio
        """
        # Apply window and FFT
        windowed = audio * np.hanning(len(audio))
        fft_audio = fft(windowed)
        
        # Get magnitude and phase
        magnitude = np.abs(fft_audio)
        phase = np.angle(fft_audio)
        
        # Apply enhancement to magnitude spectrum
        # Enhance mid-range frequencies more than extremes
        freq_bins = len(magnitude)
        freqs = np.linspace(0, self.sample_rate/2, freq_bins//2)
        
        enhancement_curve = np.ones(freq_bins)
        
        # Create enhancement curve that boosts speech frequencies
        for i, freq in enumerate(freqs):
            if 300 <= freq <= 3400:  # Speech range
                enhancement_curve[i] = enhancement_factor
            elif 80 <= freq < 300 or 3400 < freq <= 8000:  # Adjacent ranges
                enhancement_curve[i] = 1.2
            else:  # Other frequencies
                enhancement_curve[i] = 0.8
                
        # Apply enhancement symmetrically for negative frequencies
        enhancement_curve[freq_bins//2:] = enhancement_curve[:freq_bins//2][::-1]
        
        # Apply enhancement
        enhanced_magnitude = magnitude * enhancement_curve
        
        # Reconstruct signal
        enhanced_fft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = np.real(ifft(enhanced_fft))
        
        # Remove window effect
        enhanced_audio = enhanced_audio / np.hanning(len(audio))
        
        return enhanced_audio
    
    def dynamic_range_expansion(self, audio: np.ndarray,
                               expansion_ratio: float = 2.0,
                               threshold: float = 0.3) -> np.ndarray:
        """
        Apply dynamic range expansion to increase contrast.
        
        Args:
            audio: Input audio signal
            expansion_ratio: Expansion ratio
            threshold: Expansion threshold
            
        Returns:
            Dynamically expanded audio
        """
        audio_abs = np.abs(audio)
        expanded = audio.copy()
        
        for i in range(len(audio)):
            if audio_abs[i] > threshold:
                # Expand signals above threshold
                expansion_factor = 1.0 + (audio_abs[i] - threshold) * (expansion_ratio - 1.0)
                expanded[i] *= expansion_factor
                
        # Normalize to prevent clipping
        max_val = np.max(np.abs(expanded))
        if max_val > 1.0:
            expanded = expanded / max_val
            
        return expanded
    
    def harmonic_enhancement(self, audio: np.ndarray,
                           harmonic_strength: float = 0.3) -> np.ndarray:
        """
        Enhance harmonic content to improve speech intelligibility.
        
        Args:
            audio: Input audio signal
            harmonic_strength: Strength of harmonic enhancement
            
        Returns:
            Harmonically enhanced audio
        """
        # Generate harmonics
        enhanced = audio.copy()
        
        # Add second harmonic (octave)
        second_harmonic = audio * harmonic_strength
        enhanced += second_harmonic
        
        # Add subtle third harmonic for warmth
        third_harmonic = audio * harmonic_strength * 0.5
        enhanced += third_harmonic
        
        # Normalize
        max_val = np.max(np.abs(enhanced))
        if max_val > 1.0:
            enhanced = enhanced / max_val
            
        return enhanced
    
    def temporal_enhancement(self, audio: np.ndarray,
                           attack_boost: float = 1.2,
                           release_boost: float = 0.8) -> np.ndarray:
        """
        Apply temporal enhancement to improve transient response.
        
        Args:
            audio: Input audio signal
            attack_boost: Boost factor for attack transients
            release_boost: Boost factor for release transients
            
        Returns:
            Temporally enhanced audio
        """
        # Calculate derivative to find transients
        derivative = np.diff(audio, prepend=audio[0])
        
        # Identify attack and release transients
        attack_mask = derivative > 0
        release_mask = derivative < 0
        
        # Apply enhancement
        enhanced = audio.copy()
        
        # Boost attacks
        enhanced[1:][attack_mask] *= attack_boost
        
        # Adjust releases
        enhanced[1:][release_mask] *= release_boost
        
        # Normalize
        max_val = np.max(np.abs(enhanced))
        if max_val > 1.0:
            enhanced = enhanced / max_val
            
        return enhanced
    
    def noise_shaping(self, audio: np.ndarray,
                     shaping_factor: float = 0.1) -> np.ndarray:
        """
        Apply noise shaping to move quantization noise to less audible frequencies.
        
        Args:
            audio: Input audio signal
            shaping_factor: Strength of noise shaping
            
        Returns:
            Noise shaped audio
        """
        # Simple high-pass filter for noise shaping
        nyquist = self.sample_rate / 2
        cutoff = 1000 / nyquist  # Shape noise above 1kHz
        
        b, a = signal.butter(1, cutoff, btype='high')
        
        # Calculate error signal
        quantized = np.round(audio * 32767) / 32767  # Simulate 16-bit quantization
        error = quantized - audio
        
        # Shape error signal
        shaped_error = signal.filtfilt(b, a, error)
        
        # Apply shaped error
        shaped_audio = audio + shaped_error * shaping_factor
        
        return shaped_audio
    
    def de_reverberation(self, audio: np.ndarray,
                        decay_factor: float = 0.7) -> np.ndarray:
        """
        Apply simple de-reverberation to reduce echo effects.
        
        Args:
            audio: Input audio signal
            decay_factor: Reverberation decay factor
            
        Returns:
            De-reverberated audio
        """
        # Simple inverse filtering approach
        # Estimate room impulse response (simplified)
        impulse_length = int(0.1 * self.sample_rate)  # 100ms impulse
        impulse = np.zeros(impulse_length)
        impulse[0] = 1.0  # Direct sound
        
        # Add simulated early reflections
        for i in range(1, min(10, impulse_length)):
            delay_samples = int(i * 0.03 * self.sample_rate)  # 30ms intervals
            if delay_samples < impulse_length:
                impulse[delay_samples] = decay_factor ** i
        
        # Deconvolution (simplified)
        fft_impulse = fft(impulse, len(audio))
        fft_audio = fft(audio)
        
        # Inverse filter
        epsilon = 1e-8  # Prevent division by zero
        inverse_filter = 1.0 / (fft_impulse + epsilon)
        
        # Apply deconvolution
        deconvolved_fft = fft_audio * inverse_filter
        deconvolved = np.real(ifft(deconvolved_fft))
        
        return deconvolved
    
    def speech_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply speech-specific enhancement pipeline.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Speech-enhanced audio
        """
        # Step 1: Spectral enhancement for speech frequencies
        enhanced = self.spectral_enhancement(audio, enhancement_factor=1.3)
        
        # Step 2: Harmonic enhancement for intelligibility
        enhanced = self.harmonic_enhancement(enhanced, harmonic_strength=0.2)
        
        # Step 3: Dynamic range expansion for contrast
        enhanced = self.dynamic_range_expansion(enhanced, expansion_ratio=1.5)
        
        # Step 4: Temporal enhancement for transients
        enhanced = self.temporal_enhancement(enhanced)
        
        return enhanced
    
    def comprehensive_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply comprehensive enhancement pipeline.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Comprehensively enhanced audio
        """
        # Step 1: Spectral enhancement
        enhanced = self.spectral_enhancement(audio)
        
        # Step 2: Speech enhancement
        enhanced = self.speech_enhancement(enhanced)
        
        # Step 3: Noise shaping
        enhanced = self.noise_shaping(enhanced)
        
        return enhanced


def apply_stereo_enhancement(audio: np.ndarray, 
                           stereo_width: float = 1.5) -> np.ndarray:
    """
    Apply stereo width enhancement (for stereo audio).
    
    Args:
        audio: Input stereo audio (2 channels)
        stereo_width: Stereo width enhancement factor
        
    Returns:
        Stereo-enhanced audio
    """
    if audio.ndim != 2 or audio.shape[0] != 2:
        return audio
    
    left, right = audio[0], audio[1]
    
    # Calculate mid and side signals
    mid = (left + right) / 2
    side = (left - right) / 2
    
    # Enhance stereo width
    enhanced_side = side * stereo_width
    
    # Reconstruct left and right channels
    enhanced_left = mid + enhanced_side
    enhanced_right = mid - enhanced_side
    
    # Normalize to prevent clipping
    max_val = max(np.max(np.abs(enhanced_left)), np.max(np.abs(enhanced_right)))
    if max_val > 1.0:
        enhanced_left /= max_val
        enhanced_right /= max_val
    
    return np.array([enhanced_left, enhanced_right])
