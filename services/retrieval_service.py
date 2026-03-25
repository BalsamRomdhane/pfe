"""Evidence retrieval layer using a hybrid semantic + lexical strategy.

This module is responsible for generating query embeddings for compliance
requirements and retrieving the most relevant document chunks using a hybrid
approach that combines embedding similarity and BM25 lexical scoring.
"""

import hashlib
import logging
from typing import Dict, List, Optional

from django.core.cache import cache

from services.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


def _cache_key_for_rule(rule_id: str, query: str, top_k: int, document_id: Optional[str] = None) -> str:
    digest = hashlib.sha256(query.encode("utf-8", errors="ignore")).hexdigest()
    base = f"retrieval:{rule_id}:{digest}:{top_k}"
    if document_id:
        base += f":{document_id}"
    return base


class RetrievalService:
    """Service to retrieve evidence chunks for compliance rules."""

    def __init__(self, hybrid_retriever: Optional[HybridRetriever] = None):
        self.hybrid_retriever = hybrid_retriever or HybridRetriever()

    def retrieve_evidence(
        self,
        rule_id: str,
        rule_text: str,
        document_id: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_k: int = 5,
        use_cache: bool = True,
    ) -> List[Dict[str, any]]:
        """Retrieve the most relevant chunks for a compliance rule.

        This uses a hybrid retrieval strategy combining semantic similarity and
        BM25 lexical relevance.
        """
        if not rule_text:
            return []

        query = rule_text
        if keywords:
            query = "\n".join([rule_text] + keywords)

        cache_key = _cache_key_for_rule(rule_id, query, top_k, document_id)
        if use_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Retrieval cache hit for rule %s", rule_id)
                return cached

        candidates = self.hybrid_retriever.retrieve(
            query=query, document_id=document_id, top_k=top_k
        )

        if use_cache:
            cache.set(cache_key, candidates, timeout=60 * 5)

        return candidates
