"""
Audio filtering module for audio preprocessing.
Implements various digital filters to improve audio quality.
"""

import numpy as np
from scipy import signal
from typing import Tuple


class AudioFiltering:
    """Digital audio filters for noise reduction and enhancement."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
    def highpass_filter(self, audio: np.ndarray, 
                       cutoff_freq: float = 80, 
                       order: int = 4) -> np.ndarray:
        """
        Apply high-pass filter to remove low-frequency noise.
        
        Args:
            audio: Input audio signal
            cutoff_freq: Cutoff frequency in Hz
            order: Filter order
            
        Returns:
            High-pass filtered audio
        """
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        b, a = signal.butter(order, normalized_cutoff, btype='high')
        filtered = signal.filtfilt(b, a, audio)
        
        return filtered
    
    def lowpass_filter(self, audio: np.ndarray, 
                      cutoff_freq: float = 8000, 
                      order: int = 4) -> np.ndarray:
        """
        Apply low-pass filter to remove high-frequency noise.
        
        Args:
            audio: Input audio signal
            cutoff_freq: Cutoff frequency in Hz
            order: Filter order
            
        Returns:
            Low-pass filtered audio
        """
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        b, a = signal.butter(order, normalized_cutoff, btype='low')
        filtered = signal.filtfilt(b, a, audio)
        
        return filtered
    
    def bandpass_filter(self, audio: np.ndarray, 
                        low_freq: float = 300, 
                        high_freq: float = 3400,
                        order: int = 4) -> np.ndarray:
        """
        Apply band-pass filter for speech frequency range.
        
        Args:
            audio: Input audio signal
            low_freq: Low cutoff frequency in Hz
            high_freq: High cutoff frequency in Hz
            order: Filter order
            
        Returns:
            Band-pass filtered audio
        """
        nyquist = self.sample_rate / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        
        b, a = signal.butter(order, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, audio)
        
        return filtered
    
    def notch_filter(self, audio: np.ndarray, 
                    freq: float = 50, 
                    quality_factor: float = 30) -> np.ndarray:
        """
        Apply notch filter to remove specific frequency (e.g., 50/60 Hz hum).
        
        Args:
            audio: Input audio signal
            freq: Frequency to remove in Hz
            quality_factor: Quality factor of the notch
            
        Returns:
            Notch filtered audio
        """
        nyquist = self.sample_rate / 2
        normalized_freq = freq / nyquist
        
        b, a = signal.iirnotch(normalized_freq, quality_factor)
        filtered = signal.filtfilt(b, a, audio)
        
        return filtered
    
    def remove_power_line_noise(self, audio: np.ndarray, 
                               freq: float = 50) -> np.ndarray:
        """
        Remove power line interference (50 Hz or 60 Hz).
        
        Args:
            audio: Input audio signal
            freq: Power line frequency (50 or 60 Hz)
            
        Returns:
            Audio with power line noise removed
        """
        # Remove fundamental frequency
        filtered = self.notch_filter(audio, freq, quality_factor=30)
        
        # Remove harmonics (up to 5th harmonic)
        for harmonic in range(2, 6):
            harmonic_freq = freq * harmonic
            if harmonic_freq < self.sample_rate / 2:
                filtered = self.notch_filter(filtered, harmonic_freq, quality_factor=20)
        
        return filtered
    
    def median_filter(self, audio: np.ndarray, 
                     kernel_size: int = 5) -> np.ndarray:
        """
        Apply median filter to remove impulsive noise.
        
        Args:
            audio: Input audio signal
            kernel_size: Size of the median filter kernel
            
        Returns:
            Median filtered audio
        """
        from scipy.ndimage import median_filter
        
        filtered = median_filter(audio, size=kernel_size)
        return filtered
    
    def wiener_filter(self, audio: np.ndarray, 
                      noise_variance: float = 0.01) -> np.ndarray:
        """
        Apply Wiener filter for noise reduction.
        
        Args:
            audio: Input audio signal
            noise_variance: Estimated noise variance
            
        Returns:
            Wiener filtered audio
        """
        # Simple implementation of Wiener filter in frequency domain
        fft_audio = np.fft.fft(audio)
        power_spectrum = np.abs(fft_audio) ** 2
        
        # Wiener filter transfer function
        wiener_transfer = power_spectrum / (power_spectrum + noise_variance)
        
        # Apply filter
        filtered_fft = fft_audio * wiener_transfer
        filtered_audio = np.real(np.fft.ifft(filtered_fft))
        
        return filtered_audio
    
    def adaptive_filter(self, audio: np.ndarray, 
                       reference_noise: np.ndarray = None,
                       filter_length: int = 32) -> np.ndarray:
        """
        Apply adaptive filter for noise cancellation.
        
        Args:
            audio: Input audio signal
            reference_noise: Reference noise signal (optional)
            filter_length: Length of adaptive filter
            
        Returns:
            Adaptively filtered audio
        """
        if reference_noise is None:
            # Use delayed version of audio as reference (for simple noise reduction)
            delay = filter_length
            if len(audio) > delay:
                reference_noise = np.concatenate([np.zeros(delay), audio[:-delay]])
            else:
                return audio
        
        # Simple LMS adaptive filter
        filtered = np.zeros_like(audio)
        weights = np.zeros(filter_length)
        step_size = 0.01
        
        for i in range(filter_length, len(audio)):
            # Get reference window
            ref_window = reference_noise[i-filter_length:i]
            
            # Calculate filter output
            filter_output = np.dot(weights, ref_window)
            
            # Calculate error
            error = audio[i] - filter_output
            
            # Update weights
            weights += step_size * error * ref_window
            
            # Store filtered result
            filtered[i] = filter_output
        
        # Subtract filtered noise from original
        cleaned = audio - filtered
        
        return cleaned
    
    def comprehensive_filtering(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply comprehensive filtering pipeline.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Comprehensively filtered audio
        """
        # Step 1: Remove power line noise
        filtered = self.remove_power_line_noise(audio)
        
        # Step 2: Apply band-pass filter for speech frequencies
        filtered = self.bandpass_filter(filtered, low_freq=80, high_freq=8000)
        
        # Step 3: Apply median filter for impulsive noise
        filtered = self.median_filter(filtered, kernel_size=3)
        
        # Step 4: Apply Wiener filter for general noise reduction
        filtered = self.wiener_filter(filtered, noise_variance=0.005)
        
        return filtered


def apply_equalizer(audio: np.ndarray, 
                   sample_rate: int = 16000,
                   low_gain: float = 1.2,
                   mid_gain: float = 1.0,
                   high_gain: float = 0.8) -> np.ndarray:
    """
    Apply simple 3-band equalizer.
    
    Args:
        audio: Input audio signal
        sample_rate: Audio sample rate
        low_gain: Low frequency gain (linear)
        mid_gain: Mid frequency gain (linear)
        high_gain: High frequency gain (linear)
        
    Returns:
        Equalized audio signal
    """
    from scipy import signal
    
    # Define frequency bands
    low_cutoff = 300
    high_cutoff = 3000
    
    nyquist = sample_rate / 2
    
    # Low-pass filter for low frequencies
    b_low, a_low = signal.butter(2, low_cutoff / nyquist, btype='low')
    low_freq = signal.filtfilt(b_low, a_low, audio) * low_gain
    
    # Band-pass filter for mid frequencies
    b_mid, a_mid = signal.butter(2, [low_cutoff / nyquist, high_cutoff / nyquist], btype='band')
    mid_freq = signal.filtfilt(b_mid, a_mid, audio) * mid_gain
    
    # High-pass filter for high frequencies
    b_high, a_high = signal.butter(2, high_cutoff / nyquist, btype='high')
    high_freq = signal.filtfilt(b_high, a_high, audio) * high_gain
    
    # Combine bands
    equalized = low_freq + mid_freq + high_freq
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(equalized))
    if max_val > 1.0:
        equalized = equalized / max_val
    
    return equalized
