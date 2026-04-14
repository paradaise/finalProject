"""
Main audio preprocessor that combines all preprocessing methods.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

from .noise_reduction import NoiseReduction, apply_noise_gate
from .normalization import AudioNormalization
from .filtering import AudioFiltering, apply_equalizer
from .enhancement import AudioEnhancement


class AudioPreprocessor:
    """
    Main audio preprocessor that combines various audio processing techniques
    to improve sound detection accuracy.
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.logger = logging.getLogger(__name__)
        
        # Initialize processing modules
        self.noise_reducer = NoiseReduction(sample_rate)
        self.normalizer = AudioNormalization()
        self.filter = AudioFiltering(sample_rate)
        self.enhancer = AudioEnhancement(sample_rate)
        
        # Processing configuration
        self.config = {
            'noise_reduction': {
                'enabled': True,
                'method': 'comprehensive',  # 'spectral_subtraction', 'bandpass', 'comprehensive'
                'alpha': 2.0,
                'beta': 0.01
            },
            'filtering': {
                'enabled': True,
                'method': 'comprehensive',  # 'bandpass', 'highpass', 'lowpass', 'notch', 'comprehensive'
                'low_freq': 80,
                'high_freq': 8000,
                'remove_power_line': True,
                'power_line_freq': 50
            },
            'normalization': {
                'enabled': True,
                'method': 'comprehensive',  # 'peak', 'rms', 'lufs', 'adaptive', 'comprehensive'
                'target_level': 0.8,
                'target_rms': 0.1
            },
            'enhancement': {
                'enabled': True,
                'method': 'speech',  # 'spectral', 'speech', 'comprehensive'
                'enhancement_factor': 1.3
            },
            'noise_gate': {
                'enabled': True,
                'threshold': 0.01,
                'ratio': 10,
                'attack': 0.01,
                'release': 0.1
            },
            'equalizer': {
                'enabled': False,
                'low_gain': 1.2,
                'mid_gain': 1.0,
                'high_gain': 0.8
            }
        }
    
    def configure(self, config: Dict):
        """
        Update processing configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config.update(config)
        self.logger.info("Audio preprocessor configuration updated")
    
    def preprocess(self, audio: np.ndarray, 
                  processing_steps: Optional[List[str]] = None) -> np.ndarray:
        """
        Apply audio preprocessing pipeline.
        
        Args:
            audio: Input audio signal
            processing_steps: List of processing steps to apply (None for all)
            
        Returns:
            Preprocessed audio signal
        """
        if processing_steps is None:
            processing_steps = ['noise_reduction', 'filtering', 'normalization', 
                             'enhancement', 'noise_gate', 'equalizer']
        
        processed_audio = audio.copy()
        
        # Step 1: Noise Reduction
        if 'noise_reduction' in processing_steps and self.config['noise_reduction']['enabled']:
            method = self.config['noise_reduction']['method']
            
            if method == 'spectral_subtraction':
                processed_audio = self.noise_reducer.spectral_subtraction(
                    processed_audio, 
                    alpha=self.config['noise_reduction']['alpha'],
                    beta=self.config['noise_reduction']['beta']
                )
            elif method == 'bandpass':
                processed_audio = self.noise_reducer.apply_bandpass_filter(processed_audio)
            elif method == 'comprehensive':
                processed_audio = self.noise_reducer.reduce_background_noise(processed_audio)
            
            self.logger.debug(f"Applied noise reduction: {method}")
        
        # Step 2: Filtering
        if 'filtering' in processing_steps and self.config['filtering']['enabled']:
            method = self.config['filtering']['method']
            
            if method == 'bandpass':
                processed_audio = self.filter.bandpass_filter(
                    processed_audio,
                    low_freq=self.config['filtering']['low_freq'],
                    high_freq=self.config['filtering']['high_freq']
                )
            elif method == 'highpass':
                processed_audio = self.filter.highpass_filter(
                    processed_audio,
                    cutoff_freq=self.config['filtering']['low_freq']
                )
            elif method == 'lowpass':
                processed_audio = self.filter.lowpass_filter(
                    processed_audio,
                    cutoff_freq=self.config['filtering']['high_freq']
                )
            elif method == 'notch':
                processed_audio = self.filter.notch_filter(processed_audio)
            elif method == 'comprehensive':
                processed_audio = self.filter.comprehensive_filtering(processed_audio)
            
            # Remove power line noise if enabled
            if self.config['filtering']['remove_power_line']:
                processed_audio = self.filter.remove_power_line_noise(
                    processed_audio,
                    freq=self.config['filtering']['power_line_freq']
                )
            
            self.logger.debug(f"Applied filtering: {method}")
        
        # Step 3: Normalization
        if 'normalization' in processing_steps and self.config['normalization']['enabled']:
            method = self.config['normalization']['method']
            
            if method == 'peak':
                processed_audio = self.normalizer.peak_normalize(processed_audio)
            elif method == 'rms':
                processed_audio = self.normalizer.rms_normalize(
                    processed_audio,
                    target_rms=self.config['normalization']['target_rms']
                )
            elif method == 'lufs':
                processed_audio = self.normalizer.lufs_normalize(processed_audio)
            elif method == 'adaptive':
                processed_audio = self.normalizer.adaptive_normalization(processed_audio)
            elif method == 'comprehensive':
                processed_audio = self.normalizer.comprehensive_normalize(processed_audio)
            
            self.logger.debug(f"Applied normalization: {method}")
        
        # Step 4: Enhancement
        if 'enhancement' in processing_steps and self.config['enhancement']['enabled']:
            method = self.config['enhancement']['method']
            
            if method == 'spectral':
                processed_audio = self.enhancer.spectral_enhancement(
                    processed_audio,
                    enhancement_factor=self.config['enhancement']['enhancement_factor']
                )
            elif method == 'speech':
                processed_audio = self.enhancer.speech_enhancement(processed_audio)
            elif method == 'comprehensive':
                processed_audio = self.enhancer.comprehensive_enhancement(processed_audio)
            
            self.logger.debug(f"Applied enhancement: {method}")
        
        # Step 5: Noise Gate
        if 'noise_gate' in processing_steps and self.config['noise_gate']['enabled']:
            processed_audio = apply_noise_gate(
                processed_audio,
                threshold=self.config['noise_gate']['threshold'],
                ratio=self.config['noise_gate']['ratio'],
                attack=self.config['noise_gate']['attack'],
                release=self.config['noise_gate']['release'],
                sample_rate=self.sample_rate
            )
            
            self.logger.debug("Applied noise gate")
        
        # Step 6: Equalizer
        if 'equalizer' in processing_steps and self.config['equalizer']['enabled']:
            processed_audio = apply_equalizer(
                processed_audio,
                sample_rate=self.sample_rate,
                low_gain=self.config['equalizer']['low_gain'],
                mid_gain=self.config['equalizer']['mid_gain'],
                high_gain=self.config['equalizer']['high_gain']
            )
            
            self.logger.debug("Applied equalizer")
        
        # Ensure audio is not clipped
        max_val = np.max(np.abs(processed_audio))
        if max_val > 1.0:
            processed_audio = processed_audio / max_val
            self.logger.warning("Audio was clipped, normalized to prevent distortion")
        
        return processed_audio
    
    def get_processing_info(self) -> Dict:
        """
        Get information about current processing configuration.
        
        Returns:
            Dictionary with processing information
        """
        return {
            'sample_rate': self.sample_rate,
            'config': self.config,
            'available_methods': {
                'noise_reduction': ['spectral_subtraction', 'bandpass', 'comprehensive'],
                'filtering': ['bandpass', 'highpass', 'lowpass', 'notch', 'comprehensive'],
                'normalization': ['peak', 'rms', 'lufs', 'adaptive', 'comprehensive'],
                'enhancement': ['spectral', 'speech', 'comprehensive']
            }
        }
    
    def benchmark_methods(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Benchmark different preprocessing methods on the same audio.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Dictionary with processed audio for each method
        """
        results = {}
        
        # Test noise reduction methods
        results['spectral_subtraction'] = self.noise_reducer.spectral_subtraction(audio)
        results['bandpass_filter'] = self.noise_reducer.apply_bandpass_filter(audio)
        results['comprehensive_noise'] = self.noise_reducer.reduce_background_noise(audio)
        
        # Test filtering methods
        results['highpass'] = self.filter.highpass_filter(audio)
        results['lowpass'] = self.filter.lowpass_filter(audio)
        results['bandpass'] = self.filter.bandpass_filter(audio)
        results['comprehensive_filter'] = self.filter.comprehensive_filtering(audio)
        
        # Test normalization methods
        results['peak_normalize'] = self.normalizer.peak_normalize(audio)
        results['rms_normalize'] = self.normalizer.rms_normalize(audio)
        results['comprehensive_normalize'] = self.normalizer.comprehensive_normalize(audio)
        
        # Test enhancement methods
        results['spectral_enhance'] = self.enhancer.spectral_enhancement(audio)
        results['speech_enhance'] = self.enhancer.speech_enhancement(audio)
        results['comprehensive_enhance'] = self.enhancer.comprehensive_enhancement(audio)
        
        return results


# Convenience function for quick preprocessing
def quick_preprocess(audio: np.ndarray, 
                    sample_rate: int = 16000,
                    preset: str = 'default') -> np.ndarray:
    """
    Quick preprocessing with preset configurations.
    
    Args:
        audio: Input audio signal
        sample_rate: Audio sample rate
        preset: Preset configuration ('default', 'speech', 'noise_reduction', 'enhancement')
        
    Returns:
        Preprocessed audio signal
    """
    preprocessor = AudioPreprocessor(sample_rate)
    
    presets = {
        'default': {},  # Use default configuration
        'speech': {
            'noise_reduction': {'method': 'comprehensive'},
            'filtering': {'method': 'bandpass', 'low_freq': 80, 'high_freq': 8000},
            'normalization': {'method': 'comprehensive'},
            'enhancement': {'method': 'speech'},
            'noise_gate': {'threshold': 0.02}
        },
        'noise_reduction': {
            'noise_reduction': {'method': 'comprehensive', 'alpha': 3.0},
            'filtering': {'method': 'comprehensive'},
            'noise_gate': {'threshold': 0.05, 'ratio': 20}
        },
        'enhancement': {
            'enhancement': {'method': 'comprehensive', 'enhancement_factor': 1.5},
            'normalization': {'method': 'comprehensive'},
            'equalizer': {'enabled': True}
        }
    }
    
    if preset in presets:
        preprocessor.configure(presets[preset])
    
    return preprocessor.preprocess(audio)
