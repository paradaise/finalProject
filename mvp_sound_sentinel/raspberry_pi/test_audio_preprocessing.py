#!/usr/bin/env python3
"""
Тестирование алгоритмов предобработки аудио
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

from client.audio_preprocessing import (
    preprocess_audio, 
    batch_preprocess,
    generate_preprocessing_summary,
    spectral_subtraction,
    wiener_filter,
    simple_vad,
    webrtc_vad,
    normalize_rms,
    peak_normalize
)


def generate_test_audio():
    """Генерация тестовых аудио данных"""
    
    # 1. Чистый синусоидальный сигнал
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    clean_signal = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440 Hz
    
    # 2. Добавление шума
    noise = 0.1 * np.random.randn(len(clean_signal))
    noisy_signal = clean_signal + noise
    
    # 3. Добавление импульсивного шума
    impulse_noise = np.zeros_like(noisy_signal)
    for i in range(0, len(noisy_signal), 1000):
        impulse_noise[i] += 0.5 * np.random.randn()
    
    very_noisy_signal = noisy_signal + impulse_noise
    
    return {
        'clean': clean_signal,
        'noisy': noisy_signal,
        'very_noisy': very_noisy_signal,
        'sample_rate': sample_rate
    }


def test_noise_reduction():
    """Тестирование алгоритмов шумоподавления"""
    print("🧪 Тестирование шумоподавления...")
    
    test_signals = generate_test_audio()
    
    for name, signal in test_signals.items():
        if name == 'sample_rate':
            continue
            
        print(f"\n📊 Обработка сигнала: {name}")
        
        # Spectral Subtraction
        processed_spectral, metrics_spectral = spectral_subtraction(signal, test_signals['sample_rate'])
        print(f"   Spectral Subtraction: {metrics_spectral.get('noise_reduction_applied', False)}")
        
        # Wiener Filter
        processed_wiener, metrics_wiener = wiener_filter(signal, test_signals['sample_rate'])
        print(f"   Wiener Filter: {metrics_wiener.get('noise_reduction_applied', False)}")
        
        # Сохранение результатов
        results = {
            'original': signal,
            'spectral_subtraction': processed_spectral,
            'wiener_filter': processed_wiener,
            'metrics': {
                'spectral': metrics_spectral,
                'wiener': metrics_wiener
            }
        }
        
        # Визуализация
        plot_comparison(signal, processed_spectral, processed_wiener, f"noise_reduction_{name}")
        
        return results


def test_vad():
    """Тестирование детекции голосовой активности"""
    print("\n🎤 Тестирование детекции голосовой активности...")
    
    test_signals = generate_test_audio()
    
    # Создадим тестовый сигнал с голосом и паузами
    voice_signal = np.zeros(16000 * 3)  # 3 секунды
    for i in range(3):
        start = i * 16000
        end = (i + 1) * 16000
        if i % 2 == 0:  # Каждую секунду - голос
            voice_signal[start:end] = 0.2 * np.sin(2 * np.pi * 200 * np.linspace(0, 1, 16000))
    
    for name, signal in test_signals.items():
        if name in ['sample_rate', 'clean']:
            continue
            
        print(f"\n📊 VAD для сигнала: {name}")
        
        # Simple VAD
        processed_simple, metrics_simple = simple_vad(signal, test_signals['sample_rate'])
        print(f"   Simple VAD: {metrics_simple.get('vad_applied', False)}")
        print(f"   Voiced ratio: {metrics_simple.get('voiced_ratio', 0):.2%}")
        
        # WebRTC VAD (если доступно)
        try:
            processed_webrtc, metrics_webrtc = webrtc_vad(signal, test_signals['sample_rate'])
            print(f"   WebRTC VAD: {metrics_webrtc.get('vad_applied', False)}")
        except Exception as e:
            print(f"   WebRTC VAD: Недоступно ({e})")
        
        # Сохранение результатов
        results = {
            'original': signal,
            'simple_vad': processed_simple,
            'webrtc_vad': processed_webrtc if 'webrtc_vad' in locals() else signal,
            'metrics': {
                'simple': metrics_simple,
                'webrtc': metrics_webrtc if 'webrtc_vad' in locals() else {}
            }
        }
        
        # Визуализация
        plot_vad_comparison(signal, processed_simple, processed_webrtc if 'webrtc_vad' in locals() else signal, f"vad_{name}")
        
        return results


def test_normalization():
    """Тестирование алгоритмов нормализации"""
    print("\n📈 Тестирование нормализации...")
    
    test_signals = generate_test_audio()
    
    for name, signal in test_signals.items():
        if name == 'sample_rate':
            continue
            
        print(f"\n📊 Нормализация сигнала: {name}")
        
        # RMS Normalization
        processed_rms, metrics_rms = normalize_rms(signal, target_rms=0.3)
        print(f"   RMS Normalization: {metrics_rms.get('normalization_applied', False)}")
        print(f"   Original RMS: {metrics_rms.get('original_rms', 0):.4f}")
        print(f"   Final RMS: {metrics_rms.get('normalized_rms', 0):.4f}")
        
        # Peak Normalization
        processed_peak, metrics_peak = peak_normalize(signal, target_peak=0.95)
        print(f"   Peak Normalization: {metrics_peak.get('normalization_applied', False)}")
        print(f"   Original Peak: {metrics_peak.get('original_peak', 0):.4f}")
        print(f"   Final Peak: {metrics_peak.get('normalized_peak', 0):.4f}")
        
        # Сохранение результатов
        results = {
            'original': signal,
            'rms_normalized': processed_rms,
            'peak_normalized': processed_peak,
            'metrics': {
                'rms': metrics_rms,
                'peak': metrics_peak
            }
        }
        
        # Визуализация
        plot_normalization_comparison(signal, processed_rms, processed_peak, f"normalization_{name}")
        
        return results


def test_full_pipeline():
    """Тестирование полного пайплайна предобработки"""
    print("\n🔄 Тестирование полного пайплайна...")
    
    test_signals = generate_test_audio()
    
    all_results = []
    
    for name, signal in test_signals.items():
        if name == 'sample_rate':
            continue
            
        print(f"\n📊 Полная обработка сигнала: {name}")
        
        # Полный пайплайн
        processed_audio, metrics = preprocess_audio(
            signal,
            sample_rate=test_signals['sample_rate'],
            target_rms=0.3,
            apply_noise_reduction=True,
            apply_vad=True,
            apply_normalization=True,
            noise_reduction_method="spectral_subtraction",
            vad_method="simple"
        )
        
        print(f"   Статус: {metrics.get('preprocessing_applied', False)}")
        print(f"   Шаги: {', '.join(metrics.get('steps_applied', []))}")
        print(f"   Final RMS: {metrics.get('final_rms', 0):.4f}")
        print(f"   Final Peak: {metrics.get('final_peak', 0):.4f}")
        
        all_results.append(metrics)
        
        # Визуализация
        plot_full_pipeline(signal, processed_audio, f"full_pipeline_{name}")
    
    # Генерация отчета
    generate_preprocessing_summary(all_results, "preprocessing_test_results.md")
    print(f"\n📄 Отчет сохранен: preprocessing_test_results.md")
    
    return all_results


def plot_comparison(original, spectral, wiener, filename):
    """Визуализация сравнения шумоподавления"""
    plt.figure(figsize=(15, 5))
    
    # Оригинал
    plt.subplot(1, 3, 1)
    plt.plot(original)
    plt.title('Оригинал')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    # Spectral Subtraction
    plt.subplot(1, 3, 2)
    plt.plot(spectral)
    plt.title('Spectral Subtraction')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    # Wiener Filter
    plt.subplot(1, 3, 3)
    plt.plot(wiener)
    plt.title('Wiener Filter')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    plt.tight_layout()
    plt.savefig(f"{filename}.png")
    plt.close()
    print(f"   📊 График сохранен: {filename}.png")


def plot_vad_comparison(original, simple, webrtc, filename):
    """Визуализация сравнения VAD"""
    plt.figure(figsize=(15, 5))
    
    # Оригинал
    plt.subplot(1, 3, 1)
    plt.plot(original)
    plt.title('Оригинал')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    # Simple VAD
    plt.subplot(1, 3, 2)
    plt.plot(simple)
    plt.title('Simple VAD')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    # WebRTC VAD
    plt.subplot(1, 3, 3)
    plt.plot(webrtc)
    plt.title('WebRTC VAD')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    plt.tight_layout()
    plt.savefig(f"{filename}.png")
    plt.close()
    print(f"   📊 График сохранен: {filename}.png")


def plot_normalization_comparison(original, rms, peak, filename):
    """Визуализация сравнения нормализации"""
    plt.figure(figsize=(15, 5))
    
    # Оригинал
    plt.subplot(1, 3, 1)
    plt.plot(original)
    plt.title('Оригинал')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    # RMS Normalization
    plt.subplot(1, 3, 2)
    plt.plot(rms)
    plt.title('RMS Normalization')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    # Peak Normalization
    plt.subplot(1, 3, 3)
    plt.plot(peak)
    plt.title('Peak Normalization')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    plt.tight_layout()
    plt.savefig(f"{filename}.png")
    plt.close()
    print(f"   📊 График сохранен: {filename}.png")


def plot_full_pipeline(original, processed, filename):
    """Визуализация полного пайплайна"""
    plt.figure(figsize=(12, 6))
    
    # Оригинал
    plt.subplot(2, 1, 1)
    plt.plot(original)
    plt.title('Оригинал')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    # Обработанный
    plt.subplot(2, 1, 2)
    plt.plot(processed)
    plt.title('После предобработки')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    
    plt.tight_layout()
    plt.savefig(f"{filename}.png")
    plt.close()
    print(f"   📊 График сохранен: {filename}.png")


def save_test_results(results, filename="test_results.json"):
    """Сохранение результатов тестов"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"📄 Результаты сохранены: {filename}")


if __name__ == "__main__":
    print("🧪 Начало тестирования предобработки аудио...")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Создание папки для результатов
    os.makedirs("test_results", exist_ok=True)
    os.chdir("test_results")
    
    try:
        # Тестирование шумоподавления
        noise_results = test_noise_reduction()
        
        # Тестирование VAD
        vad_results = test_vad()
        
        # Тестирование нормализации
        norm_results = test_normalization()
        
        # Тестирование полного пайплайна
        pipeline_results = test_full_pipeline()
        
        # Сохранение всех результатов
        all_results = {
            'noise_reduction': noise_results,
            'vad': vad_results,
            'normalization': norm_results,
            'full_pipeline': pipeline_results,
            'test_time': datetime.now().isoformat()
        }
        
        save_test_results(all_results)
        
        print(f"\n✅ Все тесты завершены!")
        print(f"📁 Папка с результатами: test_results/")
        print(f"📄 Отчет: preprocessing_test_results.md")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    
    print(f"\n🏁 Тестирование завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
