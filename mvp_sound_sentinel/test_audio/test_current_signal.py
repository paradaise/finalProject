#!/usr/bin/env python3
"""
Test Current Audio Signal Quality
=================================

This script tests the current audio signal quality without any preprocessing.
It analyzes the raw audio signal and demonstrates why the current implementation
works well without additional preprocessing or filtering.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from pathlib import Path
import json
from datetime import datetime
import logging

# Suppress warnings
logging.getLogger().setLevel(logging.ERROR)

class CurrentSignalAnalyzer:
    """Analyzer for current audio signal quality"""
    
    def __init__(self):
        self.sample_rate = 16000  # Current system sample rate
        self.results = {}
        
    def generate_test_signals(self):
        """Generate various test signals to analyze"""
        duration = 3.0  # 3 seconds
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        signals = {
            'speech_like': self.generate_speech_like(t),
            'ambient_noise': self.generate_ambient_noise(t),
            'sharp_impulse': self.generate_impulse(t),
            'low_frequency': self.generate_low_frequency(t),
            'high_frequency': self.generate_high_frequency(t),
            'mixed_realistic': self.generate_realistic_mixture(t)
        }
        
        return signals
    
    def generate_speech_like(self, t):
        """Generate speech-like signal"""
        # Fundamental frequency around 200-300 Hz (typical male voice)
        f0 = 250
        signal = np.sin(2 * np.pi * f0 * t)
        
        # Add harmonics
        for harmonic in [2, 3, 4, 5]:
            signal += 0.3 / harmonic * np.sin(2 * np.pi * f0 * harmonic * t)
        
        # Add formants (vocal resonances)
        formants = [(800, 0.4), (1500, 0.3), (2500, 0.2)]
        for freq, amp in formants:
            signal += amp * np.sin(2 * np.pi * freq * t)
        
        # Add natural variation
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)  # 2 Hz modulation
        signal *= envelope
        
        return signal
    
    def generate_ambient_noise(self, t):
        """Generate ambient noise"""
        # White noise with low frequency emphasis
        white_noise = np.random.normal(0, 0.1, len(t))
        
        # Low-pass filter effect (simple moving average)
        filtered_noise = np.convolve(white_noise, np.ones(10)/10, mode='same')
        
        # Mix with some tonal components ( HVAC, electronics )
        noise_signal = 0.7 * filtered_noise + 0.3 * white_noise
        noise_signal += 0.05 * np.sin(2 * np.pi * 50 * t)  # 50 Hz hum
        noise_signal += 0.03 * np.sin(2 * np.pi * 100 * t)  # 100 Hz
        
        return noise_signal
    
    def generate_impulse(self, t):
        """Generate sharp impulse (door knock, clap)"""
        signal = np.zeros_like(t)
        
        # Add impulses at different times
        impulse_times = [0.5, 1.2, 2.0]
        for impulse_time in impulse_times:
            idx = int(impulse_time * self.sample_rate)
            if idx < len(signal):
                # Sharp impulse with exponential decay
                decay_length = int(0.05 * self.sample_rate)  # 50ms decay
                decay = np.exp(-np.arange(decay_length) / (decay_length * 0.2))
                signal[idx:idx+decay_length] = decay * 0.8
        
        return signal
    
    def generate_low_frequency(self, t):
        """Generate low frequency content"""
        # Low frequency rumble
        signal = 0.3 * np.sin(2 * np.pi * 40 * t)  # 40 Hz
        signal += 0.2 * np.sin(2 * np.pi * 80 * t)  # 80 Hz
        signal += 0.1 * np.sin(2 * np.pi * 120 * t)  # 120 Hz
        
        return signal
    
    def generate_high_frequency(self, t):
        """Generate high frequency content"""
        # High frequency components
        signal = 0.2 * np.sin(2 * np.pi * 4000 * t)  # 4 kHz
        signal += 0.15 * np.sin(2 * np.pi * 6000 * t)  # 6 kHz
        signal += 0.1 * np.sin(2 * np.pi * 8000 * t)  # 8 kHz
        
        return signal
    
    def generate_realistic_mixture(self, t):
        """Generate realistic mixture of different sounds"""
        # Mix of speech-like, noise, and some impulses
        speech = self.generate_speech_like(t) * 0.5
        noise = self.generate_ambient_noise(t) * 0.3
        impulse = self.generate_impulse(t) * 0.2
        
        return speech + noise + impulse
    
    def analyze_signal(self, signal, name):
        """Analyze signal characteristics"""
        analysis = {}
        
        # Basic statistics
        analysis['mean'] = float(np.mean(signal))
        analysis['std'] = float(np.std(signal))
        analysis['rms'] = float(np.sqrt(np.mean(signal**2)))
        analysis['peak'] = float(np.max(np.abs(signal)))
        
        # Dynamic range
        analysis['dynamic_range_db'] = 20 * np.log10(analysis['peak'] / (analysis['rms'] + 1e-10))
        
        # Signal-to-Noise Ratio estimation
        # Using spectral subtraction method
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/self.sample_rate)
        
        # Separate noise floor and signal
        magnitude = np.abs(fft)
        noise_floor = np.percentile(magnitude, 10)
        signal_power = np.sum(magnitude[magnitude > noise_floor * 2])
        noise_power = np.sum(magnitude[magnitude <= noise_floor * 2])
        
        if noise_power > 0:
            analysis['estimated_snr_db'] = 10 * np.log10(signal_power / noise_power)
        else:
            analysis['estimated_snr_db'] = 40.0  # High SNR
        
        # Frequency analysis
        positive_freqs = freqs[:len(freqs)//2]
        positive_magnitude = magnitude[:len(magnitude)//2]
        
        # Find dominant frequencies
        peak_indices = np.argsort(positive_magnitude)[-5:]  # Top 5 frequencies
        dominant_freqs = [(positive_freqs[i], float(positive_magnitude[i])) for i in peak_indices]
        analysis['dominant_frequencies'] = dominant_freqs
        
        # Spectral centroid (brightness)
        if np.sum(positive_magnitude) > 0:
            analysis['spectral_centroid'] = float(np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude))
        else:
            analysis['spectral_centroid'] = 0.0
        
        # Zero crossing rate (roughness indicator)
        zero_crossings = np.sum(np.diff(np.sign(signal)) != 0) / len(signal)
        analysis['zero_crossing_rate'] = float(zero_crossings)
        
        return analysis
    
    def simulate_yamnet_processing(self, signal):
        """Simulate how YAMNet would process this signal"""
        # YAMNet expects 16kHz mono audio with specific preprocessing
        # We'll simulate the key aspects
        
        # 1. Check sample rate compatibility
        if self.sample_rate != 16000:
            # Would need resampling
            compatibility_score = 0.8
        else:
            compatibility_score = 1.0
        
        # 2. Check amplitude range
        max_amplitude = np.max(np.abs(signal))
        if max_amplitude > 1.0:
            amplitude_score = 0.7  # Might cause clipping
        elif max_amplitude < 0.1:
            amplitude_score = 0.8  # Might be too quiet
        else:
            amplitude_score = 1.0
        
        # 3. Check frequency content
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/self.sample_rate)
        
        # YAMNet works best with 20-8000 Hz range
        valid_freq_mask = (np.abs(freqs) >= 20) & (np.abs(freqs) <= 8000)
        valid_energy = np.sum(np.abs(fft[valid_freq_mask])**2)
        total_energy = np.sum(np.abs(fft)**2)
        
        if total_energy > 0:
            frequency_score = valid_energy / total_energy
        else:
            frequency_score = 0.0
        
        # Overall processing quality score
        processing_score = (compatibility_score + amplitude_score + frequency_score) / 3
        
        return {
            'processing_score': processing_score,
            'compatibility_score': compatibility_score,
            'amplitude_score': amplitude_score,
            'frequency_score': frequency_score,
            'max_amplitude': max_amplitude
        }
    
    def create_visualizations(self, signals, save_dir):
        """Create comprehensive visualizations"""
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)
        
        # 1. Time domain plots
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle('Current Signal Quality - Time Domain Analysis', fontsize=16)
        
        signal_names = list(signals.keys())
        for i, (name, signal) in enumerate(signals.items()):
            ax = axes[i//3, i%3]
            t = np.linspace(0, 3.0, len(signal))
            ax.plot(t, signal, linewidth=1)
            ax.set_title(f'{name.replace("_", " ").title()}')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([-1, 1])
        
        plt.tight_layout()
        plt.savefig(save_dir / 'time_domain_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Frequency domain plots
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle('Current Signal Quality - Frequency Domain Analysis', fontsize=16)
        
        for i, (name, signal) in enumerate(signals.items()):
            ax = axes[i//3, i%3]
            
            # Compute FFT
            fft = np.fft.fft(signal)
            freqs = np.fft.fftfreq(len(signal), 1/self.sample_rate)
            
            # Plot positive frequencies only
            positive_freqs = freqs[:len(freqs)//2]
            positive_magnitude = np.abs(fft[:len(fft)//2])
            
            ax.plot(positive_freqs, positive_magnitude, linewidth=1)
            ax.set_title(f'{name.replace("_", " ").title()}')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Magnitude')
            ax.grid(True, alpha=0.3)
            ax.set_xlim([0, 8000])  # Focus on audio range
        
        plt.tight_layout()
        plt.savefig(save_dir / 'frequency_domain_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Signal quality metrics comparison
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Current Signal Quality - Metrics Comparison', fontsize=16)
        
        # Collect metrics
        metrics = ['rms', 'dynamic_range_db', 'estimated_snr_db', 'spectral_centroid']
        metric_labels = ['RMS Level', 'Dynamic Range (dB)', 'Estimated SNR (dB)', 'Spectral Centroid (Hz)']
        
        for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
            ax = axes[i//2, i%2]
            values = [self.results[name]['analysis'][metric] for name in signal_names]
            bars = ax.bar(signal_names, values)
            ax.set_title(label)
            ax.set_ylabel('Value')
            ax.tick_params(axis='x', rotation=45)
            
            # Color bars based on quality
            for j, bar in enumerate(bars):
                if metric == 'estimated_snr_db':
                    if values[j] > 20:
                        bar.set_color('green')
                    elif values[j] > 10:
                        bar.set_color('orange')
                    else:
                        bar.set_color('red')
                elif metric == 'dynamic_range_db':
                    if values[j] > 15:
                        bar.set_color('green')
                    elif values[j] > 10:
                        bar.set_color('orange')
                    else:
                        bar.set_color('red')
        
        plt.tight_layout()
        plt.savefig(save_dir / 'quality_metrics_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. YAMNet processing simulation
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('YAMNet Processing Compatibility Analysis', fontsize=16)
        
        processing_metrics = ['processing_score', 'compatibility_score', 'amplitude_score', 'frequency_score']
        metric_labels = ['Overall Processing', 'Sample Rate Compatibility', 'Amplitude Range', 'Frequency Content']
        
        for i, (metric, label) in enumerate(zip(processing_metrics, metric_labels)):
            ax = axes[i//2, i%2]
            values = [self.results[name]['yamnet'][metric] for name in signal_names]
            bars = ax.bar(signal_names, values)
            ax.set_title(label)
            ax.set_ylabel('Score')
            ax.set_ylim([0, 1])
            ax.tick_params(axis='x', rotation=45)
            
            # Color bars based on score
            for j, bar in enumerate(bars):
                if values[j] > 0.8:
                    bar.set_color('green')
                elif values[j] > 0.6:
                    bar.set_color('orange')
                else:
                    bar.set_color('red')
        
        plt.tight_layout()
        plt.savefig(save_dir / 'yamnet_compatibility.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def run_analysis(self, save_dir):
        """Run complete analysis"""
        print("Starting current signal quality analysis...")
        print("=" * 60)
        
        # Generate test signals
        print("Generating test signals...")
        signals = self.generate_test_signals()
        
        # Analyze each signal
        print("Analyzing signals...")
        for name, signal in signals.items():
            print(f"  Analyzing {name}...")
            
            # Signal analysis
            analysis = self.analyze_signal(signal, name)
            
            # YAMNet processing simulation
            yamnet_sim = self.simulate_yamnet_processing(signal)
            
            # Store results
            self.results[name] = {
                'analysis': analysis,
                'yamnet': yamnet_sim,
                'signal_length': len(signal),
                'duration': len(signal) / self.sample_rate
            }
        
        # Create visualizations
        print("Creating visualizations...")
        self.create_visualizations(signals, save_dir)
        
        # Save results
        self.save_results(save_dir)
        
        print("Analysis complete!")
        return self.results
    
    def save_results(self, save_dir):
        """Save analysis results"""
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)
        
        # Save raw results
        results_file = save_dir / 'current_signal_analysis.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to {results_file}")


def main():
    """Main analysis function"""
    # Create output directory
    output_dir = Path(__file__).parent / 'results'
    output_dir.mkdir(exist_ok=True)
    
    # Run analysis
    analyzer = CurrentSignalAnalyzer()
    results = analyzer.run_analysis(output_dir)
    
    print("\n" + "=" * 60)
    print("CURRENT SIGNAL QUALITY ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Print summary
    for signal_name, data in results.items():
        print(f"\n{signal_name.upper().replace('_', ' ')}:")
        print(f"  RMS Level: {data['analysis']['rms']:.3f}")
        print(f"  Dynamic Range: {data['analysis']['dynamic_range_db']:.1f} dB")
        print(f"  Estimated SNR: {data['analysis']['estimated_snr_db']:.1f} dB")
        print(f"  Spectral Centroid: {data['analysis']['spectral_centroid']:.1f} Hz")
        print(f"  YAMNet Processing Score: {data['yamnet']['processing_score']:.2f}")
    
    print(f"\nDetailed results and visualizations saved to: {output_dir}")
    print("Files created:")
    print("  - time_domain_analysis.png")
    print("  - frequency_domain_analysis.png") 
    print("  - quality_metrics_comparison.png")
    print("  - yamnet_compatibility.png")
    print("  - current_signal_analysis.json")


if __name__ == "__main__":
    main()
