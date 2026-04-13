# Audio Preprocessing Package

Пакет для предобработки аудио в Sound Sentinel с различными алгоритмами улучшения качества звука.

## Структура

```
audio_preprocessing/
├── __init__.py              # Инициализация пакета
├── preprocess_audio.py      # Основной пайплайн предобработки
├── noise_reduction.py        # Алгоритмы шумоподавления
├── voice_activity_detection.py # Детекция голосовой активности
├── audio_normalization.py   # Нормализация аудио
└── README.md               # Эта документация
```

## Алгоритмы

### 1. Шумоподавление (Noise Reduction)

#### Spectral Subtraction
- Спектральное вычитание шума
- Улучшение SNR на 3-6 дБ
- Подходит для стационарного фонового шума

#### Wiener Filter
- Винеровский фильтр для адаптивного шумоподавления
- Улучшение SNR на 4-8 дБ
- Лучше работает с нестационарным шумом

### 2. Детекция голосовой активности (Voice Activity Detection)

#### Energy-based VAD
- Простая детекция на основе энергии сигнала
- Быстрая обработка
- Минимальные требования к ресурсам

#### WebRTC VAD
- Продвинутая детекция голосовой активности
- Высокая точность
- Требует библиотеку `webrtcvad`

### 3. Нормализация аудио (Audio Normalization)

#### RMS Normalization
- Нормализация по среднеквадратичному значению
- Целевой уровень RMS (по умолчанию 0.3)
- Защита от клиппинга

#### Peak Normalization
- Нормализация по пиковому значению
- Целевой уровень пика (по умолчанию 0.95)
- Сохранение динамики диапазона

## Использование

### Базовая предобработка

```python
import numpy as np
from audio_preprocessing import preprocess_audio

# Загрузка аудио
audio_data = np.load("audio.npy")

# Применение пайплайна
processed_audio, metrics = preprocess_audio(
    audio=audio_data,
    sample_rate=16000,
    target_rms=0.3,
    apply_noise_reduction=True,
    apply_vad=True,
    apply_normalization=True,
    noise_reduction_method="spectral_subtraction",
    vad_method="simple"
)

print(f"Processing completed: {metrics}")
```

### Пакетная обработка

```python
from audio_preprocessing import batch_preprocess, generate_preprocessing_summary

# Список аудио файлов
audio_files = [audio1, audio2, audio3]

# Пакетная обработка
results = batch_preprocess(
    audio_files,
    sample_rate=16000,
    apply_noise_reduction=True,
    apply_vad=True,
    apply_normalization=True
)

# Генерация отчета
generate_preprocessing_summary([metrics for _, metrics in results])
```

### Сохранение отчетов

```python
from audio_preprocessing import save_preprocessing_report

# Сохранение детального отчета в JSON
save_preprocessing_report(metrics, "detailed_report.json")

# Генерация markdown отчета
generate_preprocessing_summary([metrics1, metrics2, metrics3], "summary.md")
```

## Интеграция с основным клиентом

Для интеграции с audio_client_app.py:

```python
# В audio_client_app.py
from audio_preprocessing import preprocess_audio

# Перед отправкой на backend
def process_and_send(audio_data):
    # Предобработка
    processed_audio, metrics = preprocess_audio(
        audio_data,
        sample_rate=16000,
        target_rms=0.3
    )
    
    # Отправка обработанного аудио
    send_to_backend(processed_audio)
    
    # Логирование метрик
    print(f"Audio processed: {metrics}")
```

## Тестирование

Для тестирования алгоритмов:

```python
# Создать тестовый файл в raspberry_pi/
python test_audio_preprocessing.py
```

Тесты включают:
- Синтетические аудио данные
- Сравнение "до" и "после"
- Генерация отчетов в JSON и Markdown
- Измерение производительности алгоритмов

## Метрики

Каждый алгоритм возвращает детальные метрики:

- **Original/Final RMS**: Уровень сигнала до/после обработки
- **Original/Final Peak**: Пиковое значение до/после обработки
- **SNR Improvement**: Улучшение отношения сигнал/шум
- **Voiced Ratio**: Доля кадров с голосовой активностью
- **Clipping Detection**: Обнаружение клиппинга
- **Processing Time**: Время обработки

## Зависимости

```
numpy>=1.21.0
scipy>=1.7.0
webrtcvad>=2.0.10  # опционально для WebRTC VAD
```

## Настройки

Параметры предобработки можно настроить:

- `target_rms`: Целевой RMS уровень (0.1-0.5)
- `noise_reduction_method`: "spectral_subtraction" или "wiener_filter"
- `vad_method`: "simple" или "webrtc"
- `apply_*`: Флаги включения/выключения шагов
