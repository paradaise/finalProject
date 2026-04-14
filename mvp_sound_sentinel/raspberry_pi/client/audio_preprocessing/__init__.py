"""
Audio preprocessing module for Sound Sentinel.
Contains various audio processing methods to improve sound detection accuracy.
"""

from .noise_reduction import NoiseReduction, apply_noise_gate
from .normalization import AudioNormalization
from .filtering import AudioFiltering, apply_equalizer
from .enhancement import AudioEnhancement
from .preprocessor import AudioPreprocessor, quick_preprocess

__all__ = [
    "NoiseReduction",
    "AudioNormalization",
    "AudioFiltering",
    "AudioEnhancement",
    "AudioPreprocessor",
    "quick_preprocess",
    "apply_noise_gate",
    "apply_equalizer",
]
