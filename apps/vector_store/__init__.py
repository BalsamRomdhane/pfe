"""Vector store abstraction and factory.

This module exposes a `get_vector_store` helper that returns a configured
vector store backend based on the `VECTOR_DB` setting.
"""

from django.conf import settings

from .base_vector_store import BaseVectorStore


def get_vector_store() -> BaseVectorStore:
    """Return the configured vector store backend."""
    backend = settings.VECTOR_DB
    if backend == "chromadb":
        from .chromadb_store import ChromaDBStore

        return ChromaDBStore(settings.VECTOR_DB_CONFIG.get("chromadb", {}))
    if backend == "faiss":
        from .faiss_store import FAISSStore

        return FAISSStore(settings.VECTOR_DB_CONFIG.get("faiss", {}))
    if backend == "qdrant":
        from .qdrant_store import QdrantStore

        return QdrantStore(settings.VECTOR_DB_CONFIG.get("qdrant", {}))

    raise ValueError(f"Unsupported VECTOR_DB backend: {backend}")
