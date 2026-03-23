from __future__ import annotations

from typing import List, Tuple, Dict, Any

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub


def load_yamnet_model() -> Tuple[Any, List[str]]:
    """Load YAMNet model and its class names.

    Returns:
        (model, class_names)
    """
    try:
        print("🔄 Загрузка YAMNet модели...")

        import os

        # Clean TFHub cache to avoid stale/corrupted modules.
        import tempfile
        import shutil

        cache_dir = os.path.join(tempfile.gettempdir(), "tfhub_modules")
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print("🧹 Старый кэш TensorFlow Hub удалён")
            except Exception:
                pass

        yamnet_url = os.getenv(
            "YAMNET_TF_HUB_URL", "https://tfhub.dev/google/yamnet/1"
        )
        model = hub.load(yamnet_url)

        class_map_url = os.getenv(
            "YAMNET_CLASS_MAP_URL",
            "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv",
        )
        class_names_path = tf.keras.utils.get_file(
            "yamnet_class_map.csv",
            class_map_url,
        )

        class_names: List[str] = []
        with open(class_names_path, "r") as f:
            next(f)  # skip header
            for line in f:
                # 3rd column contains the display label
                class_names.append(line.strip().split(",")[2])

        print(f"✅ YAMNet модель загружена. Классов: {len(class_names)}")
        return model, class_names
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        raise


def extract_embeddings(
    audio_data: List[float], model: Any
) -> List[float]:
    """Extract mean YAMNet embeddings for the provided audio."""
    try:
        audio_np = np.array(audio_data, dtype=np.float32)

        # YAMNet expects mono 16kHz. If multi-channel is passed, use first channel.
        if len(audio_np.shape) > 1:
            audio_np = audio_np[:, 0]

        _, embeddings, _ = model(audio_np)

        # Return mean embedding over time (1024-d vector).
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
    """Detect top-5 YAMNet classes for the provided audio chunk."""
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

