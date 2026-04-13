# Установка зависимостей для аудио предобработки

## Базовые зависимости (обязательные)

```bash
pip install numpy scipy matplotlib
```

## Опциональные зависимости для WebRTC VAD

```bash
pip install webrtcvad
```

## Полная установка

```bash
# Установить все зависимости
pip install -r requirements_audio.txt

# Или по отдельности
pip install numpy scipy matplotlib webrtcvad
```

## Проверка установки

```python
python -c "import numpy; import scipy; import matplotlib; print('Базовые зависимости установлены')"

# Проверка WebRTC VAD
python -c "import webrtcvad; print('WebRTC VAD доступен')"
```

## Примечания

- **webrtcvad** - опциональная зависимость для продвинутой детекции голосовой активности
- При отсутствии **webrtcvad** автоматически используется простой energy-based VAD
- Все алгоритмы работают без **webrtcvad**, но с меньшей точностью
