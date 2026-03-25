"""ChromaDB vector store implementation."""

import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from .base_vector_store import BaseVectorStore


class ChromaDBStore(BaseVectorStore):
    """ChromaDB backend for vector storage."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        persist_directory = config.get("persist_directory", os.path.abspath("./vector_store"))
        self.client = chromadb.Client(Settings(persist_directory=persist_directory))
        self.collection = self._get_collection("compliance_vectors")

    def _get_collection(self, name: str):
        if name in [c.name for c in self.client.list_collections()]:
            return self.client.get_collection(name)
        return self.client.create_collection(name)

    def add_embeddings(self, vectors: List[Dict[str, Any]]) -> None:
        ids = [item["id"] for item in vectors]
        embeddings = [item["vector"] for item in vectors]
        metadatas = [item.get("metadata", {}) for item in vectors]
        documents = [item.get("metadata", {}).get("chunk", "") for item in vectors]
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(query_embeddings=[query_vector], n_results=top_k)
        items: List[Dict[str, Any]] = []
        for idx, item_id in enumerate(results["ids"][0]):
            items.append(
                {
                    "id": item_id,
                    "score": results["distances"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "document": results["documents"][0][idx],
                }
            )
        return items

    def delete_document_embeddings(self, document_id: str) -> None:
        """Remove all vectors associated with the given document."""
        try:
            # `ids` is always returned by `get`, even when not specified in include.
            results = self.collection.get(where={"document_id": document_id}, include=["metadatas"])
            ids = results.get("ids", [])
            if ids:
                self.collection.delete(ids=ids)
        except Exception:
            # Some Chroma versions do not support `where` queries; fallback to full scan.
            all_entries = self.collection.get(include=["metadatas"])
            ids_to_delete = [
                i
                for i, m in zip(all_entries.get("ids", []), all_entries.get("metadatas", []))
                if m.get("document_id") == document_id
            ]
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
