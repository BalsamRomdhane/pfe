"""Embedding generation with caching.

This module centralizes embedding generation using a shared model and caches results
to avoid redundant computation during repeated compliance audits.
"""

import hashlib
import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

from ai.models import get_embedding_model

logger = logging.getLogger(__name__)


def _cache_key(text: str, model_name: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return f"embedding:{model_name}:{digest}"


import numpy as np
def embed_text(text: str, model_name: str = None):
    """Embed a single text string, using cache if available. Always returns float32 numpy array. Adds BGE prefix."""
    print("===== EMBEDDINGS =====")
    print("EMBEDDING INPUT TEXT LENGTH:", len(text))
    print("EMBEDDING INPUT PREVIEW:", text[:300])
    if not text:
        print("ERROR: Empty text for embedding generation")
        return np.zeros((1,), dtype="float32")

    # Detect if this is a query or passage by prefix (callers should pass the right prefix)
    is_query = text.strip().lower().startswith("query:")
    is_passage = text.strip().lower().startswith("passage:")
    # If not prefixed, default to passage
    if not (is_query or is_passage):
        # Heuristic: if looks like a question or short, treat as query
        if len(text) < 200 or text.strip().endswith("?"):
            text = "query: " + text
        else:
            text = "passage: " + text

    model_name = model_name or getattr(settings, "COMPLIANCE_EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
    key = _cache_key(text, model_name)
    cached = cache.get(key)
    if cached is not None:
        logger.debug("Embedding cache hit for key %s", key)
        print("EMBEDDING CACHE HIT")
        print("EMBEDDING SHAPE:", len(cached))
        arr = np.array(cached, dtype="float32")
        print("EMBEDDING DIM:", arr.shape)
        return arr

    try:
        model = get_embedding_model(model_name)
        embedding = model.encode(text, show_progress_bar=False)
        if isinstance(embedding, list):
            embedding = np.array(embedding)
        embedding = embedding.astype("float32")
        # Fix: If shape is (N, 1, 1024), squeeze axis 1
        if len(embedding.shape) == 3 and embedding.shape[1] == 1:
            embedding = embedding[:, 0, :]
        # If shape is (1024,), make it (1, 1024)
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
            
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        print("Embeddings final shape:", embedding.shape)
        assert embedding.shape[1] == 1024, f"Embedding dim mismatch: {embedding.shape}"
        cache.set(key, embedding, timeout=60 * 60 * 24)  # Cache for 24h
        logger.debug("Generated embedding (cached)")
        return embedding
    except Exception as ex:
        logger.exception("Failed to embed text: %s", ex)
        # Try a fallback to a known-good model if the first attempt failed.
        try:
            fallback_model = get_embedding_model("intfloat/multilingual-e5-large")
            embedding = fallback_model.encode(text, show_progress_bar=False)
            if isinstance(embedding, list):
                embedding = np.array(embedding)
            embedding = embedding.astype("float32")
            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
                
            print("EMBEDDING SHAPE:", embedding.shape)
            cache.set(key, embedding, timeout=60 * 60 * 24)
            logger.debug("Generated embedding using fallback model (cached)")
            return embedding
        except Exception as ex2:
            logger.exception("Fallback embedding failed: %s", ex2)
        return np.zeros((1, 1024), dtype="float32")


def embed_texts(texts: List[str], model_name: str = None) -> List[List[float]]:
    """Embed multiple texts. Individual results are cached for efficiency. Adds BGE passage prefix and returns float32 numpy arrays."""
    import numpy as np
    embeddings = []
    for text in texts:
        t = text.strip()
        if not t.lower().startswith("passage:"):
            t = "passage: " + t
        emb = embed_text(t, model_name=model_name)
        import numpy as np
        if not isinstance(emb, np.ndarray):
            emb = np.array(emb, dtype="float32")
        else:
            emb = emb.astype("float32")
        # FIX: If shape is (1,1024), squeeze to (1024,)
        if len(emb.shape) == 2 and emb.shape[0] == 1:
            emb = emb[0]
        if emb.size == 0:
            logger.warning("Embedding generation returned empty for text length %d", len(text or ""))
        embeddings.append(emb)
    arr = np.stack(embeddings) if embeddings else np.zeros((0, 1024), dtype="float32")
    print("CHUNK EMBEDDINGS SHAPE:", arr.shape)
    assert arr.shape[1] == 1024, f"Embeddings shape error: {arr.shape}"
    return embeddings


def get_embedding_dimension(model_name: str = None) -> int:
    """Return the dimensionality of the embedding model."""
    model_name = model_name or getattr(settings, "COMPLIANCE_EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
    try:
        model = get_embedding_model(model_name)
        embedding = model.encode(["test"], show_progress_bar=False, convert_to_numpy=True)[0]
        return len(embedding)
    except Exception as ex:
        logger.exception("Failed to determine embedding dimension for model %s: %s", model_name, ex)
        # Fallback to a reasonable default to avoid breaking the system.
        return 768
