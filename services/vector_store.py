"""Vector storage abstraction for compliance evidence retrieval.

This module provides a consistent interface for storing and retrieving
embeddings and associated text chunks.
"""

import logging
from typing import Any, Dict, List, Optional

from apps.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class VectorStore:
    def reset_store(self):
        # Reset both the FAISS index and the chunk store/id map
        if hasattr(self._store, 'reset_store'):
            self._store.reset_store()
        self._chunk_store = {}
        self._id_map = []
    """Wrapper around the configured vector store implementation."""

    def __init__(self):
        self._store = get_vector_store()
        self._chunk_store = {}
        self._id_map = []

    def add_chunks(
        self,
        document_id: str,
        standard_id: Optional[str],
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        """Add a set of chunks with embeddings to the underlying vector store."""
        # Always reset before adding new document
        self.reset_store()
        vectors = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}_{chunk.get('chunk_index', idx)}"
            metadata = {
                "document_id": document_id,
                "standard_id": standard_id,
                "chunk_id": str(chunk.get("chunk_index", idx)),
                "section_title": chunk.get("section_title"),
                "section_index": chunk.get("section_index"),
                "chunk_text": chunk.get("text", ""),
                "text": chunk.get("text", ""),
            }
            vectors.append({
                "id": chunk_id,
                "vector": embedding,
                "metadata": metadata,
            })
            # Store mapping for retrieval
            self._chunk_store[chunk_id] = chunk
            self._id_map.append(chunk_id)
        try:
            logger.debug("Indexing %d chunks for document %s", len(vectors), document_id)
            self._store.add_embeddings(vectors)
            # Validation: ensure FAISS and chunk_store are in sync
            if hasattr(self._store, '_index'):
                assert getattr(self._store._index, 'ntotal', 0) == len(self._chunk_store), f"FAISS index count {getattr(self._store._index, 'ntotal', 0)} != chunk_store {len(self._chunk_store)}"
        except Exception as ex:
            logger.exception("Failed to add embeddings to vector store: %s", ex)

    def query(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Return the most relevant chunks for a query vector, mapped to real chunk text."""
        try:
            logger.debug("Querying vector store with top_k=%d", top_k)
            results = self._store.similarity_search(query_vector, top_k=top_k)
            logger.debug("Vector store returned %d results", len(results))
            # Map FAISS ids to real chunk text using id_map and chunk_store
            retrieved_chunks = []
            for r in results:
                chunk_id = r.get("id")
                if chunk_id in self._chunk_store:
                    chunk = self._chunk_store[chunk_id]
                    # Attach score and metadata for downstream use
                    chunk_out = dict(chunk)
                    chunk_out["score"] = r.get("score")
                    chunk_out["metadata"] = r.get("metadata")
                    retrieved_chunks.append(chunk_out)
            assert len(retrieved_chunks) > 0 or len(self._chunk_store) == 0, "No chunks mapped from FAISS results!"
            return retrieved_chunks
        except Exception as ex:
            logger.exception("Vector store query failed: %s", ex)
            return []

    def delete_document(self, document_id: str) -> None:
        """Remove all vector embeddings associated with a document."""
        try:
            logger.debug("Deleting vectors for document %s", document_id)
            self._store.delete_document_embeddings(document_id)
        except Exception as ex:
            logger.exception("Failed to delete document embeddings: %s", ex)
