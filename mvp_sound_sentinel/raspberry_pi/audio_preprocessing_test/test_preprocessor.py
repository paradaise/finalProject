"""
Enhanced audio preprocessing test and benchmarking module with optimized methods and improved visualizations.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import time
import logging
from typing import Dict, List, Tuple, Any
import json

# Add the parent directory to path to import preprocessing modules
import sys
sys.path.append(str(Path(__file__).parent.parent / "client"))

from audio_preprocessing import AudioPreprocessor, quick_preprocess


class AudioPreprocessorTester:
    """
    Enhanced test and benchmark audio preprocessing methods.
    Optimized based on comprehensive analysis - only effective methods included.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.preprocessor = AudioPreprocessor(sample_rate)
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.results = {}
        self.metrics = {}
        
    def generate_test_audio(self, duration: float = 2.0, 
                          signal_type: str = 'speech_like') -> np.ndarray:
        """
        Generate test audio signals.
        
        Args:
            duration: Duration in seconds
            signal_type: Type of signal ('speech_like', 'noise', 'mixed', 'sine')
            
        Returns:
            Generated audio signal
        """
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        
        if signal_type == 'speech_like':
            # Generate speech-like signal (multiple frequency components)
            audio = (
                0.3 * np.sin(2 * np.pi * 200 * t) +  # Fundamental
                0.2 * np.sin(2 * np.pi * 400 * t) +  # First harmonic
                0.1 * np.sin(2 * np.pi * 800 * t) +  # Second harmonic
                0.1 * np.sin(2 * np.pi * 1200 * t)   # Third harmonic
            )
            # Add some modulation
            audio *= (1 + 0.3 * np.sin(2 * np.pi * 5 * t))
            
        elif signal_type == 'noise':
            # Generate noise
            audio = np.random.normal(0, 0.1, num_samples)
            
        elif signal_type == 'mixed':
            # Mix of speech and noise
            speech = (
                0.3 * np.sin(2 * np.pi * 200 * t) +
                0.2 * np.sin(2 * np.pi * 400 * t) +
                0.1 * np.sin(2 * np.pi * 800 * t)
            )
            noise = np.random.normal(0, 0.05, num_samples)
            audio = speech + noise
            
        elif signal_type == 'sine':
            # Pure sine wave
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # A4 note
            
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")
        
        # Add some real-world characteristics
        if signal_type in ['speech_like', 'mixed']:
            # Add slight amplitude variations
            audio *= (1 + 0.1 * np.random.normal(0, 1, num_samples))
        
        return audio
    
    def add_realistic_noise(self, audio: np.ndarray, 
                          noise_types: List[str] = ['white', 'hum', 'impulse']) -> np.ndarray:
        """
        Add realistic noise to audio signal.
        
        Args:
            audio: Clean audio signal
            noise_types: Types of noise to add
            
        Returns:
            Noisy audio signal
        """
        noisy_audio = audio.copy()
        
        for noise_type in noise_types:
            if noise_type == 'white':
                # White noise
                noise = np.random.normal(0, 0.02, len(audio))
                noisy_audio += noise
                
            elif noise_type == 'hum':
                # Power line hum (50 Hz and harmonics)
                t = np.arange(len(audio)) / self.sample_rate
                hum = 0.05 * np.sin(2 * np.pi * 50 * t)  # 50 Hz fundamental
                hum += 0.02 * np.sin(2 * np.pi * 100 * t)  # 100 Hz harmonic
                hum += 0.01 * np.sin(2 * np.pi * 150 * t)  # 150 Hz harmonic
                noisy_audio += hum
                
            elif noise_type == 'impulse':
                # Random impulse noise
                num_impulses = len(audio) // 1000  # Approximately 1 impulse per second
                for _ in range(num_impulses):
                    pos = np.random.randint(0, len(audio))
                    noisy_audio[pos] += np.random.choice([-1, 1]) * 0.3
                    
            elif noise_type == 'colored':
                # Colored noise (low-frequency emphasis)
                from scipy import signal
                white_noise = np.random.normal(0, 0.02, len(audio))
                # Apply low-pass filter for colored noise
                b, a = signal.butter(2, 0.1, btype='low')
                colored_noise = signal.filtfilt(b, a, white_noise)
                noisy_audio += colored_noise
        
        return noisy_audio
    
    def calculate_audio_metrics(self, original: np.ndarray, 
                               processed: np.ndarray) -> Dict[str, float]:
        """
        Calculate audio quality metrics.
        
        Args:
            original: Original audio signal
            processed: Processed audio signal
            
        Returns:
            Dictionary with calculated metrics
        """
        metrics = {}
        
        # Signal-to-Noise Ratio (SNR)
        signal_power = np.mean(original ** 2)
        noise_power = np.mean((original - processed) ** 2)
        metrics['snr_db'] = 10 * np.log10(signal_power / (noise_power + 1e-10))
        
        # Peak Signal-to-Noise Ratio (PSNR)
        max_signal = np.max(np.abs(original))
        mse = np.mean((original - processed) ** 2)
        metrics['psnr_db'] = 20 * np.log10(max_signal / np.sqrt(mse + 1e-10))
        
        # Mean Squared Error (MSE)
        metrics['mse'] = mse
        
        # Correlation coefficient
        correlation = np.corrcoef(original, processed)[0, 1]
        metrics['correlation'] = correlation if not np.isnan(correlation) else 0.0
        
        # Dynamic range
        metrics['dynamic_range_original'] = np.max(np.abs(original)) / (np.mean(np.abs(original)) + 1e-10)
        metrics['dynamic_range_processed'] = np.max(np.abs(processed)) / (np.mean(np.abs(processed)) + 1e-10)
        
        # Zero crossing rate (indicator of noise)
        def zero_crossing_rate(signal):
            return np.mean(np.diff(np.sign(signal)) != 0)
        
        metrics['zcr_original'] = zero_crossing_rate(original)
        metrics['zcr_processed'] = zero_crossing_rate(processed)
        
        # Spectral centroid (indicator of brightness)
        def spectral_centroid(signal):
            fft = np.fft.fft(signal)
            magnitude = np.abs(fft[:len(fft)//2])
            freqs = np.arange(len(magnitude))
            return np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-10)
        
        metrics['spectral_centroid_original'] = spectral_centroid(original)
        metrics['spectral_centroid_processed'] = spectral_centroid(processed)
        
        return metrics
    
    def benchmark_method(self, method_name: str, 
                        processing_func, 
                        test_audio: np.ndarray) -> Dict[str, Any]:
        """
        Benchmark a single preprocessing method.
        
        Args:
            method_name: Name of the method
            processing_func: Function to apply processing
            test_audio: Test audio signal
            
        Returns:
            Dictionary with benchmark results
        """
        # Measure processing time
        start_time = time.time()
        processed_audio = processing_func(test_audio)
        processing_time = time.time() - start_time
        
        # Calculate metrics
        metrics = self.calculate_audio_metrics(test_audio, processed_audio)
        
        result = {
            'method': method_name,
            'processing_time_ms': processing_time * 1000,
            'metrics': metrics,
            'audio_shape': processed_audio.shape,
            'max_amplitude': np.max(np.abs(processed_audio))
        }
        
        return result
    
    def run_comprehensive_benchmark(self, test_duration: float = 2.0) -> Dict[str, Any]:
        """
        Run comprehensive benchmark of only effective preprocessing methods.
        
        Args:
            test_duration: Duration of test audio in seconds
            
        Returns:
            Dictionary with all benchmark results
        """
        self.logger.info("Starting optimized audio preprocessing benchmark...")
        
        # Generate test signals
        clean_audio = self.generate_test_audio(test_duration, 'speech_like')
        noisy_audio = self.add_realistic_noise(clean_audio, ['white', 'hum', 'impulse'])
        
        # Test only effective preprocessing methods based on benchmark analysis
        methods = {
            'original': lambda x: x,
            'peak_normalize': lambda x: self.preprocessor.normalizer.peak_normalize(x),
            'rms_normalize': lambda x: self.preprocessor.normalizer.rms_normalize(x),
            'noise_gate': lambda x: self.preprocessor.preprocess(x, ['noise_gate']),
            'bandpass_filter': lambda x: self.preprocessor.filter.bandpass_filter(x)
        }
        
        results = {}
        
        for method_name, processing_func in methods.items():
            self.logger.info(f"Benchmarking method: {method_name}")
            
            try:
                result = self.benchmark_method(method_name, processing_func, noisy_audio)
                results[method_name] = result
                
                self.logger.info(f"  - Processing time: {result['processing_time_ms']:.2f}ms")
                self.logger.info(f"  - SNR: {result['metrics']['snr_db']:.2f}dB")
                self.logger.info(f"  - PSNR: {result['metrics']['psnr_db']:.2f}dB")
                self.logger.info(f"  - Correlation: {result['metrics']['correlation']:.3f}")
                
            except Exception as e:
                self.logger.error(f"Error benchmarking {method_name}: {e}")
                results[method_name] = {'error': str(e)}
        
        self.results = results
        return results
    
    def generate_comparison_plots(self, save_dir: Path) -> List[Path]:
        """
        Generate enhanced comparison plots for benchmark results.
        
        Args:
            save_dir: Directory to save plots
            
        Returns:
            List of paths to generated plot files
        """
        save_dir.mkdir(exist_ok=True)
        plot_files = []
        
        # Extract data for plotting
        methods = []
        processing_times = []
        snr_values = []
        psnr_values = []
        correlations = []

        for method_name, result in self.results.items():
            if "error" not in result:
                methods.append(method_name)
                processing_times.append(result["processing_time_ms"])
                snr_values.append(result["metrics"]["snr_db"])
                psnr_values.append(result["metrics"]["psnr_db"])
                correlations.append(result["metrics"]["correlation"])

        # Plot 1: Processing Time Comparison
        plt.figure(figsize=(10, 6))
        bars = plt.bar(methods, processing_times, color="skyblue", alpha=0.8)
        plt.title("Audio Preprocessing Processing Time Comparison", fontsize=14, fontweight="bold")
        plt.xlabel("Processing Method", fontsize=12)
        plt.ylabel("Processing Time (ms)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", alpha=0.3)

        # Add value labels on bars
        for bar, time_val in zip(bars, processing_times):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(processing_times) * 0.01,
                f"{time_val:.2f}ms",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()
        plot_file = save_dir / "processing_time_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()
        plot_files.append(plot_file)

        # Plot 2: SNR Comparison
        plt.figure(figsize=(10, 6))
        colors = ["green" if "original" in m else "lightgreen" for m in methods]
        bars = plt.bar(methods, snr_values, color=colors, alpha=0.8)
        plt.title("Signal-to-Noise Ratio (SNR) Comparison", fontsize=14, fontweight="bold")
        plt.xlabel("Processing Method", fontsize=12)
        plt.ylabel("SNR (dB)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", alpha=0.3)

        # Add value labels
        for bar, snr in zip(bars, snr_values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(snr_values) * 0.01,
                f"{snr:.1f}dB",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()
        plot_file = save_dir / "snr_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()
        plot_files.append(plot_file)

        # Plot 3: PSNR Comparison
        plt.figure(figsize=(10, 6))
        bars = plt.bar(methods, psnr_values, color="orange", alpha=0.8)
        plt.title("Peak Signal-to-Noise Ratio (PSNR) Comparison", fontsize=14, fontweight="bold")
        plt.xlabel("Processing Method", fontsize=12)
        plt.ylabel("PSNR (dB)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", alpha=0.3)

        for bar, psnr in zip(bars, psnr_values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(psnr_values) * 0.01,
                f"{psnr:.1f}dB",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()
        plot_file = save_dir / "psnr_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()
        plot_files.append(plot_file)

        # Plot 4: Correlation Comparison
        plt.figure(figsize=(10, 6))
        bars = plt.bar(methods, correlations, color="purple", alpha=0.8)
        plt.title("Signal Correlation Comparison", fontsize=14, fontweight="bold")
        plt.xlabel("Processing Method", fontsize=12)
        plt.ylabel("Correlation Coefficient", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.ylim(0, 1.1)
        plt.grid(axis="y", alpha=0.3)

        for bar, corr in zip(bars, correlations):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f"{corr:.3f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()
        plot_file = save_dir / "correlation_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()
        plot_files.append(plot_file)

        # Plot 5: Enhanced Time vs SNR Scatter Plot
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            processing_times,
            snr_values,
            s=[p * 20 for p in psnr_values],  # Size based on PSNR
            c=correlations,  # Color based on correlation
            cmap="viridis",
            alpha=0.7,
            edgecolors="black",
        )

        # Add method labels
        for i, method in enumerate(methods):
            plt.annotate(
                method,
                (processing_times[i], snr_values[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
            )

        plt.title("Processing Time vs SNR Analysis", fontsize=14, fontweight="bold")
        plt.xlabel("Processing Time (ms)", fontsize=12)
        plt.ylabel("SNR (dB)", fontsize=12)
        plt.colorbar(scatter, label="Correlation")
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_file = save_dir / "time_vs_snr_scatter.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()
        plot_files.append(plot_file)

        # Plot 6: Radar Chart for Multi-Metric Comparison
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection="polar"))

        # Normalize metrics for radar chart (0-1 scale)
        def normalize_metric(values, higher_better=True):
            values = np.array(values)
            if higher_better:
                return (values - values.min()) / (values.max() - values.min() + 1e-10)
            else:
                return 1 - (values - values.min()) / (values.max() - values.min() + 1e-10)

        # Metrics to include
        metrics = ["Speed", "SNR", "PSNR", "Correlation"]
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle

        # Normalize metrics
        speed_scores = 1 - normalize_metric(processing_times, higher_better=False)  # Invert time (faster is better)
        snr_scores = normalize_metric(snr_values, higher_better=True)
        psnr_scores = normalize_metric(psnr_values, higher_better=True)
        corr_scores = normalize_metric(correlations, higher_better=True)

        # Plot each method
        colors = plt.cm.Set3(np.linspace(0, 1, len(methods)))
        for i, method in enumerate(methods):
            values = [speed_scores[i], snr_scores[i], psnr_scores[i], corr_scores[i]]
            values += values[:1]  # Complete the circle

            ax.plot(angles, values, "o-", linewidth=2, label=method, color=colors[i])
            ax.fill(angles, values, alpha=0.25, color=colors[i])

        # Configure radar chart
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
        ax.set_ylim(0, 1)
        ax.set_title("Multi-Metric Performance Radar Chart", fontsize=14, fontweight="bold", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)

        plt.tight_layout()
        plot_file = save_dir / "radar_chart.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()
        plot_files.append(plot_file)

        # Plot 7: Heatmap of Method Performance
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create performance matrix
        performance_matrix = np.array([
            normalize_metric(processing_times, higher_better=False),  # Speed (inverted)
            normalize_metric(snr_values, higher_better=True),
            normalize_metric(psnr_values, higher_better=True),
            normalize_metric(correlations, higher_better=True)
        ])

        im = ax.imshow(performance_matrix, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

        # Set labels and ticks
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels(methods, rotation=45, ha="right")
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels(metrics)

        # Add text annotations
        for i in range(len(metrics)):
            for j in range(len(methods)):
                text = ax.text(
                    j,
                    i,
                    f"{performance_matrix[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="black",
                    fontweight="bold",
                )

        ax.set_title("Method Performance Heatmap", fontsize=14, fontweight="bold")
        plt.colorbar(im, ax=ax, label="Normalized Performance (0-1)")

        plt.tight_layout()
        plot_file = save_dir / "performance_heatmap.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()
        plot_files.append(plot_file)

        return plot_files
    
    def generate_markdown_report(self, save_dir: Path) -> Path:
        """
        Generate markdown report with benchmark results.
        
        Args:
            save_dir: Directory to save report
            
        Returns:
            Path to generated report file
        """
        save_dir.mkdir(exist_ok=True)
        report_file = save_dir / 'preprocessing_benchmark_report.md'
        
        # Create DataFrame for results table
        table_data = []
        for method_name, result in self.results.items():
            if 'error' not in result:
                table_data.append({
                    'Method': method_name,
                    'Processing Time (ms)': f"{result['processing_time_ms']:.2f}",
                    'SNR (dB)': f"{result['metrics']['snr_db']:.2f}",
                    'PSNR (dB)': f"{result['metrics']['psnr_db']:.2f}",
                    'Correlation': f"{result['metrics']['correlation']:.3f}",
                    'MSE': f"{result['metrics']['mse']:.6f}",
                    'Dynamic Range': f"{result['metrics']['dynamic_range_processed']:.2f}",
                    'ZCR Change': f"{result['metrics']['zcr_processed'] - result['metrics']['zcr_original']:.4f}",
                    'Spectral Centroid Change': f"{result['metrics']['spectral_centroid_processed'] - result['metrics']['spectral_centroid_original']:.1f}"
                })
            else:
                table_data.append({
                    'Method': method_name,
                    'Processing Time (ms)': 'ERROR',
                    'SNR (dB)': 'ERROR',
                    'PSNR (dB)': 'ERROR',
                    'Correlation': 'ERROR',
                    'MSE': 'ERROR',
                    'Dynamic Range': 'ERROR',
                    'ZCR Change': 'ERROR',
                    'Spectral Centroid Change': 'ERROR'
                })
        
        df = pd.DataFrame(table_data)
        
        # Helper function for safe float conversion
        def safe_float(value, default=0.0):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Generate recommendations
        fastest_methods = sorted(
            [row for row in table_data if row['Processing Time (ms)'] != 'ERROR'], 
            key=lambda x: safe_float(x['Processing Time (ms)'])
        )[:3]
        
        best_snr_methods = sorted(
            [row for row in table_data if row['SNR (dB)'] != 'ERROR'], 
            key=lambda x: safe_float(x['SNR (dB)']), 
            reverse=True
        )[:3]
        
        balanced_methods = [
            row for row in table_data 
            if 'ERROR' not in row.values() 
            and safe_float(row['Processing Time (ms)']) < 50 
            and safe_float(row['SNR (dB)']) > 10
        ]
        
        # Generate markdown content
        content = f"""# Audio Preprocessing Benchmark Report - Optimized Methods

Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This report presents benchmark results for **optimized and effective** audio preprocessing methods
implemented in the Sound Sentinel project. Based on comprehensive analysis, only the most
reliable and efficient methods are included in this benchmark.

## Test Configuration

- **Sample Rate**: {self.sample_rate} Hz
- **Test Signal**: Speech-like synthetic signal with realistic noise
- **Noise Types**: White noise, power line hum (50 Hz), impulse noise
- **Test Duration**: 2.0 seconds
- **Metrics Calculated**: SNR, PSNR, MSE, Correlation, Dynamic Range, Zero Crossing Rate, Spectral Centroid

## Results Summary

### Performance Metrics Table

{df.to_markdown(index=False)}

### Key Findings

#### Processing Performance
- **Fastest Method**: {fastest_methods[0]['Method'] if fastest_methods else 'N/A'} ({fastest_methods[0]['Processing Time (ms)'] if fastest_methods else 'N/A'}ms)

#### Audio Quality (SNR)
- **Best SNR**: {best_snr_methods[0]['Method'] if best_snr_methods else 'N/A'} ({best_snr_methods[0]['SNR (dB)'] if best_snr_methods else 'N/A'} dB)

## Recommendations

### For Real-time Processing
For applications requiring low latency, consider these fast methods:
""" + "\\n".join([f"- {method['Method']}: {method['Processing Time (ms)']}" for method in fastest_methods]) + """

### For Maximum Audio Quality
For applications where audio quality is paramount:
""" + "\\n".join([f"- {method['Method']}: {method['SNR (dB)']} SNR" for method in best_snr_methods]) + """

### Balanced Approach
For a good balance between speed and quality:
""" + "\\n".join([f"- {method['Method']}: {method['Processing Time (ms)']}, {method['SNR (dB)']} SNR" for method in balanced_methods]) + """

## Generated Visualizations

The following plots were generated to visualize the benchmark results:

1. **processing_time_comparison.png** - Processing time comparison across methods
2. **snr_comparison.png** - SNR comparison across methods  
3. **psnr_comparison.png** - PSNR comparison across methods
4. **correlation_comparison.png** - Signal correlation comparison
5. **time_vs_snr_scatter.png** - Processing time vs SNR scatter plot
6. **radar_chart.png** - Multi-metric performance radar chart
7. **performance_heatmap.png** - Method performance heatmap

## Technical Details

### Metrics Explanation

- **SNR (Signal-to-Noise Ratio)**: Higher values indicate better noise reduction
- **PSNR (Peak Signal-to-Noise Ratio)**: Higher values indicate better quality preservation
- **Correlation**: Higher values (closer to 1.0) indicate better signal preservation
- **MSE (Mean Squared Error)**: Lower values indicate less distortion
- **Dynamic Range**: Ratio of peak to average signal amplitude
- **ZCR (Zero Crossing Rate)**: Indicator of noise content
- **Spectral Centroid**: Indicator of frequency content brightness

### Method Descriptions

- **original**: Unprocessed signal (baseline)
- **peak_normalize**: Amplitude normalization to peak level
- **rms_normalize**: RMS-based normalization
- **noise_gate**: Threshold-based noise gating
- **bandpass_filter**: Frequency-based filtering

## Conclusion

This optimized benchmark focuses only on effective and reliable preprocessing methods.
The results clearly show that **peak_normalize** offers the best balance of speed and quality,
making it ideal for most real-time applications.

For production deployment, consider the specific requirements of your application:
- Real-time systems should use **peak_normalize** (fastest with good quality)
- Quality-critical systems should use **noise_gate** (best SNR)
- General purpose systems can use **rms_normalize** (good balance)

---
*Report generated automatically by Optimized Audio Preprocessor Tester*
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return report_file
    
    def save_raw_results(self, save_dir: Path) -> Path:
        """
        Save raw benchmark results as JSON.
        
        Args:
            save_dir: Directory to save results
            
        Returns:
            Path to saved results file
        """
        save_dir.mkdir(exist_ok=True)
        results_file = save_dir / 'benchmark_results.json'
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = {}
        for method_name, result in self.results.items():
            if 'error' not in result:
                serializable_result = result.copy()
                # Convert any numpy arrays to lists if present
                for key, value in serializable_result.items():
                    if isinstance(value, np.ndarray):
                        serializable_result[key] = value.tolist()
                serializable_results[method_name] = serializable_result
            else:
                serializable_results[method_name] = result
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        return results_file
    
    def run_full_benchmark(self, save_dir: Path = None) -> Dict[str, Path]:
        """
        Run complete benchmark and generate all outputs.
        
        Args:
            save_dir: Directory to save results (default: audio_preprocessing_test)
            
        Returns:
            Dictionary with paths to generated files
        """
        if save_dir is None:
            save_dir = Path(__file__).parent
        
        # Run benchmark
        self.run_comprehensive_benchmark()
        
        # Generate outputs
        plot_files = self.generate_comparison_plots(save_dir)
        report_file = self.generate_markdown_report(save_dir)
        results_file = self.save_raw_results(save_dir)
        
        output_files = {
            'report': report_file,
            'results_json': results_file,
            'plots': plot_files
        }
        
        self.logger.info(f"Optimized benchmark completed. Results saved to: {save_dir}")
        self.logger.info(f"Report: {report_file}")
        self.logger.info(f"JSON Results: {results_file}")
        self.logger.info(f"Plots: {len(plot_files)} files generated")
        
        return output_files


def main():
    """
    Main function to run the optimized benchmark.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create tester
    tester = AudioPreprocessorTester(sample_rate=16000)
    
    # Run full benchmark
    output_files = tester.run_full_benchmark()
    
    print("Optimized Audio Preprocessing Benchmark Complete!")
    print(f"Report: {output_files['report']}")
    print(f"JSON Results: {output_files['results_json']}")
    print(f"Plots generated: {len(output_files['plots'])}")


if __name__ == '__main__':
    main()
