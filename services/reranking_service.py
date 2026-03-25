"""Re-ranking service using cross-encoder models.

This module provides a second-stage relevance ranking for candidate evidence
chunks retrieved from the vector store. It uses a cross-encoder model to score
pairwise relevance between the rule and each chunk, then returns the top N.
"""

import logging
from typing import List, Dict

from ai.models import get_reranker_model

logger = logging.getLogger(__name__)


class RerankingService:
    """Reranks retrieved evidence using a cross-encoder model."""

    def __init__(self):
        self._model = get_reranker_model()

    def rerank(self, rule_text: str, candidates: List[Dict[str, any]], top_k: int = 3) -> List[Dict[str, any]]:
        """Rerank candidate chunks by relevance to the rule text.

        Args:
            rule_text: The compliance requirement description.
            candidates: List of dicts containing at least 'text' and 'score'.
            top_k: Number of final chunks to return.

        Returns:
            A list of candidate dicts with an additional 'rerank_score' field.
        """
        if not candidates:
            return []

        # Ensure we pass strings to the cross-encoder; SentenceTransformers expects TextInputSequence values.
        rule_text_str = str(rule_text or "")
        inputs = []
        for c in candidates:
            # Some stored metadata may have been accidentally stored as non-string (lists or dicts) 
            # due to upstream processing. Normalize to a safe string representation.
            text = c.get("text")
            if not isinstance(text, str):
                if text is None:
                    text = ""
                elif isinstance(text, (list, tuple)):
                    text = " ".join(str(t) for t in text)
                else:
                    text = str(text)
            inputs.append((rule_text_str, text))

        try:
            scores = self._model.predict(inputs)
        except Exception as ex:
            logger.exception("Reranker scoring failed: %s", ex)
            return candidates[:top_k]

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        # Sort by rerank score (higher is more relevant)
        sorted_candidates = sorted(candidates, key=lambda c: c.get("rerank_score", 0.0), reverse=True)
        return sorted_candidates[:top_k]
