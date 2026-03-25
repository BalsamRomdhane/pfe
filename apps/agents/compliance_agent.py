"""Agent that checks document compliance against defined controls.

This module uses semantic retrieval and an LLM evaluation step to improve
reliability and explainability. It is designed to work with a vector store
backed by sentence embeddings.
"""

import logging
import re
from typing import Dict, List, Optional

from apps.compliance.services.llm_evaluator import LLMEvaluator
from apps.compliance.services.violation_detector import ViolationDetector
from apps.rag.embedding_service import get_embedding_service
from apps.rag.retriever import Retriever
from apps.standards.models import Standard

logger = logging.getLogger(__name__)


# Default weights used for scoring based on severity
_SEVERITY_WEIGHTS = {
    "critical": 5,
    "major": 3,
    "minor": 1,
}

# Mapping of compliance status to a normalized score multiplier
_STATUS_SCORES = {
    "compliant": 1.0,
    "partially_compliant": 0.5,
    "uncertain": 0.3,
    "missing": 0.0,
    "non_compliant": 0.0,
}


class ComplianceAgent:
    """Evaluates whether a document adheres to a compliance standard."""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.retriever = Retriever()
        self.llm = LLMEvaluator()
        self.violation_detector = ViolationDetector()

    def assess(self, parsed_document: Dict, standard: Standard) -> Dict:
        """Assess document compliance against each control in the standard."""
        document_text = (parsed_document.get("text") or "").strip()
        document_id = str(parsed_document.get("document_id", parsed_document.get("id", "")))

        control_results: List[Dict] = []
        for control in standard.controls.all():
            control_results.append(self._evaluate_control(control, document_id, document_text))

        score = self.compute_score(control_results)
        violations = [
            r["summary"]
            for r in control_results
            if r["status"] in ("non_compliant", "missing")
        ]
        violation_details = [
            r for r in control_results if r["status"] in ("non_compliant", "missing")
        ]

        return {
            "score": score,
            "rules": control_results,
            "violations": violations,
            "violation_details": violation_details,
        }

    def _evaluate_control(self, control, document_id: str, document_text: str) -> Dict:
        """Evaluate a single control using semantic retrieval + LLM reasoning."""
        requirement = control.description or ""
        query_text = "\n".join(filter(None, [control.objective or "", requirement]))

        # Retrieve relevant chunks using the vector store
        query_embedding = self.embedding_service.embed_text(query_text)
        relevant_chunks = self.retriever.query(query_embedding, top_k=5)

        # Collect text and scores
        evidence_texts = [c.get("chunk_text", "") for c in relevant_chunks if c.get("chunk_text")]
        avg_score = 0.0
        if relevant_chunks:
            avg_score = sum((c.get("score") or 0.0) for c in relevant_chunks) / len(relevant_chunks)

        # LLM evaluation for compliance decision
        llm_result = self.llm.evaluate(requirement, evidence_texts)
        status = llm_result.get("status", "uncertain")
        if status not in _STATUS_SCORES:
            status = "uncertain"

        # If no evidence was found, mark as missing
        if not evidence_texts or status in (None, "", "missing"):
            status = "missing"

        # Detect explicit negation / contradiction
        if any(self._detect_negation(t) for t in evidence_texts):
            status = "non_compliant"

        # Calculate scores and severity
        severity = control.severity if hasattr(control, "severity") else "major"
        weight = _SEVERITY_WEIGHTS.get(severity, 3)

        # Determine a readable summary
        summary = f"{control.identifier or control.description[:40]}: {status}"

        # Violation detection heuristics
        violation_info = self.violation_detector.detect_violations(
            document_text, requirement, is_critical_control=(severity == "critical")
        )

        return {
            "rule_id": control.identifier or f"control_{control.pk}",
            "description": requirement,
            "objective": getattr(control, "objective", ""),
            "severity": severity,
            "status": status,
            "evidence": evidence_texts,
            "average_similarity_score": avg_score,
            "llm_confidence": llm_result.get("confidence", 0.0),
            "reasoning": llm_result.get("reasoning", ""),
            "summary": summary,
            "weight": weight,
            "violation_info": violation_info,
        }

    @staticmethod
    def _detect_negation(text: str) -> bool:
        """Detect whether the text contains negation patterns."""
        if not text:
            return False

        s = text.lower()
        negation_patterns = [
            r"\bno\b",
            r"\bnot\b",
            r"\bnone\b",
            r"\bnever\b",
            r"\bdoes not\b",
            r"\bdoesn't\b",
            r"\bdid not\b",
            r"\bdidn't\b",
            r"\bwas not\b",
            r"\bwasn't\b",
            r"\bhas not\b",
            r"\bhasn't\b",
            r"\bhave not\b",
            r"\bhaven't\b",
            r"\bcannot\b",
            r"\bcan't\b",
            r"\bwithout\b",
            r"\bmissing\b",
            r"\babsence of\b",
        ]
        return any(re.search(pattern, s) for pattern in negation_patterns)

    @staticmethod
    def compute_score(control_results: List[Dict]) -> int:
        """Compute a normalized compliance score (0-100) from control evaluations."""
        if not control_results:
            return 0

        total_weight = sum(r.get("weight", 0) for r in control_results)
        if total_weight <= 0:
            return 0

        weighted_sum = 0.0
        for r in control_results:
            status = r.get("status")
            weight = r.get("weight", 0)
            multiplier = _STATUS_SCORES.get(status, 0.0)
            weighted_sum += weight * multiplier

        score = int(round((weighted_sum / total_weight) * 100))
        return max(0, min(100, score))
