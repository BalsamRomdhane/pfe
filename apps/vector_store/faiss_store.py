"""FAISS vector store implementation."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from services.embedding_service import get_embedding_dimension
from .base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)



class FAISSStore(BaseVectorStore):
    def reset_store(self):
        self._create_index()
    """FAISS backend for vector storage."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.index_path = config.get("persist_path", os.path.abspath("./vector_store/faiss.index"))
        self.metadata_path = f"{self.index_path}.meta.json"
        # Ensure the FAISS dimensionality matches the embedding model.
        self.dimension = config.get("dimension") or get_embedding_dimension()
        self._index = None
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._ids: List[str] = []
        self._load()

    def _load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self._index = faiss.read_index(self.index_path)

                # If the stored index has a different dimensionality than the current
                # embedding model, rebuild it to avoid assertion errors during queries.
                if hasattr(self._index, 'd') and self._index.d != self.dimension:
                    logger.warning(
                        "FAISS index dimension (%d) does not match embedding model dimension (%d). Recreating index.",
                        getattr(self._index, 'd', -1),
                        self.dimension,
                    )
                    self._create_index()
                    return

                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._metadata = data.get("metadata", {})
                    self._ids = data.get("ids", [])
            except Exception:
                self._create_index()
        else:
            self._create_index()

    def _create_index(self):
        self._index = faiss.IndexFlatIP(self.dimension)
        self._metadata = {}
        self._ids = []

    def _persist(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self._index, self.index_path)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump({"ids": self._ids, "metadata": self._metadata}, f)

    def add_embeddings(self, vectors: List[Dict[str, Any]]) -> None:
        if not vectors:
            return
        vectors_np = []
        for item in vectors:
            vector = np.array(item.get("vector", []), dtype="float32")

            # Skip invalid embeddings
            if vector.size == 0 or len(vector) != self.dimension:
                logger.warning(
                    "Skipping embedding for id %s: expected dimension %d but got %d",
                    item.get("id"),
                    self.dimension,
                    len(vector),
                )
                continue

            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            vectors_np.append(vector)
            idx = str(item["id"])
            self._ids.append(idx)
            metadata = dict(item.get("metadata", {}))
            metadata["vector"] = vector.tolist()
            metadata["document_id"] = metadata.get("document_id") or item.get("metadata", {}).get("document_id")
            self._metadata[idx] = metadata

        if not vectors_np:
            logger.warning("No valid embeddings to add to FAISS index.")
            return

        matrix = np.vstack(vectors_np).astype("float32")
        self._index.add(matrix)
        self._persist()

    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if self._index is None or self._index.ntotal == 0:
            return []

        query_vec = np.array(query_vector, dtype="float32")
        # Ensure 2D shape for FAISS (1, dim)
        if len(query_vec.shape) == 1:
            query_vec = query_vec.reshape(1, -1)
        print("QUERY SHAPE:", query_vec.shape)
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec /= norm

        # If already 2D, don't expand dims again
        query_mat = query_vec if len(query_vec.shape) == 2 else np.expand_dims(query_vec, axis=0)
        distances, indices = self._index.search(query_mat, top_k)
        print("INDICES:", indices)
        print("DISTANCES:", distances)

        top_chunks = [self._ids[i] for i in indices[0] if i != -1 and i < len(self._ids)]
        print("TOP CHUNKS:", top_chunks)

        results: List[Dict[str, Any]] = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._ids):
                continue
            key = self._ids[idx]
            metadata = self._metadata.get(key, {})
            results.append({"id": key, "score": float(score), "metadata": metadata})
        # If there are chunks in the index but results is empty, return all chunks (fail-safe)
        if not results and len(self._ids) > 0:
            print("WARNING: No results from FAISS but chunks exist. Returning all chunks.")
            for idx, key in enumerate(self._ids):
                metadata = self._metadata.get(key, {})
                results.append({"id": key, "score": 0.0, "metadata": metadata})
        return results

    def delete_document_embeddings(self, document_id: str) -> None:
        # FAISS does not support deletion in IndexFlat; rebuild from scratch.
        remaining_ids = [i for i in self._ids if self._metadata.get(i, {}).get("document_id") != document_id]
        remaining_vectors = []
        for idx in remaining_ids:
            metadata = self._metadata.get(idx, {})
            vec = metadata.get("vector")
            if vec is not None:
                remaining_vectors.append(np.array(vec, dtype="float32"))

        self._create_index()
        self._ids = remaining_ids
        # rebuild index
        if remaining_vectors:
            matrix = np.vstack(remaining_vectors)
            self._index.add(matrix)
        self._persist()
