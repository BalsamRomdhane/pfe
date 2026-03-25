"""Centralized model loading for all AI components.

This module ensures that expensive ML models are loaded once per process and reused
across requests. It provides singleton accessors for embedding, reranking, and
LLM models used by the compliance pipeline.
"""

import logging
from functools import lru_cache

from django.conf import settings

logger = logging.getLogger(__name__)


def _get_setting(name: str, default: str) -> str:
    return getattr(settings, name, default)


@lru_cache(maxsize=8)
def get_embedding_model(model_name: str = None):
    """Return a shared embedding model instance (SentenceTransformer).

    Uses a multilingual model by default to support cross-language semantic
    retrieval (e.g., English rules matched against French documents).

    Falls back to known-good models if the preferred model cannot be loaded.
    """
    preferred = model_name or _get_setting("COMPLIANCE_EMBEDDING_MODEL", "BAAI/bge-m3")
    candidates = [preferred, "intfloat/multilingual-e5-large", "sentence-transformers/all-MiniLM-L6-v2"]

    from sentence_transformers import SentenceTransformer

    last_exception = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            model = SentenceTransformer(candidate)
            logger.info("Loaded embedding model: %s", candidate)
            return model
        except Exception as ex:
            logger.warning("Failed to load embedding model '%s': %s", candidate, ex)
            last_exception = ex

    logger.error("Unable to load any embedding model; tried: %s", candidates)
    raise last_exception or RuntimeError("Failed to load embedding model.")


@lru_cache(maxsize=1)
def get_reranker_model():
    """Return a shared cross-encoder model for reranking."""
    model_name = _get_setting("COMPLIANCE_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder(model_name)
        logger.info("Loaded reranker model: %s", model_name)
        return model
    except Exception as ex:
        logger.exception("Failed to load reranker model '%s': %s", model_name, ex)
        raise


@lru_cache(maxsize=1)
def get_zero_shot_classifier(model_name: str = None):
    """Return a shared zero-shot classification pipeline."""
    model_name = model_name or _get_setting("COMPLIANCE_ZEROSHOT_MODEL", "facebook/bart-large-mnli")
    try:
        from transformers import pipeline

        classifier = pipeline("zero-shot-classification", model=model_name, device=-1)
        logger.info("Loaded zero-shot classifier model: %s", model_name)
        return classifier
    except Exception as ex:
        logger.exception("Failed to load zero-shot classifier '%s': %s", model_name, ex)
        raise


@lru_cache(maxsize=1)
def get_llm_model():
    """Return a shared LLM model for reasoning and validation."""
    # Default to a lightweight, generative model for stable JSON output.
    model_name = _get_setting("COMPLIANCE_LLM_MODEL", "gpt2")
    try:
        from transformers import pipeline

        # Use text-generation for more flexible prompting.
        # Note: Avoid passing max_length at pipeline init to prevent
        # warnings about conflicting generation arguments later.
        generator = pipeline(
            "text-generation",
            model=model_name,
            device=-1,
            truncation=True,
            do_sample=False,
        )
        logger.info("Loaded LLM model: %s", model_name)
        return generator
    except Exception as ex:
        logger.exception("Failed to load LLM model '%s': %s", model_name, ex)
        raise
