"""Hybrid retrieval using embedding similarity + BM25 lexical matching.

This module provides a deterministic retrieval mechanism that combines semantic
search (vector similarity) with lexical relevance (BM25) to find the best
candidate chunks supporting a compliance requirement.

Hybrid score:
    hybrid_score = 0.6 * embedding_similarity + 0.4 * bm25_score

The BM25 component is computed over the candidate pool returned by the vector
store to keep the computation bounded and deterministic.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from services.embedding_service import embed_text
from services.vector_store import VectorStore


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer."""
    if not text:
        return []
    # Remove punctuation and normalize whitespace
    cleaned = re.sub(r"[\W_]+", " ", text.lower())
    tokens = [t for t in cleaned.split() if t]
    return tokens


def _compute_idf(corpus_tokens: List[List[str]]) -> Dict[str, float]:
    """Compute IDF for terms in the provided corpus."""
    n_docs = len(corpus_tokens)
    df = Counter()
    for doc_tokens in corpus_tokens:
        unique = set(doc_tokens)
        df.update(unique)

    idf: Dict[str, float] = {}
    for term, doc_freq in df.items():
        # Standard BM25 IDF with smoothing
        idf_value = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
        idf[term] = max(idf_value, 0.0)
    return idf


def _bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    idf: Dict[str, float],
    avgdl: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Compute BM25 score between a query and a document."""

    if not query_tokens or not doc_tokens:
        return 0.0

    doc_len = len(doc_tokens)
    term_freqs = Counter(doc_tokens)
    score = 0.0

    for term in query_tokens:
        if term not in idf:
            continue
        tf = term_freqs.get(term, 0)
        if tf == 0:
            continue

        term_idf = idf.get(term, 0.0)
        denom = tf + k1 * (1 - b + b * (doc_len / avgdl))
        score += term_idf * ((tf * (k1 + 1)) / denom)

    return float(score)


def _normalize_scores(scores: List[float]) -> List[float]:
    """Normalize a list of scores to 0-1 range."""
    if not scores:
        return []
    mini = min(scores)
    maxi = max(scores)
    if maxi <= mini:
        # Avoid division by zero; return 1.0 for all scores when constant.
        return [1.0 for _ in scores]
    return [(s - mini) / (maxi - mini) for s in scores]


class HybridRetriever:
    """Hybrid retriever combining semantic search and BM25 lexical search."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_weight: float = 0.6,
        bm25_weight: float = 0.4,
        top_k: int = 8,
        candidate_multiplier: int = 3,
    ):
        self.vector_store = vector_store or VectorStore()
        self.embedding_weight = embedding_weight
        self.bm25_weight = bm25_weight
        self.top_k = top_k
        self.candidate_multiplier = candidate_multiplier

    def retrieve(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
        document_language: Optional[str] = None,
    ) -> List[Dict[str, any]]:
        """Retrieve the top-k passages for a query using hybrid scoring, with optional translation for multilingual support."""
        from services.translation_service import translate_to_french
        print("===== RETRIEVAL =====")
        print("QUERY:", query)
        # Translate query to French if document language is French
        if document_language == "fr":
            print("Translating query to French for semantic retrieval...")
            query = translate_to_french(query)
            print("Translated QUERY:", query)
        if not query:
            print("ERROR: Empty query for retrieval")
            return []

        top_k = top_k or self.top_k

        # 1) Semantic search using vector store
        # Always use BGE query prefix and normalization
        import numpy as np
        if not query.strip().lower().startswith("query:"):
            query_text = "query: " + query
        else:
            query_text = query
        query_embedding = embed_text(query_text)
        # Ensure float32 and correct shape for FAISS
        if not isinstance(query_embedding, np.ndarray):
            query_embedding = np.array(query_embedding, dtype="float32")
        else:
            query_embedding = query_embedding.astype("float32")
        print("EMBEDDING DIM:", len(query_embedding))
        if hasattr(self.vector_store, '_store') and hasattr(self.vector_store._store, '_index'):
            print("FAISS DIM:", getattr(self.vector_store._store._index, 'd', 'N/A'))
        candidates = self.vector_store.query(
            query_embedding, top_k=top_k * self.candidate_multiplier
        )
        print("CANDIDATE COUNT:", len(candidates))

        # 2) Filter by document if requested
        if document_id:
            candidates = [c for c in candidates if c.get("metadata", {}).get("document_id") == str(document_id)]

        if not candidates:
            print("ERROR: No candidates found for retrieval")
            return []

        # Prepare tokenized texts
        corpus_tokens = []
        for c in candidates:
            text = str(c.get("metadata", {}).get("text") or c.get("metadata", {}).get("chunk_text") or "")
            # Always use BGE passage prefix for chunk embedding
            t = text.strip()
            if not t.lower().startswith("passage:"):
                t = "passage: " + t
            corpus_tokens.append(_tokenize(t))

        query_tokens = _tokenize(query)
        idf = _compute_idf(corpus_tokens)

        # Average document length for BM25
        avgdl = float(sum(len(t) for t in corpus_tokens) / len(corpus_tokens)) if corpus_tokens else 1.0

        embedding_scores = [float(c.get("score") or 0.0) for c in candidates]
        bm25_scores: List[float] = []

        for tokens in corpus_tokens:
            bm25_scores.append(_bm25_score(query_tokens, tokens, idf, avgdl))

        # Normalize both score sets to 0-1
        norm_embedding = _normalize_scores(embedding_scores)
        norm_bm25 = _normalize_scores(bm25_scores)

        hybrid_scores = []
        for emb, bm25 in zip(norm_embedding, norm_bm25):
            hybrid_scores.append(
                (self.embedding_weight * emb) + (self.bm25_weight * bm25)
            )

        print("SIMILARITY SCORES:", embedding_scores)
        print("BM25 SCORES:", bm25_scores)
        print("HYBRID SCORES:", hybrid_scores)
        if all(score == 0 for score in embedding_scores):
            print("ERROR: Retrieval failed, all similarity scores are zero")

        # Attach hybrid score and return top_k
        results = []
        for c, emb, bm25, hybrid_score in zip(candidates, norm_embedding, norm_bm25, hybrid_scores):
            metadata = c.get("metadata", {})
            results.append(
                {
                    "id": c.get("id"),
                    "document_id": metadata.get("document_id"),
                    "chunk_id": metadata.get("chunk_id"),
                    "section_title": metadata.get("section_title"),
                    "section_index": metadata.get("section_index"),
                    "text": metadata.get("text") or metadata.get("chunk_text"),
                    "score": float(emb),
                    "embedding_score": float(emb),
                    "bm25_score": float(bm25),
                    "hybrid_score": float(hybrid_score),
                    "vector_score": float(emb),
                }
            )

        results = sorted(results, key=lambda r: r["hybrid_score"], reverse=True)
        print("TOP CHUNKS:", results[:top_k])
        return results[:top_k]
