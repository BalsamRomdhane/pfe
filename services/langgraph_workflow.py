"""LangGraph workflow definition for the compliance audit pipeline.

This module provides a LangGraph StateGraph where each node corresponds to a
stage in the compliance audit workflow. It enables explicit tracing and
visualization of the pipeline, while reusing the underlying audit pipeline
implementation.
"""

from typing import Any, Dict

from langgraph.graph import START, StateGraph

from services.audit_pipeline import AuditPipeline


class LangGraphAuditWorkflow:
    """A LangGraph workflow for compliance auditing.

    Each node corresponds to a stage in the compliance audit workflow. The graph
    is primarily used for traceable orchestration and visualization.
    """

    def __init__(self):
        self.pipeline = AuditPipeline()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)

        # Define nodes for each major pipeline stage
        graph.add_node("parse_document", self._parse_document)
        graph.add_node("chunk_document", self._chunk_document)
        graph.add_node("retrieve_chunks", self._retrieve_chunks)
        graph.add_node("rerank_chunks", self._rerank_chunks)
        graph.add_node("detect_evidence", self._detect_evidence)
        graph.add_node("evaluate_compliance", self._evaluate_compliance)
        graph.add_node("score_results", self._score_results)
        graph.add_node("audit_results", self._audit_results)
        graph.add_node("format_report", self._format_report)

        graph.add_edge(START, "parse_document")
        graph.add_edge("parse_document", "chunk_document")
        graph.add_edge("chunk_document", "retrieve_chunks")
        graph.add_edge("retrieve_chunks", "rerank_chunks")
        graph.add_edge("rerank_chunks", "detect_evidence")
        graph.add_edge("detect_evidence", "evaluate_compliance")
        graph.add_edge("evaluate_compliance", "score_results")
        graph.add_edge("score_results", "audit_results")
        graph.add_edge("audit_results", "format_report")

        return graph.compile()

    def run(self, document: Any, standard: Any) -> Dict[str, Any]:
        """Execute the LangGraph workflow for a given document and standard."""
        state: Dict[str, Any] = {"document": document, "standard": standard}
        result = self.graph.invoke(state)
        return result.get("report", {})

    # Nodes
    def _parse_document(self, state: Dict[str, Any]) -> Dict[str, Any]:
        parsed = self.pipeline.parser.parse_document(state.get("document"))
        state["parsed"] = parsed
        state["document_text"] = parsed.get("text", "")
        return state

    def _chunk_document(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["chunks"] = self.pipeline.chunker.chunk_with_overlap(state.get("document_text", ""))
        return state

    def _retrieve_chunks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform hybrid retrieval for each requirement in the standard."""
        # Delegate to the audit pipeline for retrieval and evaluation.
        # This node is mainly for structural graph clarity.
        return state

    def _rerank_chunks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def _detect_evidence(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def _evaluate_compliance(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Perform the full audit and attach to the state
        state["report"] = self.pipeline.run(state.get("document"), state.get("standard"))
        return state

    def _score_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def _audit_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def _format_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state
