from __future__ import annotations

from typing import List, Tuple, Dict, Any
import os
import hashlib
import requests
from pathlib import Path

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub


class YAMNetCache:
    """Кэширование YAMNet модели локально"""

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "cache", "yamnet")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # URLs для скачивания
        self.model_url = "https://tfhub.dev/google/yamnet/1"
        self.class_map_url = "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"

        # Локальные пути
        self.model_path = self.cache_dir / "yamnet_model"
        self.class_map_path = self.cache_dir / "yamnet_class_map.csv"

    def is_model_cached(self) -> bool:
        """Проверяет, закэширована ли модель"""
        return self.model_path.exists() and self.class_map_path.exists()

    def download_model(self) -> bool:
        """Скачивает и кэширует модель"""
        try:
            print("📥 Скачивание YAMNet модели...")

            # Скачиваем модель через TensorFlow Hub (автоматически кэшируется)
            model = hub.load(self.model_url)

            # Сохраняем модель в формате SavedModel
            tf.saved_model.save(model, str(self.model_path))

            # Скачиваем class map
            print("📥 Скачивание class map...")
            response = requests.get(self.class_map_url)
            response.raise_for_status()

            with open(self.class_map_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            print("✅ YAMNet модель успешно закэширована")
            return True

        except Exception as e:
            print(f"❌ Ошибка скачивания модели: {e}")
            return False

    def load_cached_model(self) -> Tuple[Any, List[str]]:
        """Загружает модель из кэша"""
        try:
            print("📂 Загрузка YAMNet из кэша...")

            # Загружаем модель из кэша
            model = tf.saved_model.load(str(self.model_path))

            # Загружаем class names
            class_names = []
            with open(self.class_map_path, "r", encoding="utf-8") as f:
                next(f)  # skip header
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        # 3rd column contains display label
                        class_names.append(parts[2])

            print(f"✅ YAMNet модель загружена из кэша. Классов: {len(class_names)}")
            return model, class_names

        except Exception as e:
            print(f"❌ Ошибка загрузки из кэша: {e}")
            return None, None

    def get_model(self, force_download: bool = False) -> Tuple[Any, List[str]]:
        """Получает модель (из кэша или скачивает)"""
        if force_download or not self.is_model_cached():
            if not self.download_model():
                raise RuntimeError("Не удалось скачать YAMNet модель")

        return self.load_cached_model()


# Глобальный экземпляр кэша
_yamnet_cache = YAMNetCache()


def load_yamnet_model(force_download: bool = False) -> Tuple[Any, List[str]]:
    """Загрузка YAMNet модели с локальным кэшированием

    Args:
        force_download: Принудительно скачать модель заново

    Returns:
        (model, class_names)
    """
    return _yamnet_cache.get_model(force_download=force_download)


def extract_embeddings(audio_data: List[float], model: Any) -> List[float]:
    """Извлечение средних YAMNet эмбеддингов для аудио"""
    try:
        audio_np = np.array(audio_data, dtype=np.float32)

        # YAMNet ожидает моно 16kHz. Если многоканальный, берём первый канал
        if len(audio_np.shape) > 1:
            audio_np = audio_np[:, 0]

        _, embeddings, _ = model(audio_np)

        # Возвращаем средний эмбеддинг по времени (1024-d вектор)
        embedding_mean = np.mean(embeddings.numpy(), axis=0)
        return embedding_mean.tolist()
    except Exception as e:
        print(f"❌ Ошибка извлечения embeddings: {e}")
        return []


def detect_sound(
    audio_data: List[float],
    model: Any,
    class_names: List[str],
) -> Dict[str, Any]:
    """Детекция топ-5 YAMNet классов для аудио"""
    try:
        audio_np = np.array(audio_data, dtype=np.float32)

        if len(audio_np.shape) > 1:
            audio_np = audio_np[:, 0]

        scores, embeddings, _ = model(audio_np)

        top_scores = tf.math.top_k(scores, k=5)
        results = []

        for i in range(5):
            class_id = top_scores.indices[0][i].numpy()
            confidence = top_scores.values[0][i].numpy()
            class_name = class_names[class_id]
            results.append(
                {
                    "sound_type": class_name,
                    "confidence": float(confidence),
                }
            )

        return {"predictions": results, "embeddings": embeddings.numpy().tolist()}
    except Exception as e:
        print(f"❌ Ошибка детекции: {e}")
        return {"predictions": [], "embeddings": []}


def clear_yamnet_cache() -> bool:
    """Очистка кэша YAMNet"""
    try:
        if _yamnet_cache.is_model_cached():
            import shutil

            shutil.rmtree(_yamnet_cache.cache_dir)
            print("🧹 Кэш YAMNet очищен")
            return True
        else:
            print("ℹ️ Кэш YAMNet уже пуст")
            return True
    except Exception as e:
        print(f"❌ Ошибка очистки кэша: {e}")
        return False


def get_cache_info() -> Dict[str, Any]:
    """Информация о кэше"""
    return {
        "cache_dir": str(_yamnet_cache.cache_dir),
        "model_cached": _yamnet_cache.is_model_cached(),
        "model_path": str(_yamnet_cache.model_path),
        "class_map_path": str(_yamnet_cache.class_map_path),
        "model_url": _yamnet_cache.model_url,
        "class_map_url": _yamnet_cache.class_map_url,
    }


# Функции для совместимости со старым кодом
def get_yamnet_model_info() -> Dict[str, Any]:
    """Получение информации о модели"""
    cache_info = get_cache_info()
    return {
        "status": "cached" if cache_info["model_cached"] else "not_cached",
        "cache_location": cache_info["cache_dir"],
        "model_size": "15MB (approx)",
        "class_count": 521,
    }
