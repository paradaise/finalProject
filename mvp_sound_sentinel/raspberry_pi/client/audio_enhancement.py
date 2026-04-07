#!/usr/bin/env python3
"""
Audio Enhancement Module
Improves audio quality before sending to server
"""

import numpy as np
from scipy import signal
from typing import Tuple, Dict, Any
import json

class AudioEnhancer:
    """Enhances audio quality for better sound detection"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.noise_threshold = 0.02  # Adaptive noise threshold
        self.target_level = 0.5      # Target RMS level
        
    def apply_filters(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply bandpass filter to reduce noise"""
        try:
            # Bandpass filter: 80Hz - 8000Hz (human speech range)
            nyquist = self.sample_rate / 2
            low = 80 / nyquist
            high = 8000 / nyquist
            
            # Butterworth filter for smooth response
            b, a = signal.butter(4, [low, high], btype='band')
            filtered = signal.filtfilt(b, a, audio_data)
            
            return filtered
        except Exception as e:
            print(f"Filter error: {e}")
            return audio_data
    
    def reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Simple noise reduction using spectral gating"""
        try:
            # Estimate noise from first 0.5 seconds
            noise_samples = int(0.5 * self.sample_rate)
            if len(audio_data) > noise_samples:
                noise_floor = np.std(audio_data[:noise_samples])
            else:
                noise_floor = np.std(audio_data)
            
            # Adaptive threshold
            threshold = max(noise_floor * 2, self.noise_threshold)
            
            # Soft gating
            mask = np.abs(audio_data) > threshold
            enhanced = audio_data * mask
            
            return enhanced
        except Exception as e:
            print(f"Noise reduction error: {e}")
            return audio_data
    
    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to target level"""
        try:
            # Calculate current RMS
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms > 0:
                # Calculate gain factor
                gain = self.target_level / rms
                # Limit gain to avoid amplifying noise too much
                gain = min(gain, 10.0)  # Max 20dB boost
                return audio_data * gain
            return audio_data
        except Exception as e:
            print(f"Normalization error: {e}")
            return audio_data
    
    def apply_compression(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply dynamic range compression"""
        try:
            # Simple soft knee compression
            threshold = 0.7
            ratio = 4.0
            
            compressed = np.copy(audio_data)
            
            # Apply compression to values above threshold
            mask = np.abs(audio_data) > threshold
            if np.any(mask):
                excess = np.abs(audio_data[mask]) - threshold
                compressed[mask] = np.sign(audio_data[mask]) * (threshold + excess / ratio)
            
            return compressed
        except Exception as e:
            print(f"Compression error: {e}")
            return audio_data
    
    def detect_clipping(self, audio_data: np.ndarray) -> Tuple[bool, float]:
        """Detect audio clipping"""
        try:
            # Count samples near maximum
            max_val = np.max(np.abs(audio_data))
            clipping_threshold = 0.99
            
            clipped_samples = np.sum(np.abs(audio_data) > clipping_threshold)
            clipping_ratio = clipped_samples / len(audio_data)
            
            is_clipped = clipping_ratio > 0.001  # 0.1% samples clipped
            
            return is_clipped, clipping_ratio
        except:
            return False, 0.0
    
    def calculate_snr(self, audio_data: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio"""
        try:
            # Estimate signal and noise
            signal_power = np.mean(audio_data ** 2)
            
            # Use high-frequency content as noise estimate
            fft = np.fft.fft(audio_data)
            freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
            
            # High frequencies (>10kHz) as noise
            noise_mask = np.abs(freqs) > 10000
            noise_power = np.mean(np.abs(fft[noise_mask]) ** 2)
            
            if noise_power > 0:
                snr_db = 10 * np.log10(signal_power / noise_power)
                return max(0, min(100, snr_db))  # Clamp to 0-100 dB
            return 50.0  # Default good SNR
        except:
            return 50.0
    
    def enhance_audio(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply all enhancements and return metrics"""
        try:
            # Store original for comparison
            original = audio_data.copy()
            
            # Apply enhancements in order
            enhanced = self.apply_filters(audio_data)
            enhanced = self.reduce_noise(enhanced)
            enhanced = self.normalize_audio(enhanced)
            enhanced = self.apply_compression(enhanced)
            
            # Calculate quality metrics
            metrics = {
                'original_rms': float(np.sqrt(np.mean(original ** 2))),
                'enhanced_rms': float(np.sqrt(np.mean(enhanced ** 2))),
                'original_peak': float(np.max(np.abs(original))),
                'enhanced_peak': float(np.max(np.abs(enhanced))),
                'clipping_detected': self.detect_clipping(enhanced)[0],
                'clipping_ratio': float(self.detect_clipping(enhanced)[1]),
                'snr_db': float(self.calculate_snr(enhanced)),
                'enhancement_applied': True
            }
            
            return enhanced, metrics
            
        except Exception as e:
            print(f"Enhancement error: {e}")
            return audio_data, {'enhancement_applied': False}
    
    def get_enhancement_summary(self, original_metrics: Dict, enhanced_metrics: Dict) -> Dict[str, Any]:
        """Generate summary of improvements"""
        try:
            improvements = {}
            
            if 'original_rms' in original_metrics and 'enhanced_rms' in enhanced_metrics:
                rms_improvement = (enhanced_metrics['enhanced_rms'] / original_metrics['original_rms'] - 1) * 100
                improvements['rms_improvement_percent'] = rms_improvement
            
            if 'snr_db' in enhanced_metrics:
                improvements['final_snr_db'] = enhanced_metrics['snr_db']
                improvements['signal_quality'] = self._classify_signal_quality(enhanced_metrics['snr_db'])
            
            if 'clipping_ratio' in enhanced_metrics:
                improvements['clipping_status'] = 'Good' if enhanced_metrics['clipping_ratio'] < 0.001 else 'Detected'
            
            improvements['overall_improvement'] = self._calculate_overall_improvement(original_metrics, enhanced_metrics)
            
            return improvements
            
        except Exception as e:
            print(f"Summary error: {e}")
            return {'overall_improvement': 0}
    
    def _classify_signal_quality(self, snr_db: float) -> str:
        """Classify signal quality based on SNR"""
        if snr_db >= 30:
            return "Excellent"
        elif snr_db >= 20:
            return "Good"
        elif snr_db >= 10:
            return "Fair"
        else:
            return "Poor"
    
    def _calculate_overall_improvement(self, original: Dict, enhanced: Dict) -> float:
        """Calculate overall improvement score (0-100)"""
        try:
            score = 50  # Base score
            
            # SNR improvement
            if 'snr_db' in enhanced:
                snr_score = min(30, enhanced['snr_db'] / 40 * 30)  # Max 30 points
                score += snr_score
            
            # Clipping penalty
            if enhanced.get('clipping_ratio', 0) > 0.001:
                score -= 20
            
            # Normalization bonus
            if 'enhanced_rms' in enhanced and 0.1 < enhanced['enhanced_rms'] < 0.8:
                score += 20
            
            return max(0, min(100, score))
            
        except:
            return 50

# Test functions
def test_audio_enhancement():
    """Test audio enhancement with sample data"""
    print("Testing Audio Enhancement...")
    
    enhancer = AudioEnhancer()
    
    # Generate test audio with noise
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Clean signal (440 Hz tone)
    clean_signal = 0.3 * np.sin(2 * np.pi * 440 * t)
    
    # Add noise
    noise = 0.1 * np.random.randn(len(t))
    noisy_signal = clean_signal + noise
    
    # Add some clipping
    noisy_signal[1000:1050] = 0.99
    noisy_signal[2000:2050] = -0.99
    
    # Process audio
    enhanced, metrics = enhancer.enhance_audio(noisy_signal)
    
    # Calculate original metrics
    original_metrics = {
        'original_rms': float(np.sqrt(np.mean(noisy_signal ** 2))),
        'enhanced_rms': float(np.sqrt(np.mean(enhanced ** 2))),
        'clipping_ratio': float(np.sum(np.abs(noisy_signal) > 0.99) / len(noisy_signal)),
        'snr_db': enhancer.calculate_snr(noisy_signal)
    }
    
    # Get improvement summary
    improvements = enhancer.get_enhancement_summary(original_metrics, metrics)
    
    print("\n=== Audio Enhancement Test Results ===")
    print(f"Original RMS: {original_metrics['original_rms']:.3f}")
    print(f"Enhanced RMS: {metrics['enhanced_rms']:.3f}")
    print(f"Original Clipping: {original_metrics['clipping_ratio']*100:.2f}%")
    print(f"Enhanced Clipping: {metrics['clipping_ratio']*100:.2f}%")
    print(f"Original SNR: {original_metrics['snr_db']:.1f} dB")
    print(f"Enhanced SNR: {metrics['snr_db']:.1f} dB")
    print(f"Signal Quality: {improvements.get('signal_quality', 'Unknown')}")
    print(f"Overall Improvement: {improvements.get('overall_improvement', 0):.1f}/100")
    
    return improvements

if __name__ == "__main__":
    test_audio_enhancement()
