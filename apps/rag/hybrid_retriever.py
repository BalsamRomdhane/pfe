"""Hybrid retrieval combining vector similarity and BM25 keyword search.

This module provides a hybrid retrieval strategy that combines:
1. Vector embeddings (semantic similarity)
2. BM25 keyword search (lexical relevance)

Results are ranked using a weighted combination of both methods.
"""

import re
from typing import List, Dict, Tuple
from collections import Counter
from apps.rag.embedding_service import get_embedding_service
from apps.rag.retriever import Retriever


class HybridRetriever:
    """Hybrid retrieval combining vector search and BM25 keyword search."""

    def __init__(self, vector_weight: float = 0.6, bm25_weight: float = 0.4):
        """Initialize hybrid retriever.
        
        Args:
            vector_weight: Weight for vector similarity scores (0-1)
            bm25_weight: Weight for BM25 keyword scores (0-1)
        """
        self.embedding_service = get_embedding_service()
        self.vector_retriever = Retriever()
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        
        # Ensure weights sum to 1
        total = vector_weight + bm25_weight
        self.vector_weight = vector_weight / total
        self.bm25_weight = bm25_weight / total

    def hybrid_search(
        self,
        query: str,
        chunks: List[str],
        top_k: int = 5,
        use_vector: bool = True,
        use_bm25: bool = True
    ) -> List[Dict[str, any]]:
        """Perform hybrid search combining vector and keyword methods.
        
        Args:
            query: Search query
            chunks: List of document chunks to search within
            top_k: Number of top results to return
            use_vector: Whether to use vector similarity
            use_bm25: Whether to use BM25 keyword search
            
        Returns:
            List of top-k ranked chunks with scores
        """
        if not query or not chunks:
            return []

        scores = {}  # chunk_index -> combined_score

        # Vector search
        if use_vector:
            vector_scores = self._vector_search(query, chunks)
            for idx, score in vector_scores.items():
                scores[idx] = scores.get(idx, 0) + self.vector_weight * score

        # BM25 keyword search
        if use_bm25:
            bm25_scores = self._bm25_search(query, chunks)
            for idx, score in bm25_scores.items():
                scores[idx] = scores.get(idx, 0) + self.bm25_weight * score

        # Rank by combined score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in ranked[:top_k]:
            results.append({
                "chunk": chunks[idx],
                "index": idx,
                "hybrid_score": score,
                "chunk_length": len(chunks[idx].split())
            })

        return results

    def _vector_search(self, query: str, chunks: List[str]) -> Dict[int, float]:
        """Perform vector similarity search.
        
        Returns:
            Dictionary mapping chunk indices to similarity scores (0-1)
        """
        try:
            query_embedding = self.embedding_service.embed_text(query)
            chunk_embeddings = self.embedding_service.embed_texts(chunks)
            
            scores = {}
            for idx, chunk_emb in enumerate(chunk_embeddings):
                similarity = self._cosine_similarity(query_embedding, chunk_emb)
                if similarity > 0:
                    scores[idx] = similarity
            
            return scores
        except Exception as e:
            print(f"Vector search error: {e}")
            return {}

    def _bm25_search(self, query: str, chunks: List[str]) -> Dict[int, float]:
        """Perform BM25 keyword search.
        
        BM25 is a probabilistic relevance ranking function that combines:
        - Term frequency in document
        - Inverse document frequency
        - Document length normalization
        
        Returns:
            Dictionary mapping chunk indices to BM25 scores (0-1 normalized)
        """
        try:
            bm25 = BM25(chunks)
            query_terms = self._tokenize(query)
            scores_raw = bm25.get_scores(query_terms)
            
            # Normalize to 0-1
            max_score = max(scores_raw) if scores_raw else 1
            if max_score == 0:
                max_score = 1
            
            scores = {}
            for idx, score in enumerate(scores_raw):
                normalized_score = score / max_score
                if normalized_score > 0:
                    scores[idx] = normalized_score
            
            return scores
        except Exception as e:
            print(f"BM25 search error: {e}")
            return {}

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(y * y for y in b) ** 0.5
        
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        return dot / (mag_a * mag_b)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text into lowercase terms."""
        # Remove punctuation and split on whitespace
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens


class BM25:
    """BM25 ranking algorithm for keyword search.
    
    Reference: Okapi BM25 - a probabilistic information retrieval model.
    """
    
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        """Initialize BM25.
        
        Args:
            corpus: List of documents (chunks)
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_freqs = []
        self.idf = {}
        self.doc_lengths = []
        self.avgdl = 0
        
        self._build_index()

    def _build_index(self) -> None:
        """Build the BM25 index from the corpus."""
        vocabulary = set()
        
        # Tokenize and collect vocabulary
        for doc in self.corpus:
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            
            doc_freq = {}
            for term in tokens:
                vocabulary.add(term)
                doc_freq[term] = doc_freq.get(term, 0) + 1
            
            self.doc_freqs.append(doc_freq)
        
        # Calculate average document length
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        
        # Calculate IDF for each term
        num_docs = len(self.corpus)
        for term in vocabulary:
            docs_with_term = sum(1 for doc_freq in self.doc_freqs if term in doc_freq)
            # IDF formula: log((N - n + 0.5) / (n + 0.5) + 1)
            idf = max(0, (num_docs - docs_with_term + 0.5) / (docs_with_term + 0.5))
            self.idf[term] = idf

    def get_scores(self, query_terms: List[str]) -> List[float]:
        """Calculate BM25 scores for all documents in the corpus.
        
        Args:
            query_terms: List of query terms
            
        Returns:
            List of BM25 scores (one per document in corpus)
        """
        scores = []
        
        for i, doc_freq in enumerate(self.doc_freqs):
            score = 0.0
            doc_length = self.doc_lengths[i]
            
            for term in query_terms:
                if term in doc_freq:
                    term_freq = doc_freq[term]
                    idf = self.idf.get(term, 0)
                    
                    # BM25 formula
                    numerator = idf * term_freq * (self.k1 + 1)
                    denominator = term_freq + self.k1 * (
                        1 - self.b + self.b * (doc_length / self.avgdl)
                    )
                    
                    score += numerator / denominator
            
            scores.append(score)
        
        return scores

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text into lowercase terms."""
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
