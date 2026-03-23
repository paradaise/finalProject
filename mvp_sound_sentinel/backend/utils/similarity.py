from typing import List

import numpy as np


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two embedding vectors."""
    try:
        a_np = np.array(a)
        b_np = np.array(b)

        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))
    except Exception as e:
        print(f"❌ Ошибка вычисления cosine similarity: {e}")
        return 0.0

