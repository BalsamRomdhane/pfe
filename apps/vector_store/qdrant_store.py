"""Qdrant vector store implementation."""

from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from .base_vector_store import BaseVectorStore


class QdrantStore(BaseVectorStore):
    """Qdrant backend for vector storage."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        url = config.get("url", "http://localhost:6333")
        api_key = config.get("api_key") or None
        collection = config.get("collection", "compliance_vectors")
        self.collection_name = collection
        self.client = QdrantClient(url=url, api_key=api_key)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self.collection_name not in [c.name for c in self.client.get_collections().result]:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(size=384, distance=qmodels.Distance.COSINE),
            )

    def add_embeddings(self, vectors: List[Dict[str, Any]]) -> None:
        if not vectors:
            return

        payloads = []
        ids = []
        vectors_data = []

        for item in vectors:
            ids.append(str(item["id"]))
            vectors_data.append(item["vector"])
            metadata = item.get("metadata", {})
            payloads.append(metadata)

        self.client.upsert(
            collection_name=self.collection_name,
            points=qmodels.PointsList(
                points=[
                    qmodels.PointStruct(id=i, vector=v, payload=p)
                    for i, v, p in zip(ids, vectors_data, payloads)
                ]
            ),
        )

    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
        )
        items: List[Dict[str, Any]] = []
        for hit in result:
            items.append(
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "metadata": hit.payload or {},
                }
            )
        return items

    def delete_document_embeddings(self, document_id: str) -> None:
        # Delete all vectors whose payload contains document_id
        self.client.delete(
            collection_name=self.collection_name,
            filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=document_id),
                    )
                ]
            ),
        )
