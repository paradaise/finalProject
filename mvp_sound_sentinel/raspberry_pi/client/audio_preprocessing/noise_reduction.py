"""
Noise reduction module for audio preprocessing.
Implements various noise reduction techniques to improve sound detection.
"""

import numpy as np
from scipy import signal
from typing import Tuple, Optional


class NoiseReduction:
    """Audio noise reduction using spectral subtraction and filtering."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.noise_profile = None
        
    def estimate_noise_profile(self, audio: np.ndarray, 
                             noise_duration: float = 0.5) -> np.ndarray:
        """
        Estimate noise profile from the beginning of audio.
        
        Args:
            audio: Input audio signal
            noise_duration: Duration in seconds to analyze for noise
            
        Returns:
            Noise spectrum profile
        """
        noise_samples = int(noise_duration * self.sample_rate)
        noise_samples = min(noise_samples, len(audio) // 4)  # Use first 25% max
        
        if noise_samples < 100:
            return np.ones(1024) * 0.01  # Default noise floor
            
        noise_segment = audio[:noise_samples]
        
        # Compute FFT of noise segment
        fft_noise = np.fft.fft(noise_segment, n=1024)
        noise_spectrum = np.abs(fft_noise)
        
        # Smooth the noise spectrum
        self.noise_profile = np.convolve(noise_spectrum, 
                                        np.ones(5)/5, mode='same')
        
        return self.noise_profile
    
    def spectral_subtraction(self, audio: np.ndarray, 
                           alpha: float = 2.0, 
                           beta: float = 0.01) -> np.ndarray:
        """
        Apply spectral subtraction for noise reduction.
        
        Args:
            audio: Input audio signal
            alpha: Over-subtraction factor
            beta: Spectral floor factor
            
        Returns:
            Denoised audio signal
        """
        if self.noise_profile is None:
            self.estimate_noise_profile(audio)
            
        # Frame the audio
        frame_length = 1024
        hop_length = 512
        
        frames = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i + frame_length]
            frames.append(frame)
        
        if not frames:
            return audio
            
        # Process each frame
        processed_frames = []
        for frame in frames:
            # Apply window
            windowed = frame * np.hanning(frame_length)
            
            # FFT
            fft_frame = np.fft.fft(windowed, n=frame_length)
            magnitude = np.abs(fft_frame)
            phase = np.angle(fft_frame)
            
            # Spectral subtraction
            subtracted_magnitude = magnitude - alpha * self.noise_profile[:frame_length]
            
            # Apply spectral floor
            floor = beta * magnitude
            subtracted_magnitude = np.maximum(subtracted_magnitude, floor)
            
            # Reconstruct signal
            reconstructed_fft = subtracted_magnitude * np.exp(1j * phase)
            reconstructed_frame = np.real(np.fft.ifft(reconstructed_fft))
            
            # Apply window again
            reconstructed_frame = reconstructed_frame * np.hanning(frame_length)
            
            processed_frames.append(reconstructed_frame)
        
        # Overlap-add reconstruction
        result_length = len(processed_frames) * hop_length + frame_length
        result = np.zeros(result_length)
        
        for i, frame in enumerate(processed_frames):
            start = i * hop_length
            end = start + frame_length
            result[start:end] += frame
        
        return result[:len(audio)]
    
    def apply_bandpass_filter(self, audio: np.ndarray, 
                            low_freq: float = 80, 
                            high_freq: float = 8000) -> np.ndarray:
        """
        Apply bandpass filter to remove out-of-band noise.
        
        Args:
            audio: Input audio signal
            low_freq: Low cutoff frequency (Hz)
            high_freq: High cutoff frequency (Hz)
            
        Returns:
            Filtered audio signal
        """
        nyquist = self.sample_rate / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        
        # Design Butterworth bandpass filter
        b, a = signal.butter(4, [low, high], btype='band')
        
        # Apply filter
        filtered_audio = signal.filtfilt(b, a, audio)
        
        return filtered_audio
    
    def reduce_background_noise(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply complete noise reduction pipeline.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Denoised audio signal
        """
        # Step 1: Bandpass filtering
        filtered = self.apply_bandpass_filter(audio)
        
        # Step 2: Spectral subtraction
        denoised = self.spectral_subtraction(filtered)
        
        # Step 3: Normalize to prevent clipping
        denoised = denoised / (np.max(np.abs(denoised)) + 1e-8)
        
        return denoised


def apply_noise_gate(audio: np.ndarray, 
                    threshold: float = 0.01, 
                    ratio: float = 10, 
                    attack: float = 0.01, 
                    release: float = 0.1,
                    sample_rate: int = 16000) -> np.ndarray:
    """
    Apply noise gate to suppress low-level noise.
    
    Args:
        audio: Input audio signal
        threshold: Gate threshold (0-1)
        ratio: Reduction ratio when below threshold
        attack: Attack time in seconds
        release: Release time in seconds
        sample_rate: Audio sample rate
        
    Returns:
            Gated audio signal
    """
    audio_abs = np.abs(audio)
    gated_audio = audio.copy()
    
    attack_coeff = np.exp(-1.0 / (attack * sample_rate))
    release_coeff = np.exp(-1.0 / (release * sample_rate))
    
    gain = 1.0
    
    for i in range(len(audio)):
        if audio_abs[i] > threshold:
            # Above threshold - apply attack
            gain = gain * attack_coeff + (1 - attack_coeff)
        else:
            # Below threshold - apply reduction
            target_gain = threshold / (audio_abs[i] + 1e-8) / ratio
            target_gain = min(target_gain, 1.0)
            gain = gain * release_coeff + target_gain * (1 - release_coeff)
        
        gated_audio[i] *= gain
    
    return gated_audio
