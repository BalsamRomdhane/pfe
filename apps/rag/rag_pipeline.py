"""Retrieval Augmented Generation (RAG) pipeline with hybrid retrieval.

This module provides an enhanced RAG pipeline with:
- Hybrid retrieval (vector + keyword search)
- Multi-source context gathering
- Related control retrieval from knowledge graph
- Guidance text integration
"""

from typing import List, Dict, Optional

from apps.documents.models import Document
from .embedding_service import get_embedding_service
from .retriever import Retriever
from .hybrid_retriever import HybridRetriever


class RAGPipeline:
    """Enhanced RAG pipeline with hybrid retrieval for compliance analysis."""

    def __init__(self):
        # Reuse a shared embedding model instance to reduce load time.
        self.embedding_service = get_embedding_service()
        self.retriever = Retriever()
        self.hybrid_retriever = HybridRetriever(
            vector_weight=0.6,
            bm25_weight=0.4
        )

    def answer_question(self, document: Document, question: str) -> str:
        """Return an answer to a question based on the document content."""
        if not document.text:
            return "No content available for this document."

        # Use hybrid retrieval for better results
        chunks = self._get_document_chunks(document)
        results = self.hybrid_retriever.hybrid_search(
            query=question,
            chunks=chunks,
            top_k=5
        )

        context = "\n\n".join([r.get("chunk", "") for r in results])
        # In a full system, we'd call an LLM here. We return a placeholder response.
        return (
            "Based on the document, the most relevant sections are:\n"
            f"{context}\n\n"
            "(This response is a placeholder; integrate an LLM for production use.)"
        )

    def retrieve_similar_chunks(self, document: Document, query: str, top_k: int = 5) -> List[str]:
        """Retrieve similar chunks using vector search."""
        query_vector = self.embedding_service.embed_text(query)
        results = self.retriever.query(query_vector, top_k=top_k)
        return [r.get("chunk", "") for r in results]

    def retrieve_control_context(
        self,
        document: Document,
        control_description: str,
        top_k: int = 5
    ) -> Dict[str, any]:
        """Retrieve comprehensive context for control evaluation.
        
        Returns:
            Dictionary with:
            - document_chunks: Top document chunks related to control
            - related_controls: Related controls from knowledge graph
            - guidance: Guidance text for the control
            - procedures: Extracted procedures from document
        """
        if not document.text:
            return self._empty_context()

        context = {
            "control_description": control_description,
            "document_chunks": [],
            "related_controls": [],
            "guidance": [],
            "procedures": [],
            "total_context_length": 0
        }

        # 1. Get document chunks using hybrid retrieval
        chunks = self._get_document_chunks(document)
        hybrid_results = self.hybrid_retriever.hybrid_search(
            query=control_description,
            chunks=chunks,
            top_k=top_k
        )
        
        context["document_chunks"] = [
            {
                "text": r.get("chunk", ""),
                "score": r.get("hybrid_score", 0),
                "length": r.get("chunk_length", 0)
            }
            for r in hybrid_results
        ]

        # 2. Get related controls from knowledge graph (if available)
        context["related_controls"] = self._get_related_controls(control_description)

        # 3. Get guidance for this control type
        context["guidance"] = self._get_control_guidance(control_description)

        # 4. Extract procedures from document
        context["procedures"] = self._extract_procedures(document.text, control_description)

        # Calculate total context length
        context["total_context_length"] = sum(
            len(chunk["text"].split())
            for chunk in context["document_chunks"]
        )

        return context

    def retrieve_evidence_for_control(
        self,
        document: Document,
        control_description: str,
        top_k: int = 5
    ) -> List[Dict[str, any]]:
        """Retrieve evidence sentences for a specific control.
        
        Returns:
            List of evidence chunks with metadata
        """
        if not document.text:
            return []

        # Use hybrid retrieval to find relevant chunks
        chunks = self._get_document_chunks(document)
        results = self.hybrid_retriever.hybrid_search(
            query=control_description,
            chunks=chunks,
            top_k=top_k,
            use_vector=True,
            use_bm25=True
        )

        evidence = []
        for result in results:
            evidence.append({
                "text": result.get("chunk", ""),
                "relevance_score": result.get("hybrid_score", 0),
                "source": "document_analysis"
            })

        return evidence

    # Private helper methods

    def _get_document_chunks(self, document: Document) -> List[str]:
        """Get all chunks from document, using semantic chunking if available."""
        if not document.text:
            return []

        try:
            # Try to use semantic chunking for better results
            from apps.documents.services.semantic_chunker import SemanticChunker
            
            chunker = SemanticChunker()
            chunk_objects = chunker.chunk(document.text)
            return [chunk["content"] for chunk in chunk_objects]
        except Exception:
            # Fallback to simple chunking
            from apps.documents.services.document_processor import chunk_text
            
            return chunk_text(document.text, chunk_size=500, overlap=50)

    def _get_related_controls(self, control_description: str) -> List[Dict[str, str]]:
        """Get related controls from knowledge graph.
        
        This is a placeholder for Neo4j integration in the future.
        """
        # TODO: Integrate with Neo4j knowledge graph
        return []

    def _get_control_guidance(self, control_description: str) -> List[str]:
        """Get guidance text for a control type.
        
        This would be sourced from a guidance knowledge base.
        """
        # Placeholder for guidance integration
        guidance_keywords = ["policy", "procedure", "responsibility", "review"]
        
        if any(kw in control_description.lower() for kw in guidance_keywords):
            return [
                "Ensure the requirement is clearly stated in policy documents",
                "Verify roles and responsibilities are assigned",
                "Check that the control includes review or audit procedures"
            ]
        
        return []

    def _extract_procedures(self, document_text: str, control_description: str) -> List[str]:
        """Extract procedures from document related to control."""
        try:
            from apps.documents.services.semantic_chunker import SemanticChunker
            
            chunker = SemanticChunker()
            sections = chunker.extract_sections(document_text)
            
            return sections.get("procedures", [])
        except Exception:
            return []

    def _empty_context(self) -> Dict[str, any]:
        """Return empty context structure."""
        return {
            "control_description": "",
            "document_chunks": [],
            "related_controls": [],
            "guidance": [],
            "procedures": [],
            "total_context_length": 0
        }
