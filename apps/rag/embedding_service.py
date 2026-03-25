"""Embedding service for converting text into vectors using sentence-transformers."""

import logging
from typing import List, Optional

from functools import lru_cache

from ai.models import get_sentence_transformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Handles embedding generation using a pre-trained model.

    This service caches recent embeddings to reduce redundant model invocations and
    improve throughput for repeated compliance runs on the same documents.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    @property
    def model(self):
        return get_sentence_transformer(self.model_name)

    @lru_cache(maxsize=1024)
    def _embed_text_cached(self, text: str) -> List[float]:
        return self.model.encode([text], show_progress_bar=False, convert_to_numpy=True)[0].tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        try:
            # Use cached single-text embeddings when possible to avoid re-running the model.
            if len(texts) == 1:
                return [self._embed_text_cached(texts[0])]
            # Fall back to bulk encoding for multiple texts.
            return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()
        except Exception as ex:
            logger.exception("Failed to generate embeddings: %s", ex)
            return [[] for _ in texts]

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self._embed_text_cached(text)


_default_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """Return a shared EmbeddingService instance.

    This avoids re-loading the model on every request and provides a simple
    shared entrypoint for dependency injection.
    """

    global _default_embedding_service
    if _default_embedding_service is None:
        _default_embedding_service = EmbeddingService(model_name=model_name)
    return _default_embedding_service
