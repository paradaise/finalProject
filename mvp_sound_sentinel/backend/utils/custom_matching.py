import json
import sqlite3
from typing import Dict, List, Any

import numpy as np

from backend.utils.similarity import cosine_similarity


def find_best_custom_match(
    embedding: List[float], device_id: str, db_path: str
) -> Dict[str, Any]:
    """Find best matching custom sound centroid using cosine similarity."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, sound_type, embeddings, centroid, threshold 
            FROM custom_sounds 
            WHERE device_id = ?
            """,
            (device_id,),
        )

        custom_sounds = cursor.fetchall()
        conn.close()

        best_match = None
        best_similarity = 0.0

        for sound in custom_sounds:
            sound_id, name, sound_type, embeddings_str, centroid_str, threshold = sound

            print(f"🔍 Проверяем custom sound: {name} (type: {sound_type})")

            # Parse centroid (if stored) or derive it from embeddings
            try:
                if centroid_str:
                    centroid = json.loads(centroid_str)

                    # Convert numpy-like structures into Python list
                    if hasattr(centroid, "tolist"):
                        centroid = centroid.tolist()
                    elif isinstance(centroid, np.ndarray):
                        centroid = centroid.tolist()
                    elif isinstance(centroid, (int, float)):
                        # If centroid is a scalar, fall back to embeddings.
                        print(
                            f"⚠️ Centroid это число ({centroid}), используем embeddings"
                        )
                        embeddings = (
                            json.loads(embeddings_str) if embeddings_str else []
                        )
                        if embeddings and len(embeddings) > 0:
                            if isinstance(embeddings[0], list):
                                centroid = np.mean(embeddings, axis=0).tolist()
                            else:
                                centroid = embeddings
                        else:
                            print(f"❌ Нет embeddings для звука {name}")
                            continue

                    print(
                        f"✅ Centroid загружен: {len(centroid) if isinstance(centroid, list) else 'not array'}"
                    )
                else:
                    embeddings = json.loads(embeddings_str) if embeddings_str else []
                    if embeddings:
                        centroid = np.mean(embeddings, axis=0).tolist()
                        print(f"✅ Centroid вычислен: {len(centroid)} элементов")
                    else:
                        print(f"❌ Нет embeddings для звука {name}")
                        continue
            except Exception as e:
                print(f"❌ Ошибка парсинга centroid для {name}: {e}")
                continue

            if not isinstance(centroid, list):
                print(f"❌ Centroid не является списком для {name}: {type(centroid)}")
                continue

            try:
                similarity = cosine_similarity(embedding, centroid)
                print(f"📊 Схожесть с {name}: {similarity:.3f}")
            except Exception as e:
                print(f"❌ Ошибка вычисления схожести с {name}: {e}")
                continue

            if similarity > best_similarity:
                best_similarity = similarity
                import os

                default_threshold = float(
                    os.getenv("CUSTOM_MATCH_DEFAULT_THRESHOLD", "0.7")
                )

                stored_threshold = (
                    float(threshold) if threshold is not None else default_threshold
                )
                effective_threshold = max(stored_threshold, default_threshold)

                best_match = {
                    "id": sound_id,
                    "name": name,
                    "sound_type": sound_type,
                    "similarity": similarity,
                    "threshold": effective_threshold,
                }
                print(
                    f" Новый лучший матч: {name} (схожесть: {similarity:.3f}) (threshold: {effective_threshold:.3f})"
                )

        return best_match or {}
    except Exception as e:
        print(f" Ошибка поиска custom match: {e}")
        return {}
