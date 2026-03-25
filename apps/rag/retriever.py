"""Retrieval utilities using the configured vector store."""

from typing import List, Dict

from apps.vector_store import get_vector_store


class Retriever:
    """Retrieves relevant chunks for a query using the configured vector store."""

    def __init__(self):
        self.store = get_vector_store()

    def add_chunks(self, document_id: str, chunks: List, embeddings: List[List[float]]) -> None:
        """Add a list of chunks with embeddings to the vector store.

        Chunks can be either plain text strings (legacy) or structured dicts containing:
            - text
            - section_title
            - section_index
            - chunk_index
        """
        vectors = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            if isinstance(chunk, dict):
                metadata = {
                    "document_id": document_id,
                    "chunk_text": chunk.get("text", ""),
                    "section_title": chunk.get("section_title"),
                    "section_index": chunk.get("section_index"),
                    "chunk_index": chunk.get("chunk_index"),
                }
            else:
                metadata = {"document_id": document_id, "chunk_text": chunk}

            vectors.append(
                {
                    "id": f"{document_id}_{idx}",
                    "vector": vector,
                    "metadata": metadata,
                }
            )
        self.store.add_embeddings(vectors)

    def query(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, any]]:
        """Return a list of the most relevant chunks.

        Each result contains the stored metadata plus the semantic score.
        """
        results = self.store.similarity_search(query_vector, top_k=top_k)
        return [
            {
                **r.get("metadata", {}),
                "score": r.get("score"),
                "id": r.get("id"),
            }
            for r in results
        ]

    def delete_document(self, document_id: str) -> None:
        self.store.delete_document_embeddings(document_id)
