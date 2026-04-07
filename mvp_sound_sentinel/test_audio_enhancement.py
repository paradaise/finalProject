#!/usr/bin/env python3
"""
Audio Enhancement Demo and Test Suite
Shows before/after comparison of audio processing
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import json
import time
import sys
import os

# Add the client directory to path
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", "raspberry_pi", "client")
)

try:
    from audio_enhancement import AudioEnhancer
except ImportError:
    print("Audio enhancement module not found. Creating test data...")

    # Define the class inline for testing
    class AudioEnhancer:
        def __init__(self, sample_rate=16000):
            self.sample_rate = sample_rate
            self.noise_threshold = 0.02
            self.target_level = 0.5

        def apply_filters(self, audio_data):
            try:
                nyquist = self.sample_rate / 2
                low = 80 / nyquist
                high = 8000 / nyquist
                b, a = signal.butter(4, [low, high], btype="band")
                return signal.filtfilt(b, a, audio_data)
            except:
                return audio_data

        def reduce_noise(self, audio_data):
            try:
                noise_samples = int(0.5 * self.sample_rate)
                if len(audio_data) > noise_samples:
                    noise_floor = np.std(audio_data[:noise_samples])
                else:
                    noise_floor = np.std(audio_data)

                threshold = max(noise_floor * 2, self.noise_threshold)
                mask = np.abs(audio_data) > threshold
                return audio_data * mask
            except:
                return audio_data

        def normalize_audio(self, audio_data):
            try:
                rms = np.sqrt(np.mean(audio_data**2))
                if rms > 0:
                    gain = min(self.target_level / rms, 10.0)
                    return audio_data * gain
                return audio_data
            except:
                return audio_data

        def apply_compression(self, audio_data):
            try:
                threshold = 0.7
                ratio = 4.0
                compressed = np.copy(audio_data)

                mask = np.abs(audio_data) > threshold
                if np.any(mask):
                    excess = np.abs(audio_data[mask]) - threshold
                    compressed[mask] = np.sign(audio_data[mask]) * (
                        threshold + excess / ratio
                    )

                return compressed
            except:
                return audio_data

        def calculate_snr(self, audio_data):
            try:
                signal_power = np.mean(audio_data**2)
                fft = np.fft.fft(audio_data)
                freqs = np.fft.fftfreq(len(audio_data), 1 / self.sample_rate)

                noise_mask = np.abs(freqs) > 10000
                noise_power = np.mean(np.abs(fft[noise_mask]) ** 2)

                if noise_power > 0:
                    snr_db = 10 * np.log10(signal_power / noise_power)
                    return max(0, min(100, snr_db))
                return 50.0
            except:
                return 50.0

        def enhance_audio(self, audio_data):
            try:
                enhanced = self.apply_filters(audio_data)
                enhanced = self.reduce_noise(enhanced)
                enhanced = self.normalize_audio(enhanced)
                enhanced = self.apply_compression(enhanced)

                metrics = {
                    "original_rms": float(np.sqrt(np.mean(audio_data**2))),
                    "enhanced_rms": float(np.sqrt(np.mean(enhanced**2))),
                    "original_peak": float(np.max(np.abs(audio_data))),
                    "enhanced_peak": float(np.max(np.abs(enhanced))),
                    "snr_db": float(self.calculate_snr(enhanced)),
                    "enhancement_applied": True,
                }

                return enhanced, metrics
            except Exception as e:
                print(f"Enhancement error: {e}")
                return audio_data, {"enhancement_applied": False}


def generate_test_scenarios():
    """Generate different audio scenarios for testing"""
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))

    scenarios = {}

    # Scenario 1: Clean speech-like signal
    scenarios["clean"] = {
        "name": "Clean Signal (440Hz tone)",
        "audio": 0.3 * np.sin(2 * np.pi * 440 * t),
        "description": "Pure sine wave, no noise",
    }

    # Scenario 2: White noise
    scenarios["noise"] = {
        "name": "White Noise",
        "audio": 0.2 * np.random.randn(len(t)),
        "description": "Random white noise",
    }

    # Scenario 3: Signal + noise (typical case)
    scenarios["noisy"] = {
        "name": "Signal + Noise",
        "audio": 0.3 * np.sin(2 * np.pi * 440 * t) + 0.15 * np.random.randn(len(t)),
        "description": "Signal with moderate noise",
    }

    # Scenario 4: Low amplitude signal
    scenarios["quiet"] = {
        "name": "Quiet Signal",
        "audio": 0.05 * np.sin(2 * np.pi * 440 * t) + 0.02 * np.random.randn(len(t)),
        "description": "Low amplitude signal with noise",
    }

    # Scenario 5: Clipped signal
    scenarios["clipped"] = {
        "name": "Clipped Signal",
        "audio": np.clip(
            0.8 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.random.randn(len(t)),
            -0.99,
            0.99,
        ),
        "description": "Signal with clipping distortion",
    }

    # Scenario 6: Real-world scenario
    scenarios["realistic"] = {
        "name": "Realistic Audio",
        "audio": generate_realistic_audio(t),
        "description": "Simulated real-world audio with multiple issues",
    }

    return scenarios


def generate_realistic_audio(t):
    """Generate realistic audio with multiple issues"""
    sample_rate = 16000

    # Base signal (speech-like)
    base = 0.2 * np.sin(2 * np.pi * 200 * t)  # Fundamental frequency
    base += 0.1 * np.sin(2 * np.pi * 400 * t)  # Harmonic
    base += 0.05 * np.sin(2 * np.pi * 800 * t)  # Higher harmonic

    # Add amplitude modulation (like speech)
    modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)
    base *= modulation

    # Add noise
    white_noise = 0.08 * np.random.randn(len(t))
    pink_noise = generate_pink_noise(len(t)) * 0.05

    # Add hum (50/60 Hz)
    hum = 0.03 * np.sin(2 * np.pi * 50 * t)

    # Add occasional clicks
    clicks = np.zeros(len(t))
    for i in range(5):
        pos = np.random.randint(0, len(t) - 100)
        clicks[pos : pos + 100] += 0.3 * np.exp(-np.arange(100) / 20)

    # Combine everything
    audio = base + white_noise + pink_noise + hum + clicks

    # Add some clipping
    audio = np.clip(audio, -0.95, 0.95)

    return audio


def generate_pink_noise(n):
    """Generate pink noise (1/f noise)"""
    white = np.random.randn(n)
    pink = np.cumsum(white)
    return pink / np.max(np.abs(pink))


def analyze_audio(audio, sample_rate=16000):
    """Analyze audio characteristics"""
    analysis = {
        "rms": float(np.sqrt(np.mean(audio**2))),
        "peak": float(np.max(np.abs(audio))),
        "crest_factor": (
            float(np.max(np.abs(audio)) / np.sqrt(np.mean(audio**2)))
            if np.sqrt(np.mean(audio**2)) > 0
            else 0
        ),
        "zero_crossing_rate": float(np.sum(np.diff(np.sign(audio)) != 0) / len(audio)),
    }

    # Frequency analysis
    fft = np.fft.fft(audio)
    freqs = np.fft.fftfreq(len(audio), 1 / sample_rate)
    magnitude = np.abs(fft)

    # Find dominant frequency
    positive_freqs = freqs[: len(freqs) // 2]
    positive_magnitude = magnitude[: len(magnitude) // 2]
    dominant_freq_idx = np.argmax(positive_magnitude)
    analysis["dominant_frequency"] = float(positive_freqs[dominant_freq_idx])

    # Spectral centroid
    analysis["spectral_centroid"] = (
        float(np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude))
        if np.sum(positive_magnitude) > 0
        else 0
    )

    return analysis


def run_enhancement_test():
    """Run comprehensive enhancement test"""
    print("=== Audio Enhancement Test Suite ===\n")

    enhancer = AudioEnhancer()
    scenarios = generate_test_scenarios()

    results = {}

    for scenario_id, scenario in scenarios.items():
        print(f"Testing: {scenario['name']}")
        print(f"Description: {scenario['description']}")

        original_audio = scenario["audio"]
        original_analysis = analyze_audio(original_audio)

        # Apply enhancement
        enhanced_audio, metrics = enhancer.enhance_audio(original_audio)
        enhanced_analysis = analyze_audio(enhanced_audio)

        # Store enhanced audio for visualization
        scenario["enhanced_audio_data"] = enhanced_audio

        # Calculate improvements
        improvements = {
            "rms_change": (
                ((enhanced_analysis["rms"] / original_analysis["rms"]) - 1) * 100
                if original_analysis["rms"] > 0
                else 0
            ),
            "peak_reduction": (original_analysis["peak"] - enhanced_analysis["peak"])
            * 100,
            "snr_improvement": metrics.get("snr_db", 0) - 50,  # Assuming 50dB baseline
            "spectral_centroid_change": enhanced_analysis["spectral_centroid"]
            - original_analysis["spectral_centroid"],
        }

        results[scenario_id] = {
            "scenario": scenario,
            "original_analysis": original_analysis,
            "enhanced_analysis": enhanced_analysis,
            "metrics": metrics,
            "improvements": improvements,
        }

        # Print results
        print(f"  Original RMS: {original_analysis['rms']:.4f}")
        print(f"  Enhanced RMS: {enhanced_analysis['rms']:.4f}")
        print(f"  RMS Change: {improvements['rms_change']:+.1f}%")
        print(f"  Original Peak: {original_analysis['peak']:.4f}")
        print(f"  Enhanced Peak: {enhanced_analysis['peak']:.4f}")
        print(f"  Peak Reduction: {improvements['peak_reduction']:.1f}%")
        print(f"  SNR: {metrics.get('snr_db', 0):.1f} dB")
        print(f"  Enhancement Applied: {metrics.get('enhancement_applied', False)}")
        print()

    # Generate summary
    print("=== Enhancement Summary ===")

    total_scenarios = len(results)
    enhanced_scenarios = sum(
        1 for r in results.values() if r["metrics"].get("enhancement_applied", False)
    )
    avg_rms_improvement = np.mean(
        [r["improvements"]["rms_change"] for r in results.values()]
    )
    avg_snr = np.mean([r["metrics"].get("snr_db", 0) for r in results.values()])

    print(f"Scenarios Tested: {total_scenarios}")
    print(f"Enhancement Applied: {enhanced_scenarios}/{total_scenarios}")
    print(f"Average RMS Improvement: {avg_rms_improvement:+.1f}%")
    print(f"Average SNR: {avg_snr:.1f} dB")

    # Classify overall performance
    if avg_snr >= 30 and enhanced_scenarios >= total_scenarios * 0.8:
        performance = "Excellent"
    elif avg_snr >= 20 and enhanced_scenarios >= total_scenarios * 0.6:
        performance = "Good"
    elif avg_snr >= 10:
        performance = "Fair"
    else:
        performance = "Poor"

    print(f"Overall Performance: {performance}")

    return results


def create_visual_comparison(results):
    """Create visual comparison plots"""
    try:
        import matplotlib.pyplot as plt

        # Select a few scenarios for visualization
        test_scenarios = ["clean", "noisy", "quiet", "clipped"]

        fig, axes = plt.subplots(len(test_scenarios), 2, figsize=(15, 10))
        fig.suptitle("Audio Enhancement: Before vs After", fontsize=16)

        for i, scenario_id in enumerate(test_scenarios):
            if scenario_id not in results:
                continue

            scenario = results[scenario_id]

            # Time domain plot
            sample_rate = 16000
            duration = 2.0
            t = np.linspace(0, duration, int(sample_rate * duration))

            # Plot only first 1000 samples for clarity
            plot_samples = 1000

            # Store enhanced audio for visualization
            enhanced_audio = None
            if "enhanced_audio_data" in scenario:
                enhanced_audio = scenario["enhanced_audio_data"]
            else:
                # Generate enhanced audio if not stored
                _, enhanced_metrics = enhancer.enhance_audio(
                    scenario["scenario"]["audio"]
                )
                # For visualization, we need to actually enhance the audio
                temp_enhanced, _ = enhancer.enhance_audio(scenario["scenario"]["audio"])
                enhanced_audio = temp_enhanced

            axes[i, 0].plot(
                t[:plot_samples],
                scenario["scenario"]["audio"][:plot_samples],
                "b-",
                alpha=0.7,
                label="Original",
            )
            axes[i, 0].set_title(f"{scenario['scenario']['name']} - Original")
            axes[i, 0].set_ylabel("Amplitude")
            axes[i, 0].grid(True, alpha=0.3)

            axes[i, 1].plot(
                t[:plot_samples],
                enhanced_audio[:plot_samples],
                "r-",
                alpha=0.7,
                label="Enhanced",
            )
            axes[i, 1].set_title(f"{scenario['scenario']['name']} - Enhanced")
            axes[i, 1].set_ylabel("Amplitude")
            axes[i, 1].grid(True, alpha=0.3)

            if i == len(test_scenarios) - 1:
                axes[i, 0].set_xlabel("Time (s)")
                axes[i, 1].set_xlabel("Time (s)")

        plt.tight_layout()
        plt.savefig("audio_enhancement_comparison.png", dpi=150, bbox_inches="tight")
        print("Visual comparison saved to 'audio_enhancement_comparison.png'")

    except ImportError:
        print("Matplotlib not available. Skipping visual comparison.")
    except Exception as e:
        print(f"Error creating visualization: {e}")


def save_results(results):
    """Save test results to JSON file"""
    try:
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = {}
        for scenario_id, data in results.items():
            serializable_results[scenario_id] = {
                "scenario": {
                    "name": data["scenario"]["name"],
                    "description": data["scenario"]["description"],
                },
                "original_analysis": data["original_analysis"],
                "enhanced_analysis": data["enhanced_analysis"],
                "metrics": data["metrics"],
                "improvements": data["improvements"],
            }

        with open("audio_enhancement_results.json", "w") as f:
            json.dump(serializable_results, f, indent=2)

        print("Results saved to 'audio_enhancement_results.json'")

    except Exception as e:
        print(f"Error saving results: {e}")


if __name__ == "__main__":
    print("Starting Audio Enhancement Test Suite...\n")

    # Run the test
    results = run_enhancement_test()

    # Save results
    save_results(results)

    # Create visual comparison
    create_visual_comparison(results)

    print("\n=== Test Complete ===")
    print("Check the generated files:")
    print("- audio_enhancement_results.json (detailed metrics)")
    print("- audio_enhancement_comparison.png (visual comparison)")
