"""Vector search utilities (legacy)."""

from __future__ import annotations

import math
from typing import List, Tuple, Dict, Any


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorSearch:
    """Perform similarity search over a list of vectors."""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def search(self, query_vector: List[float], vectors: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """Search the provided vector list for the most similar items.

        Each item in `vectors` should contain a `vector` key and additional metadata.
        """
        k = top_k or self.top_k
        candidates: List[Dict[str, Any]] = []

        for item in vectors:
            vector = item.get("vector")
            if not vector:
                continue
            try:
                score = _cosine_similarity(list(vector), query_vector)
            except Exception:
                score = 0.0
            candidate = {**item, "score": score}
            candidates.append(candidate)

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:k]
