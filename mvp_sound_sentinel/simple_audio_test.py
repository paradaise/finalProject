#!/usr/bin/env python3
"""
Simple Audio Enhancement Demo - Working Version
Shows clear before/after differences
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import json

def simple_enhance_audio(audio_data, sample_rate=16000):
    """Simple but effective audio enhancement"""
    enhanced = audio_data.copy()
    
    # 1. Simple high-pass filter to remove DC offset
    try:
        # Simple DC removal
        enhanced = enhanced - np.mean(enhanced)
    except:
        pass
    
    # 2. Gentle noise reduction
    try:
        # Simple moving average filter for noise reduction
        window_size = 5
        kernel = np.ones(window_size) / window_size
        noise_floor = np.convolve(np.abs(enhanced), kernel, mode='same')
        
        # Reduce noise by thresholding
        threshold = np.percentile(noise_floor, 70)
        mask = noise_floor > threshold
        enhanced[mask] *= 0.5  # Reduce noisy parts
    except:
        pass
    
    # 3. Simple normalization
    try:
        current_rms = np.sqrt(np.mean(enhanced ** 2))
        if current_rms > 0:
            target_rms = 0.3
            gain = target_rms / current_rms
            gain = np.clip(gain, 0.1, 5.0)  # Limit gain
            enhanced *= gain
    except:
        pass
    
    # 4. Simple limiting to prevent clipping
    try:
        max_val = 0.95
        enhanced = np.clip(enhanced, -max_val, max_val)
    except:
        pass
    
    return enhanced

def analyze_audio(audio, sample_rate=16000):
    """Analyze audio characteristics"""
    analysis = {
        'rms': float(np.sqrt(np.mean(audio ** 2))),
        'peak': float(np.max(np.abs(audio))),
        'crest_factor': float(np.max(np.abs(audio)) / np.sqrt(np.mean(audio ** 2))) if np.sqrt(np.mean(audio ** 2)) > 0 else 0,
        'zero_crossing_rate': float(np.sum(np.diff(np.sign(audio)) != 0) / len(audio)),
    }
    
    # Frequency analysis
    fft = np.fft.fft(audio)
    freqs = np.fft.fftfreq(len(audio), 1/sample_rate)
    magnitude = np.abs(fft)
    
    # Find dominant frequency
    positive_freqs = freqs[:len(freqs)//2]
    positive_magnitude = magnitude[:len(magnitude)//2]
    dominant_freq_idx = np.argmax(positive_magnitude)
    analysis['dominant_frequency'] = float(positive_freqs[dominant_freq_idx])
    
    # Spectral centroid
    analysis['spectral_centroid'] = float(np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude)) if np.sum(positive_magnitude) > 0 else 0
    
    return analysis

def generate_test_scenarios():
    """Generate different audio scenarios for testing"""
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    scenarios = {}
    
    # Scenario 1: Clean speech-like signal
    scenarios['clean'] = {
        'name': 'Clean Signal (440Hz tone)',
        'audio': 0.3 * np.sin(2 * np.pi * 440 * t),
        'description': 'Pure sine wave, no noise'
    }
    
    # Scenario 2: Signal with noise
    scenarios['noisy'] = {
        'name': 'Signal + Noise',
        'audio': 0.3 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t)),
        'description': 'Signal with moderate noise'
    }
    
    # Scenario 3: Quiet signal
    scenarios['quiet'] = {
        'name': 'Quiet Signal',
        'audio': 0.05 * np.sin(2 * np.pi * 440 * t) + 0.02 * np.random.randn(len(t)),
        'description': 'Low amplitude signal with noise'
    }
    
    # Scenario 4: Clipped signal
    scenarios['clipped'] = {
        'name': 'Clipped Signal',
        'audio': np.clip(0.8 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.random.randn(len(t)), -0.99, 0.99),
        'description': 'Signal with clipping distortion'
    }
    
    return scenarios

def run_simple_test():
    """Run simple enhancement test"""
    print("=== Simple Audio Enhancement Test ===\n")
    
    scenarios = generate_test_scenarios()
    results = {}
    
    for scenario_id, scenario in scenarios.items():
        print(f"Testing: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        
        original_audio = scenario['audio']
        enhanced_audio = simple_enhance_audio(original_audio)
        
        original_analysis = analyze_audio(original_audio)
        enhanced_analysis = analyze_audio(enhanced_audio)
        
        # Calculate improvements
        improvements = {
            'rms_change': ((enhanced_analysis['rms'] / original_analysis['rms']) - 1) * 100 if original_analysis['rms'] > 0 else 0,
            'peak_reduction': (original_analysis['peak'] - enhanced_analysis['peak']) * 100,
            'spectral_centroid_change': enhanced_analysis['spectral_centroid'] - original_analysis['spectral_centroid']
        }
        
        results[scenario_id] = {
            'scenario': scenario,
            'original_audio': original_audio,
            'enhanced_audio': enhanced_audio,
            'original_analysis': original_analysis,
            'enhanced_analysis': enhanced_analysis,
            'improvements': improvements
        }
        
        # Print results
        print(f"  Original RMS: {original_analysis['rms']:.4f}")
        print(f"  Enhanced RMS: {enhanced_analysis['rms']:.4f}")
        print(f"  RMS Change: {improvements['rms_change']:+.1f}%")
        print(f"  Original Peak: {original_analysis['peak']:.4f}")
        print(f"  Enhanced Peak: {enhanced_analysis['peak']:.4f}")
        print(f"  Peak Reduction: {improvements['peak_reduction']:.1f}%")
        print()
    
    # Generate summary
    print("=== Enhancement Summary ===")
    
    total_scenarios = len(results)
    avg_rms_improvement = np.mean([r['improvements']['rms_change'] for r in results.values()])
    
    print(f"Scenarios Tested: {total_scenarios}")
    print(f"Average RMS Improvement: {avg_rms_improvement:+.1f}%")
    
    # Classify overall performance
    if avg_rms_improvement > 10:
        performance = "Good"
    elif avg_rms_improvement > 0:
        performance = "Fair"
    else:
        performance = "Poor"
    
    print(f"Overall Performance: {performance}")
    
    return results

def create_visual_comparison(results):
    """Create visual comparison plots"""
    try:
        test_scenarios = ['clean', 'noisy', 'quiet', 'clipped']
        
        fig, axes = plt.subplots(len(test_scenarios), 2, figsize=(15, 10))
        fig.suptitle('Audio Enhancement: Before vs After', fontsize=16)
        
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
            
            # Original
            axes[i, 0].plot(t[:plot_samples], scenario['original_audio'][:plot_samples], 'b-', alpha=0.7, label='Original')
            axes[i, 0].set_title(f"{scenario['scenario']['name']} - Original")
            axes[i, 0].set_ylabel('Amplitude')
            axes[i, 0].grid(True, alpha=0.3)
            axes[i, 0].set_ylim(-1, 1)
            
            # Enhanced
            axes[i, 1].plot(t[:plot_samples], scenario['enhanced_audio'][:plot_samples], 'r-', alpha=0.7, label='Enhanced')
            axes[i, 1].set_title(f"{scenario['scenario']['name']} - Enhanced")
            axes[i, 1].set_ylabel('Amplitude')
            axes[i, 1].grid(True, alpha=0.3)
            axes[i, 1].set_ylim(-1, 1)
            
            if i == len(test_scenarios) - 1:
                axes[i, 0].set_xlabel('Time (s)')
                axes[i, 1].set_xlabel('Time (s)')
        
        plt.tight_layout()
        plt.savefig('simple_audio_enhancement_comparison.png', dpi=150, bbox_inches='tight')
        print("Visual comparison saved to 'simple_audio_enhancement_comparison.png'")
        
    except Exception as e:
        print(f"Error creating visualization: {e}")

def save_results(results):
    """Save test results to JSON file"""
    try:
        serializable_results = {}
        for scenario_id, data in results.items():
            serializable_results[scenario_id] = {
                'scenario': {
                    'name': data['scenario']['name'],
                    'description': data['scenario']['description']
                },
                'original_analysis': data['original_analysis'],
                'enhanced_analysis': data['enhanced_analysis'],
                'improvements': data['improvements']
            }
        
        with open('simple_audio_enhancement_results.json', 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print("Results saved to 'simple_audio_enhancement_results.json'")
        
    except Exception as e:
        print(f"Error saving results: {e}")

if __name__ == "__main__":
    print("Starting Simple Audio Enhancement Test...\n")
    
    # Run the test
    results = run_simple_test()
    
    # Save results
    save_results(results)
    
    # Create visual comparison
    create_visual_comparison(results)
    
    print("\n=== Test Complete ===")
    print("Check the generated files:")
    print("- simple_audio_enhancement_results.json (detailed metrics)")
    print("- simple_audio_enhancement_comparison.png (visual comparison)")
