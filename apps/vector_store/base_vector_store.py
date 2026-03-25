"""Base classes for vector store implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseVectorStore(ABC):
    """Abstract base class for vector store backends."""

    @abstractmethod
    def add_embeddings(self, vectors: List[Dict[str, Any]]) -> None:
        """Add multiple vectors to the store.

        Each vector dict should include:
        - "id": str
        - "vector": List[float]
        - "metadata": dict
        """

    @abstractmethod
    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Return the most similar vectors to the query."""

    @abstractmethod
    def delete_document_embeddings(self, document_id: str) -> None:
        """Remove all vectors associated with a document."""
