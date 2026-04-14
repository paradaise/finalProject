#!/usr/bin/env python3
"""
Light Audio Preprocessor
======================

Супер-лёгкий предпроцессор (только DC-removal + peak_normalize)
Оптимизирован для Raspberry Pi и YAMNet детекции.
"""

import numpy as np


class LightAudioPreprocessor:
    """Супер-лёгкий предпроцессор (только DC-removal + peak_normalize)"""
    
    def __init__(self, target_peak: float = 0.95):
        """
        Инициализация предпроцессора
        
        Args:
            target_peak: Целевая пиковая амплитуда (0.8-1.0)
        """
        self.target_peak = target_peak
    
    def preprocess(self, audio: np.ndarray) -> np.ndarray:
        """
        Применить лёгкую предобработку
        
        Args:
            audio: Входной аудиосигнал
            
        Returns:
            np.ndarray: Обработанный аудиосигнал
        """
        # Быстрый DC-removal (устранение смещения)
        audio = audio - np.mean(audio)
        
        # Peak normalization для стабильной амплитуды
        peak = np.max(np.abs(audio))
        if peak > 0:
            return audio * (self.target_peak / peak)
        else:
            return audio


# Быстрая функция для использования без класса
def light_preprocess(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """
    Быстрая функция предобработки без создания экземпляра класса
    
    Args:
        audio: Входной аудиосигнал
        target_peak: Целевая пиковая амплитуда
        
    Returns:
        np.ndarray: Обработанный аудиосигнал
    """
    # DC-removal
    audio = audio - np.mean(audio)
    
    # Peak normalization
    peak = np.max(np.abs(audio))
    if peak > 0:
        return audio * (target_peak / peak)
    else:
        return audio


# Импорты для удобного использования
__all__ = ['LightAudioPreprocessor', 'light_preprocess']
