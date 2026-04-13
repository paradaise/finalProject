#!/usr/bin/env python3
"""
Main audio preprocessing pipeline
"""

import numpy as np
from typing import Tuple, Dict, Any, List
import json
import os
from datetime import datetime

from .noise_reduction import spectral_subtraction, wiener_filter
from .voice_activity_detection import simple_vad, webrtc_vad
from .audio_normalization import normalize_rms, peak_normalize


def preprocess_audio(
    audio: np.ndarray,
    sample_rate: int = 16000,
    target_rms: float = 0.3,
    apply_noise_reduction: bool = True,
    apply_vad: bool = True,
    apply_normalization: bool = True,
    noise_reduction_method: str = "spectral_subtraction",
    vad_method: str = "simple"
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Complete audio preprocessing pipeline
    
    Args:
        audio: Input audio signal
        sample_rate: Sample rate of audio
        target_rms: Target RMS level for normalization
        apply_noise_reduction: Whether to apply noise reduction
        apply_vad: Whether to apply voice activity detection
        apply_normalization: Whether to apply normalization
        noise_reduction_method: Method for noise reduction
        vad_method: Method for VAD
        
    Returns:
        Processed audio and comprehensive metrics
    """
    try:
        processed_audio = audio.copy()
        all_metrics = {
            "preprocessing_applied": True,
            "original_length": len(audio),
            "original_rms": float(np.sqrt(np.mean(audio ** 2))),
            "original_peak": float(np.max(np.abs(audio))),
            "steps_applied": []
        }
        
        # Step 1: Noise Reduction
        if apply_noise_reduction:
            if noise_reduction_method == "spectral_subtraction":
                processed_audio, noise_metrics = spectral_subtraction(processed_audio, sample_rate)
            elif noise_reduction_method == "wiener_filter":
                processed_audio, noise_metrics = wiener_filter(processed_audio, sample_rate)
            else:
                noise_metrics = {"noise_reduction_applied": False, "method": "none"}
            
            all_metrics["steps_applied"].append("noise_reduction")
            all_metrics.update(noise_metrics)
        
        # Step 2: Voice Activity Detection
        if apply_vad:
            if vad_method == "webrtc":
                processed_audio, vad_metrics = webrtc_vad(processed_audio, sample_rate)
            else:
                processed_audio, vad_metrics = simple_vad(processed_audio, sample_rate)
            
            all_metrics["steps_applied"].append("voice_activity_detection")
            all_metrics.update(vad_metrics)
        
        # Step 3: Normalization
        if apply_normalization:
            processed_audio, norm_metrics = normalize_rms(processed_audio, target_rms)
            all_metrics["steps_applied"].append("normalization")
            all_metrics.update(norm_metrics)
        
        # Final metrics
        all_metrics["final_length"] = len(processed_audio)
        all_metrics["final_rms"] = float(np.sqrt(np.mean(processed_audio ** 2)))
        all_metrics["final_peak"] = float(np.max(np.abs(processed_audio)))
        all_metrics["processing_time"] = datetime.now().isoformat()
        
        return processed_audio, all_metrics
        
    except Exception as e:
        error_metrics = {
            "preprocessing_applied": False,
            "error": str(e),
            "processing_time": datetime.now().isoformat()
        }
        return audio, error_metrics


def batch_preprocess(
    audio_files: List[np.ndarray],
    sample_rate: int = 16000,
    **kwargs
) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
    """
    Process multiple audio files with the same settings
    
    Args:
        audio_files: List of audio arrays
        sample_rate: Sample rate of audio
        **kwargs: Additional arguments for preprocess_audio
        
    Returns:
        List of processed audio and metrics
    """
    results = []
    
    for i, audio in enumerate(audio_files):
        try:
            processed_audio, metrics = preprocess_audio(audio, sample_rate, **kwargs)
            results.append((processed_audio, metrics))
            print(f"Processed audio {i+1}/{len(audio_files)}")
        except Exception as e:
            print(f"Error processing audio {i+1}: {e}")
            results.append((audio, {"preprocessing_applied": False, "error": str(e)}))
    
    return results


def save_preprocessing_report(metrics: Dict[str, Any], output_path: str = "preprocessing_report.json"):
    """
    Save preprocessing metrics to JSON file
    
    Args:
        metrics: Preprocessing metrics dictionary
        output_path: Path to save report
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"Preprocessing report saved to {output_path}")
    except Exception as e:
        print(f"Error saving report: {e}")


def generate_preprocessing_summary(all_metrics: List[Dict[str, Any]], output_path: str = "preprocessing_summary.md"):
    """
    Generate markdown summary of preprocessing results
    
    Args:
        all_metrics: List of metrics from multiple audio files
        output_path: Path to save summary
    """
    try:
        summary = "# Audio Preprocessing Summary\n\n"
        summary += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, metrics in enumerate(all_metrics):
            summary += f"## Audio File {i+1}\n\n"
            
            if metrics.get("preprocessing_applied", False):
                summary += f"- **Status**: ✅ Processed successfully\n"
                summary += f"- **Steps Applied**: {', '.join(metrics.get('steps_applied', []))}\n"
                summary += f"- **Original RMS**: {metrics.get('original_rms', 'N/A'):.4f}\n"
                summary += f"- **Final RMS**: {metrics.get('final_rms', 'N/A'):.4f}\n"
                summary += f"- **Original Peak**: {metrics.get('original_peak', 'N/A'):.4f}\n"
                summary += f"- **Final Peak**: {metrics.get('final_peak', 'N/A'):.4f}\n"
                
                if "noise_reduction_applied" in metrics:
                    summary += f"- **Noise Reduction**: {metrics.get('method', 'unknown')}\n"
                if "vad_applied" in metrics:
                    summary += f"- **VAD Method**: {metrics.get('method', 'unknown')}\n"
                    summary += f"- **Voiced Ratio**: {metrics.get('voiced_ratio', 0):.2%}\n"
            else:
                summary += f"- **Status**: ❌ Processing failed\n"
                summary += f"- **Error**: {metrics.get('error', 'Unknown error')}\n"
            
            summary += "\n"
        
        # Overall statistics
        successful_count = sum(1 for m in all_metrics if m.get("preprocessing_applied", False))
        summary += f"## Overall Statistics\n\n"
        summary += f"- **Total Files**: {len(all_metrics)}\n"
        summary += f"- **Successfully Processed**: {successful_count}\n"
        summary += f"- **Failed**: {len(all_metrics) - successful_count}\n"
        summary += f"- **Success Rate**: {(successful_count/len(all_metrics)*100):.1f}%\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"Preprocessing summary saved to {output_path}")
        
    except Exception as e:
        print(f"Error generating summary: {e}")
