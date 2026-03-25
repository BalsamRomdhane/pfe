"""Compliance rule evaluation engine.

This module evaluates individual compliance rules against retrieved evidence.
It combines semantic similarity, reranking, and LLM validation to produce a
transparent, explainable compliance score.
"""

import logging
from dataclasses import dataclass, field
import hashlib
from typing import Any, Dict, List, Optional

from django.core.cache import cache

from services.llm_validator import LLMValidator

logger = logging.getLogger(__name__)


@dataclass
class ComplianceRule:
    id: str
    standard: str
    description: str
    severity: str
    keywords: List[str] = field(default_factory=list)
    expected_evidence: Optional[str] = None
    control_type: Optional[str] = None


@dataclass
class RuleEvaluation:
    rule_id: str
    rule: Dict[str, Any]
    status: str
    severity: str
    score: float
    evidence: List[Any]
    confidence: float
    reason: str
    evidence_strength: str
    evidence_used: Optional[str] = None
    llm_evidence: List[str] = field(default_factory=list)
    recommendation: Optional[str] = None
    # Extended explainability fields
    evidence_score: float = 0.0
    evidence_sentences: List[str] = field(default_factory=list)
    evidence_types: List[str] = field(default_factory=list)
    llm_confidence: float = 0.0
    auditor: Optional[Dict[str, Any]] = None
    final_score: Optional[int] = None
    final_status: Optional[str] = None


# Mapping of core compliance keywords to multilingual equivalents.
# This helps the system match English rule keywords against non-English documents.
MULTILINGUAL_KEYWORD_MAP = {
    "responsibility": ["responsibility", "responsabilité", "responsabilités"],
    "authority": ["authority", "autorité"],
    "define": ["define", "définir", "définition"],
    "must": ["must", "doit", "devra"],
    "mandatory": ["mandatory", "obligatoire"],
    "should": ["should", "devrait", "devraient"],
    "may": ["may", "peut"],
    "required": ["required", "requis", "obligatoire"],
}


class ComplianceEngine:
    """Engine that evaluates compliance rules against retrieved evidence.

    The evaluation is a hybrid multi-layer process:
      1. Keyword validation
      2. Semantic retrieval (embedding similarity)
      3. Logical rule validations (expected evidence checks)
      4. LLM reasoning

    Final compliance decisions are conservative and aimed at minimizing false positives.
    """

    # Use a looser similarity threshold to avoid false negatives when retrieving
    # evidence from documents with varied phrasing.
    MIN_SIMILARITY = 0.5
    STRONG_SIMILARITY = 0.88
    PARTIAL_SIMILARITY = 0.5
    KEYWORD_MATCH_THRESHOLD = 0.6
    LLM_CONFIDENCE_THRESHOLD = 0.4

    def __init__(self, llm_model: Optional[str] = None):
        self.validator = LLMValidator()

    def evaluate_rule(
        self,
        rule: ComplianceRule,
        evidence_chunks: List[Dict[str, Any]],
        evidence_items: Optional[List[Dict[str, Any]]] = None,
    ) -> RuleEvaluation:
        print("===== SCORING =====")
        cache_key = self._get_cache_key(rule.id, evidence_chunks)
        cached = cache.get(cache_key)
        if cached:
            return cached

        valid_evidence = [
            c for c in evidence_chunks if float(c.get("score") or 0.0) >= self.MIN_SIMILARITY
        ]
        top_chunks = sorted(valid_evidence, key=lambda c: float(c.get("score") or 0.0), reverse=True)[:5]
        best_similarity = float(top_chunks[0].get("score") or 0.0) if top_chunks else 0.0

        print("SEMANTIC:", best_similarity)
        print("CHUNK COUNT:", len(evidence_chunks))
        print("TOP CHUNKS:", top_chunks[:2])
        if len(evidence_chunks) == 1:
            print("ERROR: Chunking failed")

        keyword_score = self._compute_keyword_score(rule.keywords, top_chunks)
        print("EVIDENCE SCORE:", keyword_score)
        keywords_present = keyword_score >= self.KEYWORD_MATCH_THRESHOLD

        logical_match = self._check_expected_evidence(rule.expected_evidence, top_chunks)

        # Filter evidence semantically
        positive_evidence = []
        negative_risks = []
        from services.evidence_detector import EvidenceDetector
        
        for candidate in evidence_items or [c.get("text") or "" for c in top_chunks]:
            cls = EvidenceDetector.classify_sentence(candidate)
            if cls == "positive":
                positive_evidence.append(candidate)
            elif cls == "negative":
                negative_risks.append(candidate)
            else:
                # Retain neutral evidence conventionally
                positive_evidence.append(candidate)

        # Skip LLM if no top chunks completely, else proceed securely
        if not top_chunks:
            llm_result = {}
        else:
            llm_result = self.validator.validate(
                {
                    "id": rule.id,
                    "description": rule.description,
                    "severity": rule.severity,
                },
                evidence_items or [c.get("text") or "" for c in top_chunks],
            )

        llm_status = str(llm_result.get("status", "UNKNOWN")).upper() if top_chunks else "UNKNOWN"
        llm_confidence = float(llm_result.get("confidence", 0.0) or 0.0)
        llm_reason = str(llm_result.get("reason", ""))
        evidence_used = str(llm_result.get("evidence_used", ""))
        llm_evidence = llm_result.get("evidence") or []
        if isinstance(llm_evidence, str):
            llm_evidence = [llm_evidence]

        print("LLM CONFIDENCE:", llm_confidence)

        confidence = self._combine_confidence(
            embedding_score=best_similarity,
            keyword_score=keyword_score,
            llm_confidence=llm_confidence,
        )

        status = "unknown"
        reason = llm_reason or ""

        # Status Logic Strict Enforcement
        if negative_risks:
            status = "non_compliant"
            reason = f"Negative evidence found: {negative_risks[0]}"
        elif positive_evidence and best_similarity >= self.PARTIAL_SIMILARITY:
            if best_similarity >= self.STRONG_SIMILARITY:
                status = "compliant"
            else:
                status = "partially_compliant"
        else:
            status = "partially_compliant"
            reason = "No explicit evidence retrieved for this control."
            
        # Scoring Penalty
        penalty = len(negative_risks) * 0.2
        confidence = max(0.0, confidence - penalty)

        if not top_chunks:
            confidence = 0.0
            
        if status == "non_compliant":
            confidence = min(confidence, 0.4)

        best_chunk = top_chunks[0] if top_chunks else {}
        evidence_snippet = (best_chunk.get("text") or "")[:512]
        source_chunk = {
            "chunk_id": best_chunk.get("chunk_id") or best_chunk.get("id"),
            "section_title": best_chunk.get("section_title"),
            "section_index": best_chunk.get("section_index"),
            "similarity": best_similarity,
        }

        missing = []
        if status != "compliant" and not negative_risks:
            missing = ["Explicit control evidence"]

        recommendation = self.generate_recommendation(missing, negative_risks)

        evaluation = RuleEvaluation(
            rule_id=rule.id,
            rule={
                "id": rule.id,
                "standard": rule.standard,
                "description": rule.description,
                "severity": rule.severity,
                "expected_evidence": rule.expected_evidence,
                "keywords": rule.keywords,
                "control_type": rule.control_type,
            },
            status=status,
            severity=rule.severity,
            score=best_similarity,
            evidence=evidence_items if evidence_items is not None else top_chunks,
            confidence=confidence,
            reason=reason,
            evidence_strength=(
                "strong"
                if best_similarity >= self.STRONG_SIMILARITY
                else "partial"
                if best_similarity >= self.PARTIAL_SIMILARITY
                else "none"
            ),
            evidence_used=evidence_used,
            llm_evidence=llm_evidence,
            llm_confidence=llm_confidence,
            recommendation=recommendation,
        )

        evaluation.rule["keyword_score"] = keyword_score
        evaluation.rule["logical_match"] = logical_match
        evaluation.rule["evidence_snippet"] = evidence_snippet
        evaluation.rule["source_chunk"] = source_chunk
        evaluation.rule["recommendation"] = recommendation

        cache.set(cache_key, evaluation, timeout=60 * 5)
        return evaluation

    def _compute_keyword_score(self, keywords: List[str], chunks: List[Dict[str, Any]]) -> float:
        """Compute a keyword match score using multilingual keyword mappings."""
        if not keywords:
            return 1.0

        text = "\n\n".join([c.get("text", "") for c in chunks]).lower()
        if not text:
            return 0.0

        found = 0
        for kw in keywords:
            if not kw:
                continue

            normalized_kw = kw.lower().strip()
            variants = MULTILINGUAL_KEYWORD_MAP.get(normalized_kw, [normalized_kw])

            # Match if any variant appears in the text
            for variant in variants:
                if variant and variant in text:
                    found += 1
                    break

        return found / len(keywords)

    def _check_expected_evidence(self, expected: Optional[str], chunks: List[Dict[str, Any]]) -> bool:
        if not expected:
            return True
        lower_expected = expected.lower().strip()
        text = "\n\n".join([c.get("text", "") for c in chunks]).lower()
        return bool(lower_expected and lower_expected in text)

    def _combine_confidence(self, embedding_score: float, keyword_score: float, llm_confidence: float) -> float:
        return (0.4 * embedding_score) + (0.3 * keyword_score) + (0.3 * llm_confidence)

    def generate_recommendation(
        self,
        missing: List[str],
        risks: List[str],
    ) -> str:
        if missing:
            return "Add missing required sections: " + ", ".join(missing)
        if risks:
            return "Mitigate the identified risks."
        return "Control is properly implemented."
    def _get_cache_key(self, rule_id: str, evidence_chunks: List[Dict[str, Any]]) -> str:
        """Generate a cache key for a rule evaluation."""
        chunk_meta = "|".join(
            f"{c.get('id')}:{c.get('score')}" for c in evidence_chunks[:10]
        )
        digest = hashlib.sha256(f"{rule_id}:{chunk_meta}".encode("utf-8", errors="ignore")).hexdigest()
        return f"compliance_eval:{rule_id}:{digest}"

    def rules_from_standard(self, standard: Any) -> List[ComplianceRule]:
        """Convert a Standard object into a list of ComplianceRule instances."""
        rules: List[ComplianceRule] = []

        for control in getattr(standard, "controls", []).all():
            keywords = []
            if getattr(control, "keywords", None):
                keywords = [k.strip() for k in control.keywords.split(",") if k.strip()]

            rules.append(
                ComplianceRule(
                    id=str(getattr(control, "identifier", None) or control.pk),
                    standard=str(getattr(standard, "name", "")),
                    description=getattr(control, "description", ""),
                    severity=getattr(control, "severity", "major"),
                    expected_evidence=getattr(control, "example_evidence", ""),
                    keywords=keywords,
                )
            )

        return rules
