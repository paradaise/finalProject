#!/usr/bin/env python3
"""
Тест интегрированной предобработки аудио в реальном клиенте.
"""

import sys
import os
import time
import numpy as np
import logging
from pathlib import Path

# Добавляем путь к модулям клиента
sys.path.append(str(Path(__file__).parent.parent / "client"))

from audio_client_app import AudioClient
from config import SAMPLE_RATE

# Импортируем модуль тестирования
sys.path.append(str(Path(__file__).parent))
from test_preprocessor import AudioPreprocessorTester

def test_integrated_preprocessing():
    """Тестируем интегрированную предобработку в реальных условиях"""
    
    print("🧪 Запуск теста интегрированной предобработки...")
    print("=" * 60)
    
    # Создаем клиент
    client = AudioClient()
    
    # Создаем тестовые данные
    tester = AudioPreprocessorTester(SAMPLE_RATE)
    
    print("📊 Генерация тестовых аудио данных...")
    
    # Генерируем различные типы тестовых сигналов
    test_signals = {
        'speech_like': tester.generate_test_audio(1.0, 'speech_like'),
        'noise': tester.generate_test_audio(1.0, 'noise'),
        'mixed': tester.generate_test_audio(1.0, 'mixed'),
        'quiet': tester.generate_test_audio(1.0, 'speech_like') * 0.1,  # Тихий сигнал
        'loud': tester.generate_test_audio(1.0, 'speech_like') * 2.0,   # Громкий сигнал
    }
    
    results = {}
    
    for signal_name, original_audio in test_signals.items():
        print(f"\n🎵 Тест сигнала: {signal_name}")
        print("-" * 40)
        
        # Добавляем реалистичный шум
        noisy_audio = tester.add_realistic_noise(original_audio, ['white', 'hum'])
        
        # Применяем интегрированную предобработку
        start_time = time.time()
        processed_audio = client.audio_preprocessor.normalizer.peak_normalize(noisy_audio)
        processing_time = (time.time() - start_time) * 1000
        
        # Рассчитываем метрики
        metrics = tester.calculate_audio_metrics(noisy_audio, processed_audio)
        
        results[signal_name] = {
            'processing_time_ms': processing_time,
            'metrics': metrics,
            'original_amplitude': np.max(np.abs(original_audio)),
            'processed_amplitude': np.max(np.abs(processed_audio)),
            'original_rms': np.sqrt(np.mean(original_audio ** 2)),
            'processed_rms': np.sqrt(np.mean(processed_audio ** 2)),
        }
        
        print(f"⚡ Время обработки: {processing_time:.2f} мс")
        print(f"📈 Улучшение SNR: {metrics['snr_db']:.2f} dB")
        print(f"🎯 Корреляция: {metrics['correlation']:.4f}")
        print(f"📊 Исходная амплитуда: {results[signal_name]['original_amplitude']:.4f}")
        print(f"📊 Обработанная амплитуда: {results[signal_name]['processed_amplitude']:.4f}")
        print(f"📊 Нормализация RMS: {results[signal_name]['processed_rms']:.4f}")
        
        # Проверяем стабильность амплитуды
        if 0.75 <= results[signal_name]['processed_amplitude'] <= 0.85:
            print("✅ Амплитуда нормализована корректно (0.75-0.85)")
        else:
            print("❌ Амплитуда вне диапазона 0.75-0.85")
    
    # Итоговый анализ
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ ИНТЕГРИРОВАННОЙ ПРЕДОБРАБОТКИ")
    print("=" * 60)
    
    avg_processing_time = np.mean([r['processing_time_ms'] for r in results.values()])
    avg_snr = np.mean([r['metrics']['snr_db'] for r in results.values()])
    avg_correlation = np.mean([r['metrics']['correlation'] for r in results.values()])
    
    print(f"\n⚡ Среднее время обработки: {avg_processing_time:.2f} мс")
    print(f"📈 Среднее улучшение SNR: {avg_snr:.2f} dB")
    print(f"🎯 Средняя корреляция: {avg_correlation:.4f}")
    
    # Оценка производительности
    if avg_processing_time < 2.0:
        print("✅ ПРОИЗВОДИТЕЛЬНОСТЬ: Отлично (<2мс)")
    elif avg_processing_time < 5.0:
        print("✅ ПРОИЗВОДИТЕЛЬНОСТЬ: Хорошо (<5мс)")
    else:
        print("❌ ПРОИЗВОДИТЕЛЬНОСТЬ: Медленно (>5мс)")
    
    # Оценка качества
    if avg_snr > 15.0:
        print("✅ КАЧЕСТВО: Отличное (>15dB)")
    elif avg_snr > 10.0:
        print("✅ КАЧЕСТВО: Хорошее (>10dB)")
    elif avg_snr > 5.0:
        print("⚠️ КАЧЕСТВО: Удовлетворительное (>5dB)")
    else:
        print("❌ КАЧЕСТВО: Плохое (<5dB)")
    
    # Оценка сохранения сигнала
    if avg_correlation > 0.99:
        print("✅ СОХРАНЕНИЕ СИГНАЛА: Отличное (>0.99)")
    elif avg_correlation > 0.95:
        print("✅ СОХРАНЕНИЕ СИГНАЛА: Хорошее (>0.95)")
    else:
        print("❌ СОХРАНЕНИЕ СИГНАЛА: Плохое (<0.95)")
    
    # Рекомендация
    print(f"\n🎯 РЕКОМЕНДАЦИЯ:")
    if avg_processing_time < 2.0 and avg_snr > 10.0 and avg_correlation > 0.95:
        print("🏆 peak_normalize ИДЕАЛЬНО ПОДХОДИТ для real-time детекции!")
        print("   ⚡ Сверхбыстрый")
        print("   🎵 Хорошее качество") 
        print("   📊 Отличное сохранение сигнала")
        print("   🎯 Стабильная амплитуда для ML моделей")
    else:
        print("⚠️ Требуется дополнительная оптимизация")
    
    # Сохраняем результаты
    output_dir = Path(__file__).parent / "integrated_test_results"
    output_dir.mkdir(exist_ok=True)
    
    import json
    with open(output_dir / "integrated_preprocessing_test.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в: {output_dir}")
    
    return results

def main():
    """Основная функция"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        results = test_integrated_preprocessing()
        print("\n🎉 Тест интегрированной предобработки завершен успешно!")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка выполнения теста: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
